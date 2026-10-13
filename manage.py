"""Initialize the database and add clearly labelled fictional demo resources."""
import argparse
from pathlib import Path
from app import create_app, HASHER, now
from database import initialize, TYPES

SAMPLES = [
 ('云山的第一束光（自编神话示例）', '神话故事', '浙江省', ['创世', '神灵'],
  '古老的神话说，云山最初没有光。守山的神灵将一粒火种交给村民，村民共同守护火种，照亮了山谷。这是用于课程演示的自编文本。'),
 ('守桥的将军（自编人物示例）', '人物传说', '河北省', ['英雄', '守护'],
  '传说一位将军在洪水来临时组织乡亲修筑石桥。他把木料让给村民，最后才离开河岸，人们记住了他的名字。这是用于课程演示的自编文本。'),
 ('灯下的约定（自编爱情示例）', '爱情传说', '江苏省', ['爱情', '约定'],
  '一对相爱的恋人在河岸约定，每逢春天点亮一盏灯。多年后，两人仍一起制作灯笼，把祝愿送给来往的行人。这是用于课程演示的自编文本。'),
 ('月牙湖的名字（自编风物示例）', '风物传说', '云南省', ['湖泊', '地名'],
  '村旁的湖泊弯如月牙。老人讲述，祖先曾在湖岸植树，让清水留在村中，因此大家将湖泊称为月牙湖。这是用于课程演示的自编文本。'),
 ('邻里的竹篮（自编生活示例）', '生活故事', '四川省', ['邻里', '互助'],
  '村民阿禾丢了竹篮，邻居帮他一起寻找。第二天，他编了一只新篮送给邻居，两家此后常常互相帮忙。这是用于课程演示的自编文本。'),
 ('两只小鹿（自编寓言示例）', '寓言故事', '湖北省', ['谦让', '合作'],
  '两只小鹿在独木桥上相遇，谁也不肯退让。后来一只小鹿退回岸边，让另一只先过，两只小鹿都顺利过桥。这是用于课程演示的自编文本。'),
]


def seed(db):
    timestamp = now()
    for username, role in [('admin', 'admin'), ('reader', 'user')]:
        if not db.users.find_one({'username': username}):
            db.users.insert_one({'username': username,
                'password_hash': HASHER.hash('StoryDemo2026!'), 'role': role, 'created_at': timestamp})
    for i, (title, category, region, keywords, body) in enumerate(SAMPLES):
        url = f'https://example.org/course-demo/{i + 1}'
        if not db.stories.find_one({'title': title, 'source.url': url}):
            db.stories.insert_one({'title': title, 'content_kind': '故事正文',
                'story_type': category, 'original_content': body, 'summary': body.split('这是')[0],
                'regions': [region], 'ethnic_groups': [], 'main_characters': [],
                'theme_keywords': keywords, 'images': [], 'cultural_meaning': '用于演示资源管理流程。',
                'source': {'site_name': '课程自编演示资料（非实际采集）', 'url': url,
                           'collected_at': timestamp},
                'status': 'published', 'created_at': timestamp, 'updated_at': timestamp})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['init', 'seed'])
    args = parser.parse_args()
    app = create_app()
    db = app.extensions['mongo_db']
    initialize(db)
    if args.command == 'seed':
        seed(db)
        print('演示账号：admin / reader；演示密码：StoryDemo2026!')
    print('数据库就绪；资源数量：', db.stories.count_documents({}))
