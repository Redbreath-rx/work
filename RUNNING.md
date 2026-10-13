# 民间故事资源库：运行说明

本项目按本组设计文档实现，采用 Flask + MongoDB + PyMongo，并使用 Flask-Admin 的 PyMongo 管理视图。Flask-Admin 采用 BSD-3-Clause 协议；项目参考其官方后台示例的组织方式，应用业务代码另行实现。

开源基础：https://github.com/pallets-eco/flask-admin/tree/master/examples/pymongo_simple

## 已实现

- 公开列表与详情只展示已发布故事；名称检索、类型/地域/关键词筛选、分页。
- 注册、登录、Argon2密码哈希、角色权限、个人收藏与取消收藏。
- Flask-Admin新增与编辑故事；草稿发布、撤回、软删除及恢复。
- CSV、Excel逐行导入、来源校验、数组去重、错误行报告及唯一索引去重。
- PNG/JPEG/WEBP图片上传、本地路径保存、按发布状态控制访问。
- 处理建议生成、输出校验、审核/拒绝、输入哈希检查及MongoDB事务采用。
- 四个集合的数据库验证器及设计文档中的业务索引。

预置的6条资源是**自编演示文本**，包含示例地域，不是爬取的真实资料；源网址为 example.org 的测试标识。真实资源请通过管理页面导入。

## Windows运行

1. 安装 Python 3.12（可与其他版本共存）、Docker Desktop，并启动Docker Desktop。Windows上的Docker需要Linux容器模式。
2. 下载源码压缩包并解压。
3. 双击 `run_windows.bat`。脚本固定选择Python 3.12，已有不兼容虚拟环境会先备份。脚本安装依赖，启动MongoDB单节点副本集并初始化演示数据。
4. 保持窗口运行，在本机浏览器打开 `http://127.0.0.1:5000`。

演示账号：`admin`（管理员）、`reader`（普通用户）。演示密码均为 `StoryDemo2026!`。这些账号仅用于本地课程演示。

## macOS / Linux运行

安装Python 3.10+及Docker，并启动Docker。然后在项目目录执行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python start_demo.py
```

已有MongoDB时，设置 `MONGO_URI` 和可选的 `MONGO_DB`；MongoDB必须为副本集，AI结果采用才支持多文档事务。启动脚本不会删除已有数据。Docker启动的数据库使用持久卷 `folk_stories_mongo_data`。

## 演示顺序

1. 首页按“寓言故事”“湖北省”“谦让”检索，查看自编小鹿故事。
2. 用reader登录，收藏故事，打开“我的收藏”，再取消收藏。
3. 用admin登录，打开“新增故事”，保存为草稿。
4. 打开“处理与审核”，生成本地规则建议，核对并采用，再发布。
5. 在“导入资料”上传 `sample_import.csv`；再次上传检查重复记录。
6. 修改故事原文后，尝试采用旧的待审核结果，应提示输入变化。
7. 软删除资源，检查公开页面不再显示；恢复后应为草稿。

## 智能处理模式

默认模式名为 `local-rules-v1`，页面明确标注为**本地规则演示**。它按词表建议分类、截取原文生成摘要并匹配关键词，**不是大语言模型调用**。

要连接真实模型，在启动前设置：

- `AI_BASE_URL`：支持OpenAI兼容接口的HTTPS基础地址，以 `/v1` 结尾。
- `AI_MODEL`：供应商实际支持的模型名称。
- `AI_API_KEY`：通过本机环境变量或云环境安全设置提供，不写入代码和Git。

服务调用 `AI_BASE_URL/chat/completions`，要求供应商支持JSON对象输出模式。云环境还需允许该API域名访问；本次未配置、未验证外部模型。默认本地规则模式的生成、审核和事务采用流程已验证。

## 测试

测试连接真实MongoDB副本集，每个测试建立随机命名的独立测试库，测试结束删除该测试库，不修改演示库。

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Windows将上面的Python路径改为 `.venv\Scripts\python.exe`。

本次云环境实测：25项集成测试通过，无失败、无跳过；真实浏览器走通启用CSRF的新增、生成建议、事务采用、发布、收藏、CSV导入与去重流程，并检查手机宽度布局。实际备份恢复验证了四个集合的记录数量、索引及验证器。截图及测试结果见 `demo` 目录。Windows启动脚本已提供，本次没有在Windows机器上实测。

`requirements-lock.txt` 保存本次云环境解析的完整依赖版本，包含测试与浏览器工具；需要复现验证环境时用它安装。

## 备份与恢复

先暂停所有应用写入，再备份数据库，并复制 `uploads` 图片目录；完成后恢复应用。

```sh
docker exec folk-stories-mongo mongodump --db folk_stories --archive=/tmp/folk-stories.archive --gzip
docker cp folk-stories-mongo:/tmp/folk-stories.archive ./folk-stories.archive
```

恢复到独立测试库时：

```sh
docker cp ./folk-stories.archive folk-stories-mongo:/tmp/folk-stories.archive
docker exec folk-stories-mongo mongorestore --archive=/tmp/folk-stories.archive --gzip --nsInclude='folk_stories.*' --nsFrom='folk_stories.*' --nsTo='folk_restore_test.*'
```

Windows命令行将命名空间参数中的单引号改成双引号。恢复后核对记录、索引、验证器，以及另行恢复的图片目录。
