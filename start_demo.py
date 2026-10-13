"""Start or reuse the local demo MongoDB, then start Flask."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
venv_python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
if venv_python.exists() and Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
    os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve())])

from pymongo import MongoClient
from app import create_app
from database import initialize
from manage import seed

NAME = 'folk-stories-mongo'


def docker(*args, check=True):
    result = subprocess.run(['docker', *args], text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Docker命令失败。')
    return result


def prepare():
    if not os.environ.get('MONGO_URI'):
        if not shutil.which('docker'):
            raise RuntimeError('请先安装并启动Docker Desktop，或设置已有MongoDB副本集的MONGO_URI。')
        docker('info', '--format', '{{.ServerVersion}}')
        existing = docker('inspect', NAME, check=False)
        if existing.returncode:
            docker('run', '-d', '--name', NAME, '-p', '127.0.0.1:27017:27017',
                   '-v', 'folk_stories_mongo_data:/data/db', 'mongo:7.0',
                   '--replSet', 'rs0', '--bind_ip_all')
        elif not json.loads(existing.stdout)[0]['State']['Running']:
            docker('start', NAME)
        mongo = MongoClient('mongodb://127.0.0.1:27017/?directConnection=true',
                            serverSelectionTimeoutMS=2000)
        ready = False
        for _ in range(25):
            try:
                mongo.admin.command('ping')
                ready = True
                break
            except Exception:
                time.sleep(1)
        if not ready:
            raise RuntimeError('MongoDB未就绪，请检查Docker容器日志。')
        try:
            mongo.admin.command('replSetGetStatus')
        except Exception as error:
            if getattr(error, 'code', None) != 94:
                raise
            mongo.admin.command('replSetInitiate', {
                '_id': 'rs0', 'members': [{'_id': 0, 'host': 'localhost:27017'}]})
        for _ in range(25):
            if mongo.admin.command('hello').get('isWritablePrimary'):
                break
            time.sleep(1)
        else:
            raise RuntimeError('副本集未选出可写主节点。')
        mongo.close()
    app = create_app()
    db = app.extensions['mongo_db']
    initialize(db)
    seed(db)
    print('数据库已就绪，演示资源不会重复新增。', flush=True)
    print('打开浏览器访问 http://127.0.0.1:5000', flush=True)
    print('账号：admin（管理员）、reader（普通用户）；密码均为 StoryDemo2026!', flush=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)


if __name__ == '__main__':
    try:
        prepare()
    except Exception as error:
        print('启动失败：', error, file=sys.stderr)
        sys.exit(1)
