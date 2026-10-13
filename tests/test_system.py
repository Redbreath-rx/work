"""Integration tests against a real, disposable MongoDB replica-set database."""
import csv
import io
import re
import uuid
import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, WriteError
from app import create_app, story_from_form, now
from database import initialize
from manage import seed


@pytest.fixture
def app(tmp_path):
    name = 'folk_test_' + uuid.uuid4().hex
    app = create_app({'TESTING': True, 'WTF_CSRF_ENABLED': False, 'MONGO_DB': name,
                      'UPLOAD_FOLDER': str(tmp_path / 'uploads')})
    db = app.extensions['mongo_db']
    initialize(db)
    seed(db)
    yield app
    app.extensions['mongo_client'].drop_database(name)
    app.extensions['mongo_client'].close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return app.extensions['mongo_db']


def login(client, username='admin'):
    return client.post('/login', data={'username': username, 'password': 'StoryDemo2026!'})


def formdata(**changes):
    data = {'title': '测试资源', 'content_kind': '故事正文', 'story_type': '待分类',
            'original_content': '两只小鹿通过谦让顺利过桥。', 'summary': '',
            'site_name': '测试来源', 'source_url': 'https://example.org/test',
            'regions': '浙江省，浙江省', 'theme_keywords': ''}
    data.update(changes)
    return data


def generate(client, db, identifier):
    response = client.post(f'/manage/{identifier}/process', follow_redirects=True)
    assert response.status_code == 200
    return db.ai_results.find_one({'story_id': identifier})


def accept(client, result):
    return client.post(f'/manage/results/{result["_id"]}/review', data={
        'action': 'accept', 'story_type': result['output']['story_type'],
        'summary': result['output']['summary'],
        'theme_keywords': ','.join(result['output']['theme_keywords'])}, follow_redirects=True)


def test_home_search_and_literal_regex(client, db):
    assert client.get('/').status_code == 200
    body = client.get('/?type=寓言故事&region=湖北省&keyword=谦让').get_data(as_text=True)
    assert '两只小鹿（自编寓言示例）' in body
    assert '月牙湖的名字（自编风物示例）' not in body
    assert '共 0 条' in client.get('/?q=.*').get_data(as_text=True)
    assert client.get('/?page=bad').status_code == 200


def test_draft_hidden_and_publish_rules(client, db):
    login(client)
    identifier = db.stories.insert_one(story_from_form(formdata())).inserted_id
    assert client.get(f'/stories/{identifier}').status_code == 404
    r = client.post(f'/manage/{identifier}/status', data={'action': 'publish'}, follow_redirects=True)
    assert '发布前须补充摘要' in r.get_data(as_text=True)
    assert db.stories.find_one({'_id': identifier})['status'] == 'draft'


def test_admin_create_edit_delete_restore(client, db):
    login(client)
    r = client.post('/admin/stories/new/', data=formdata(), follow_redirects=True)
    assert r.status_code == 200
    story = db.stories.find_one({'title': '测试资源'})
    assert story and story['regions'] == ['浙江省']
    r = client.post('/admin/stories/edit/?id=' + str(story['_id']),
                    data=formdata(title='修改后的资源', story_type='寓言故事', summary='小鹿谦让过桥。'),
                    follow_redirects=True)
    assert r.status_code == 200
    client.post(f'/manage/{story["_id"]}/status', data={'action': 'publish'})
    assert client.get(f'/stories/{story["_id"]}').status_code == 200
    client.post(f'/manage/{story["_id"]}/status', data={'action': 'delete'})
    assert client.get(f'/stories/{story["_id"]}').status_code == 404
    client.post(f'/manage/{story["_id"]}/status', data={'action': 'restore'})
    assert db.stories.find_one({'_id': story['_id']})['status'] == 'draft'


def test_editing_text_unpublishes(client, db):
    login(client)
    story = db.stories.find_one({'story_type': '寓言故事'})
    data = formdata(title=story['title'], source_url=story['source']['url'],
        story_type='寓言故事', summary='已有摘要', original_content='修改后的故事原文。')
    client.post('/admin/stories/edit/?id=' + str(story['_id']), data=data)
    assert db.stories.find_one({'_id': story['_id']})['status'] == 'draft'


def test_authorization_and_registration(client, db):
    assert client.get('/manage').status_code == 302
    login(client, 'reader')
    assert client.get('/manage').status_code == 403
    assert client.get('/admin/stories/new/').status_code == 403
    story = db.stories.find_one()
    assert client.post(f'/manage/{story["_id"]}/status', data={'action': 'delete'}).status_code == 403
    client.post('/logout')
    client.post('/register', data={'username': 'newreader', 'password': 'StrongDemo123!', 'role': 'admin'})
    assert db.users.find_one({'username': 'newreader'})['role'] == 'user'


def test_favorites_unique_private_and_deleted_hidden(client, db, app):
    login(client, 'reader')
    story = db.stories.find_one()
    identifier = story['_id']
    client.post(f'/stories/{identifier}/favorite')
    reader = db.users.find_one({'username': 'reader'})
    assert db.favorites.count_documents({'user_id': reader['_id']}) == 1
    with pytest.raises(DuplicateKeyError):
        db.favorites.insert_one({'user_id': reader['_id'], 'story_id': identifier, 'created_at': now()})
    other = app.test_client()
    login(other)
    assert story['title'] not in other.get('/favorites').get_data(as_text=True)
    db.stories.update_one({'_id': identifier}, {'$set': {'status': 'deleted'}})
    assert story['title'] not in client.get('/favorites').get_data(as_text=True)
    assert db.favorites.count_documents({'user_id': reader['_id']}) == 1


def test_favorite_cancel(client, db):
    login(client, 'reader')
    identifier = db.stories.find_one()['_id']
    client.post(f'/stories/{identifier}/favorite')
    client.post(f'/stories/{identifier}/favorite')
    assert db.favorites.count_documents({}) == 0


def test_import_errors_dedup_and_csv(client, db):
    login(client)
    content = io.StringIO()
    writer = csv.DictWriter(content, fieldnames=['title', 'original_content', 'site_name', 'source_url'])
    writer.writeheader()
    good = {'title': '导入测试', 'original_content': '有效原文', 'site_name': '测试',
            'source_url': 'https://example.org/import'}
    writer.writerow(good); writer.writerow(good)
    writer.writerow({**good, 'title': '错误记录', 'site_name': ''})
    r = client.post('/manage/import', data={'file': (io.BytesIO(content.getvalue().encode()), 'test.csv')})
    text = r.get_data(as_text=True)
    assert '新增 1 条' in text and '重复 1 条' in text and '第4行' in text
    assert db.stories.find_one({'title': '导入测试'})['status'] == 'draft'


def test_excel_import(client, db):
    from openpyxl import Workbook
    login(client)
    book = Workbook(); sheet = book.active
    sheet.append(['title', 'original_content', 'site_name', 'source_url'])
    sheet.append(['Excel测试', '来自Excel的正文', '测试资料', 'https://example.org/excel'])
    buffer = io.BytesIO(); book.save(buffer); buffer.seek(0)
    r = client.post('/manage/import', data={'file': (buffer, 'data.xlsx')})
    assert '新增 1 条' in r.get_data(as_text=True)
    assert db.stories.find_one({'title': 'Excel测试'})


def test_content_cleaning():
    doc = story_from_form(formdata(original_content='<p>第一段</p><script>广告脚本</script><p>第二段</p>'))
    assert '第一段' in doc['original_content'] and '第二段' in doc['original_content']
    assert '广告脚本' not in doc['original_content'] and '<p>' not in doc['original_content']


def test_processing_accept_transaction_and_history(client, db):
    login(client)
    identifier = db.stories.insert_one(story_from_form(formdata())).inserted_id
    result = generate(client, db, identifier)
    assert result['model_name'] == 'local-rules-v1'
    r = accept(client, result)
    assert '审核已完成' in r.get_data(as_text=True)
    fresh = db.stories.find_one({'_id': identifier})
    reviewed = db.ai_results.find_one({'_id': result['_id']})
    assert reviewed['review_status'] == 'accepted' and 'reviewed_at' in reviewed
    assert fresh['summary'] == reviewed['output']['summary']
    assert fresh['status'] == 'draft'
    accept(client, result)
    assert db.ai_results.find_one({'_id': result['_id']})['review_status'] == 'accepted'


@pytest.mark.parametrize('field,value', [('title', '新名称'), ('content_kind', '项目介绍'),
                                        ('original_content', '已经改过的原文')])
def test_stale_processing_refused(client, db, field, value):
    login(client)
    identifier = db.stories.find_one()['_id']
    result = generate(client, db, identifier)
    db.stories.update_one({'_id': identifier}, {'$set': {field: value}})
    r = accept(client, result)
    assert '输入内容已变化' in r.get_data(as_text=True)
    assert db.ai_results.find_one({'_id': result['_id']})['review_status'] == 'pending'


def test_transaction_rollback(client, db, monkeypatch):
    from pymongo.synchronous.collection import Collection
    login(client)
    identifier = db.stories.find_one()['_id']
    result = generate(client, db, identifier)
    before = db.stories.find_one({'_id': identifier})
    original = Collection.update_one
    def fail_result_update(self, *args, **kwargs):
        if self.name == 'ai_results':
            raise ValueError('模拟审核状态写入失败')
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Collection, 'update_one', fail_result_update)
    r = accept(client, result)
    assert '模拟审核状态写入失败' in r.get_data(as_text=True)
    assert db.stories.find_one({'_id': identifier}) == before
    assert db.ai_results.find_one({'_id': result['_id']})['review_status'] == 'pending'


def test_reject_and_invalid_output(client, db):
    login(client)
    identifier = db.stories.find_one()['_id']
    result = generate(client, db, identifier)
    client.post(f'/manage/results/{result["_id"]}/review', data={'action': 'accept',
                'story_type': '不存在', 'summary': '错误分类', 'theme_keywords': '词'})
    assert db.ai_results.find_one({'_id': result['_id']})['review_status'] == 'pending'
    client.post(f'/manage/results/{result["_id"]}/review', data={'action': 'reject'})
    assert db.ai_results.find_one({'_id': result['_id']})['review_status'] == 'rejected'


@pytest.mark.parametrize('change', [{'regions': '错误类型'}, {'theme_keywords': [1]},
    {'story_type': '待分类'}, {'summary': ''}, {'summary': '字' * 201},
    {'images': [{'path': 'file.png', 'source_url': 'https://example.org/p.png'}]}])
def test_database_rejects_invalid_published(db, change):
    story = db.stories.find_one(); del story['_id']
    story['title'] += uuid.uuid4().hex
    story.update(change)
    with pytest.raises(WriteError):
        db.stories.insert_one(story)


def test_auxiliary_validators(db):
    with pytest.raises(WriteError):
        db.users.insert_one({'username': 'wrong', 'password_hash': 'hash', 'role': 'super', 'created_at': now()})
    with pytest.raises(WriteError):
        db.favorites.insert_one({'user_id': 'not-objectid', 'story_id': ObjectId(), 'created_at': now()})


def test_image_upload_validation_visibility(client, db):
    from PIL import Image
    login(client)
    identifier = db.stories.find_one()['_id']
    buffer = io.BytesIO(); Image.new('RGB', (20, 20), 'green').save(buffer, format='PNG'); buffer.seek(0)
    client.post(f'/manage/{identifier}/image', data={'image': (buffer, 'demo.png'),
        'source_url': 'https://example.org/image', 'caption': '测试图'})
    story = db.stories.find_one({'_id': identifier}); image = story['images'][0]
    assert story['status'] == 'draft'
    assert client.get('/images/' + image['path']).status_code == 200
    client.post('/logout')
    assert client.get('/images/' + image['path']).status_code == 404


def test_csrf_required(app):
    app.config['WTF_CSRF_ENABLED'] = True
    c = app.test_client()
    assert c.post('/login', data={'username': 'admin', 'password': 'StoryDemo2026!'}).status_code == 400
