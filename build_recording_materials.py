from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "录屏准备材料"
OUT.mkdir(exist_ok=True)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(10.5)


doc = Document()
section = doc.sections[0]
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(2.0)
section.left_margin = Cm(2.2)
section.right_margin = Cm(2.2)

styles = doc.styles
styles["Normal"].font.name = "宋体"
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
styles["Normal"].font.size = Pt(11)
styles["Normal"].paragraph_format.line_spacing = 1.35
for style_name, font_name, size in [("Title", "黑体", 22), ("Heading 1", "黑体", 16), ("Heading 2", "黑体", 13)]:
    style = styles[style_name]
    style.font.name = font_name
    style._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    style.font.size = Pt(size)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("中华民族民间故事资源数据管理与智能处理系统")
r.bold = True
r.font.name = "黑体"
r._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
r.font.size = Pt(22)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("汇报录屏准备材料")
r.bold = True
r.font.name = "黑体"
r._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
r.font.size = Pt(18)

doc.add_paragraph("建议时长：8—10分钟　录制方式：腾讯会议录制　摄像头：可关闭")
doc.add_paragraph("说明：系统内现有6条记录为功能演示数据。正式汇报时应明确说明，避免把演示数据表述为已经完成的真实采集成果。")

doc.add_heading("一、录制信息填写", level=1)
table = doc.add_table(rows=7, cols=3)
table.style = "Table Grid"
headers = ["顺序", "姓名", "学号"]
for i, h in enumerate(headers):
    set_cell_text(table.rows[0].cells[i], h, True)
    shade(table.rows[0].cells[i], "D9EAD3")
names = ["穰筱（录制者）", "李翔", "李尚", "杨昊", "王少翎", "郭浩宇"]
for idx, name in enumerate(names, 1):
    set_cell_text(table.rows[idx].cells[0], str(idx))
    set_cell_text(table.rows[idx].cells[1], name)
    set_cell_text(table.rows[idx].cells[2], "________________")
doc.add_paragraph("文件名模板：小组名_学号穰筱_学号李翔_学号李尚_学号杨昊_学号王少翎_学号郭浩宇.mp4")

doc.add_heading("二、录制前准备", level=1)
items = [
    "启动Docker Desktop，确认Docker Engine已经运行。",
    "双击项目目录中的 run_windows.bat，保持命令窗口开启。",
    "浏览器访问 http://127.0.0.1:5000。",
    "演示管理员账号：admin；密码：StoryDemo2026!。",
    "提前打开首页、后台管理、批量导入、智能处理审核和收藏页面。",
    "准备 sample_import.csv，录制批量导入时使用。",
    "关闭微信等通知，腾讯会议选择录制屏幕和麦克风。",
    "录制后检查声音、画面、时长、MP4格式和文件名。",
]
for item in items:
    doc.add_paragraph(item, style="List Number")

doc.add_heading("三、录屏分镜表", level=1)
shots = [
    ("0:00—0:40", "系统首页", "介绍系统名称、技术架构和主要用途"),
    ("0:40—2:20", "首页、详情页", "说明选题原因、数据类型和字段设计"),
    ("2:20—4:10", "CSV示例、导入页", "讲清检索、筛选、清洗、统一字段和检查过程"),
    ("4:10—6:30", "登录、后台管理、检索", "演示新增、修改、筛选、发布和来源核查"),
    ("6:30—7:30", "智能处理审核页", "说明摘要、分类、主题词及人工审核流程"),
    ("7:30—8:20", "收藏页、首页", "说明问题、解决方法和后续改进"),
]
table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"
for i, h in enumerate(["时间", "画面", "讲解重点"]):
    set_cell_text(table.rows[0].cells[i], h, True)
    shade(table.rows[0].cells[i], "D9EAD3")
for row in shots:
    cells = table.add_row().cells
    for i, value in enumerate(row):
        set_cell_text(cells[i], value)

doc.add_page_break()
doc.add_heading("四、完整讲稿", level=1)

script_sections = [
    ("1. 开场与系统介绍（展示首页）", "大家好，我们小组汇报的系统是“中华民族民间故事资源数据管理与智能处理系统”。系统采用Flask开发网页功能，使用MongoDB存储数据，主要实现民间故事的采集、整理、导入、查询、维护和辅助处理。本次汇报重点介绍资源数据的采集思路、整理过程和系统功能。"),
    ("2. 选题与数据结构（展示故事列表和详情页）", "我们选择民间故事作为资源数据，主要有三个原因。第一，民间故事能够反映不同地区和民族的历史记忆、生活经验与价值观念，具有文化价值。第二，民间故事以文本为主，适合开展分类、摘要和主题词提取。第三，不同故事的地区、民族、人物和图片数量可能不同，MongoDB的文档结构便于保存这类存在差异的数据。\n\n每条故事主要包含标题、资源类型、故事类别、故事正文、摘要、地区、民族、主要人物、主题词、文化意义、来源网站、原始网址、采集时间和图片信息。故事类别包括神话故事、人物传说、爱情传说、风物传说、生活故事和寓言故事；暂时无法判断的资源可以标记为“待分类”，之后再审核。"),
    ("3. 采集思路和过程（展示来源字段和CSV示例）", "我们优先从来源明确、内容完整的公开文化资源平台查找资料，例如中国非物质文化遗产网。采集过程分为五步。\n\n第一步是确定检索词，使用“民间故事”“民间传说”“神话故事”以及具体故事名称进行检索。第二步是筛选资源，重点检查资料是否有明确标题、完整正文、来源网站和原始网址；来源不明、内容过短或重复转载的资料不直接采用。第三步是提取内容，记录标题、正文、类别、地区、民族、人物和来源信息，并清除网页中的导航、广告和无关文字。第四步是统一字段，例如统一地区名称，主题词使用简短词语，来源字段保留原始页面地址。第五步是检查数据，检查必填字段、网址格式、正文完整性和重复来源。\n\n目前系统中的6条记录用于验证字段和演示功能，不能代替正式采集成果。下一步计划整理100到200条来源明确的真实民间故事资源。"),
    ("4. 登录与资源管理（登录后台，展示新增和编辑）", "系统设置管理员和普通用户两类角色。管理员可以录入、修改、删除、审核和发布资源；普通用户可以浏览、检索和收藏已经发布的故事。\n\n管理员新增故事时，需要填写标题、正文、类别、地区、民族、主题词和来源等信息。系统对关键字段进行校验，例如标题和正文不能为空，来源网址需要符合网址格式；已经发布的资源必须具有摘要、正式类别和完整来源。删除采用状态标记，发现误操作后可以恢复。"),
    ("5. 检索与批量导入（展示首页筛选和导入页）", "用户可以按照关键词、故事类别、地区和民族筛选资源。进入详情页后，可以查看正文、摘要、主题词、文化意义和来源信息。\n\n为了提高录入效率，系统支持CSV和Excel批量导入。导入前需要按照统一模板整理数据。系统读取文件后检查字段名称、必填内容和来源网址，发现错误时返回提示，修改后可以重新导入。批量导入提高了效率，但故事类别、文化意义和正文完整性仍需人工检查。"),
    ("6. 智能处理与审核（展示审核页）", "系统设计了类别、摘要和主题词辅助处理功能。处理流程是读取故事标题和正文，生成建议类别、摘要和主题词，再进入人工审核页面。管理员对照原文检查结果，可以接受或拒绝，通过审核的结果才写入正式字段。\n\n当前系统使用本地规则完成辅助处理。小组还调研了TextRank算法，它可以根据句子或词语之间的联系计算重要程度，不需要大量标注数据，适合用于本项目的摘要和关键词实验。这里介绍的是下一步改进计划，当前演示结果不表述为TextRank运行结果。"),
    ("7. 问题、解决方法与计划（展示收藏页后返回首页）", "项目实施中主要遇到三个问题。第一，资料字段写法不统一，我们通过建立字段表、统一类别和填写规范解决。第二，网页内容包含导航和广告等杂质，我们在导入前进行文本清洗，并保留原始网址供复核。第三，运行环境配置较复杂，我们统一使用Python 3.12，并通过Docker运行MongoDB，减少不同计算机之间的环境差异。\n\n后续将补充真实数据，完善重复检测和缺失字段检查；同时运行TextRank项目，对不同长度和类别的故事进行实验，从主要人物、核心事件和故事结局三个方面评价摘要质量。\n\n以上是我们小组的资源数据管理系统汇报，谢谢老师观看。"),
]

for heading, body in script_sections:
    doc.add_heading(heading, level=2)
    for para in body.split("\n\n"):
        doc.add_paragraph(para)

doc.add_heading("五、录制后检查", level=1)
checks = [
    "视频时长在5—20分钟范围内，建议控制在8—10分钟。",
    "开头说明系统名称，正文讲清资料来源、筛选标准、整理和导入过程。",
    "演示数据与正式采集数据表述清楚，不夸大实际进度。",
    "画面能够看清系统页面，声音连续且无明显杂音。",
    "视频格式为MP4，文件名包含小组名及全部成员学号、姓名，录制者排第一。",
    "在课程规定的第10周周日20:00前完成提交。",
]
for item in checks:
    doc.add_paragraph("□ " + item)

docx_path = OUT / "民间故事资源库_录屏讲稿与准备清单.docx"
doc.save(docx_path)

readme = OUT / "使用说明.txt"
readme.write_text(
    "1. 先在Word讲稿第一页补齐6名成员学号和小组名。\n"
    "2. 录制前启动Docker Desktop，再双击项目中的run_windows.bat。\n"
    "3. 浏览器打开http://127.0.0.1:5000。\n"
    "4. 管理员账号：admin，密码：StoryDemo2026!。\n"
    "5. 使用腾讯会议录制，完成后按课程要求命名MP4文件。\n",
    encoding="utf-8",
)

zip_path = ROOT / "民间故事资源库_录屏准备材料包.zip"
with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
    zf.write(docx_path, f"录屏准备材料/{docx_path.name}")
    zf.write(readme, f"录屏准备材料/{readme.name}")
    zf.write(ROOT / "sample_import.csv", "录屏准备材料/sample_import.csv")
    for name in ["home.png", "manage.png", "import.png", "review.png", "favorites.png"]:
        zf.write(ROOT / "demo" / name, f"录屏准备材料/系统截图/{name}")

print(docx_path)
print(zip_path)
