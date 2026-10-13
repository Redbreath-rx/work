"""MongoDB validators and indexes matching the course report."""
TYPES = ['神话故事', '人物传说', '爱情传说', '风物传说', '生活故事', '寓言故事']
TEXT = {'bsonType': 'string', 'minLength': 1}
DATE = {'bsonType': 'date'}
OID = {'bsonType': 'objectId'}
STRINGS = {'bsonType': 'array', 'items': TEXT, 'uniqueItems': True}
OUTPUT = {
    'bsonType': 'object', 'required': ['story_type', 'summary', 'theme_keywords'],
    'properties': {
        'story_type': {'enum': TYPES},
        'summary': {'bsonType': 'string', 'minLength': 1, 'maxLength': 200},
        'theme_keywords': {**STRINGS, 'minItems': 1, 'maxItems': 5},
    },
}
SCHEMAS = {
    'stories': {
        'bsonType': 'object',
        'required': ['title', 'content_kind', 'story_type', 'original_content',
                     'source', 'status', 'created_at', 'updated_at'],
        'properties': {
            '_id': OID, 'title': TEXT,
            'content_kind': {'enum': ['故事正文', '项目介绍']},
            'story_type': {'enum': TYPES + ['待分类']}, 'original_content': TEXT,
            'summary': {'bsonType': 'string', 'maxLength': 200},
            'regions': STRINGS, 'ethnic_groups': STRINGS,
            'main_characters': STRINGS, 'theme_keywords': STRINGS,
            'cultural_meaning': {'bsonType': 'string'},
            'source': {
                'bsonType': 'object', 'required': ['site_name', 'url', 'collected_at'],
                'properties': {'site_name': TEXT, 'url': TEXT, 'collected_at': DATE},
            },
            'images': {'bsonType': 'array', 'items': {
                'bsonType': 'object', 'required': ['path', 'source_url', 'caption'],
                'properties': {'path': TEXT, 'source_url': TEXT,
                               'caption': {'bsonType': 'string'},
                               'author': {'bsonType': 'string'},
                               'license': {'bsonType': 'string'}},
            }},
            'status': {'enum': ['draft', 'published', 'deleted']},
            'created_at': DATE, 'updated_at': DATE,
        },
        'anyOf': [
            {'properties': {'status': {'enum': ['draft', 'deleted']}}},
            {'required': ['summary'], 'properties': {
                'status': {'enum': ['published']}, 'story_type': {'enum': TYPES},
                'summary': {'bsonType': 'string', 'minLength': 1, 'maxLength': 200},
            }},
        ],
    },
    'users': {
        'bsonType': 'object',
        'required': ['username', 'password_hash', 'role', 'created_at'],
        'properties': {'_id': OID, 'username': TEXT, 'password_hash': TEXT,
                       'role': {'enum': ['user', 'admin']}, 'created_at': DATE},
    },
    'favorites': {
        'bsonType': 'object', 'required': ['user_id', 'story_id', 'created_at'],
        'properties': {'_id': OID, 'user_id': OID, 'story_id': OID, 'created_at': DATE},
    },
    'ai_results': {
        'bsonType': 'object',
        'required': ['story_id', 'model_name', 'prompt_version', 'input_hash',
                     'output', 'review_status', 'generated_at'],
        'properties': {'_id': OID, 'story_id': OID, 'model_name': TEXT,
                       'prompt_version': TEXT,
                       'input_hash': {'bsonType': 'string', 'pattern': '^[0-9a-f]{64}$'},
                       'output': OUTPUT,
                       'review_status': {'enum': ['pending', 'accepted', 'rejected']},
                       'generated_at': DATE, 'reviewed_at': DATE},
        'anyOf': [
            {'properties': {'review_status': {'enum': ['pending']}}},
            {'required': ['reviewed_at'], 'properties': {
                'review_status': {'enum': ['accepted', 'rejected']}}},
        ],
    },
}


def initialize(db):
    existing = db.list_collection_names()
    for name, schema in SCHEMAS.items():
        options = {'validator': {'$jsonSchema': schema},
                   'validationLevel': 'strict', 'validationAction': 'error'}
        if name in existing:
            db.command('collMod', name, **options)
        else:
            db.create_collection(name, **options)
    db.stories.create_index([('source.url', 1), ('title', 1)], unique=True)
    db.stories.create_index([('status', 1), ('story_type', 1), ('regions', 1)])
    db.stories.create_index('theme_keywords')
    db.users.create_index('username', unique=True)
    db.favorites.create_index([('user_id', 1), ('story_id', 1)], unique=True)
    db.ai_results.create_index([('story_id', 1), ('generated_at', -1)])
