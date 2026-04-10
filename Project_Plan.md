# 📋 个人资讯收集与整理 Agent - 核心执行规范 (Vibe Coding 版)

<!-- > **📌 使用说明**：将此文件保存至项目根目录为 `AGENT_EXECUTION_PLAN.md`。所有后续开发会话需将此文件作为系统上下文输入，AI 将严格按本规范分步执行，禁止跳步或修改核心约束。 -->

---

## 🎯 一、项目定位与核心目标
构建一个基于 **Python** 的自动化资讯处理 Agent，实现：
1. **双模式采集**：每日定时全自动检索 + 自然语言按需定向检索
2. **精准去重**：基于 `内容 + 发布时间` 严格比对，零重复处理
3. **结构化输出**：生成带引用标签的 Markdown 文档，按分类与时间戳归档
4. **交叉推理**：支持多选分类/文档进行 LLM 关系推理，输出至专属目录
5. **可视化图谱**：自动构建并渲染资讯实体关系网络
6. **源可配置**：权威网站列表支持 YAML 动态管理，支持 AI 推荐增补

---

## 🛠️ 二、技术栈约束 (Python Only)
| 模块 | 推荐库 | 约束说明 |
|:---|:---|:---|
| 调度引擎 | `APScheduler` | 仅使用 `cron`/`interval`，禁止阻塞主线程 |
| 采集解析 | `feedparser`, `requests`, `BeautifulSoup4` | 优先 RSS， fallback 网页解析 |
| 存储索引 | `sqlite3` (内置), `pathlib` | 元数据与文档路径分离管理 |
| LLM 处理 | `openai` 或 `langchain` | 支持 `gpt-4o-mini` / `Qwen` 等，需配置降级策略 |
| 关系图谱 | `networkx` + `pyvis` | 纯 Python 实现，导出 HTML 供前端嵌入 |
| 交互界面 | `Streamlit` | 单文件 `app.py`，禁止复杂前端框架 |
| 配置管理 | `PyYAML` + `dataclasses`/`pydantic` | 零硬编码，全量配置外置 |

---

## 📁 三、标准目录结构
```text
iKnow/
├── config/
│   ├── sources.yaml          # 资讯源定义（分类/URL/类型/启用状态）
│   └── prompts/              # LLM 提示词模板
├── data/
│   ├── documents/
│   │   ├── 国际形势/
│   │   ├── 国内政策/
│   │   │   ├── 国家/
│   │   │   ├── 广东省/
│   │   │   ├── 珠海市/
│   │   │   └── 澳门横琴/
│   │   ├── 大模型资讯/
│   │   ├── 开源社区/
│   │   ├── 众筹平台/
│   │   ├── 智能硬件与机器人资讯/
│   │   └── 交叉关系总结/      # 交叉推理输出专属目录
│   ├── graphs/               # 关系图谱 HTML/JSON 缓存
│   └── metadata.db           # SQLite 元数据索引
├── src/
│   ├── config_loader.py      # YAML 加载与校验
│   ├── collector.py          # 采集路由与解析
│   ├── deduplicator.py       # 去重核心逻辑
│   ├── processor.py          # LLM 摘要与引用生成
│   ├── cross_reasoner.py     # 交叉推理引擎
│   ├── graph_builder.py      # 图谱构建与渲染
│   └── db_manager.py         # SQLite 读写封装
├── ui/
│   └── dashboard.py          # Streamlit 控制台
├── AGENT_EXECUTION_PLAN.md   # 本文件
└── requirements.txt
```

---

## ⚠️ 四、核心规则 (CRITICAL - 严格执行)

### 1. 去重判定逻辑（最高优先级）
```python
# 伪代码规范
new_hash = normalize_md5(raw_content)
new_time = parse_publish_time(publish_str)

if exists_in_db(content_hash=new_hash, publish_time=new_time):
    log("DUPLICATE_SKIPPED")
    return  # 不进入任何处理流程
else:
    process_new_article()
```
- **内容清洗**：去除首尾空白、换行符、HTML 标签、连续空格后计算 MD5。
- **时间匹配**：精确到 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM`，格式统一为 ISO 8601。
- **行为**：命中重复直接跳过，不消耗 LLM Token，不生成文件。

### 2. 文档命名与存储规范
| 触发场景 | 命名格式 | 存储路径 |
|:---|:---|:---|
| 定时自动采集 | `{资讯核心主题}_{YYYYMMDD_HHMMSS}.md` | `data/documents/{分类}/` |
| 自然语言按需 | `{用户指定内容名}_{YYYYMMDD_HHMMSS}.md` | `data/documents/{分类}/` |
| 交叉关系推理 | `{交叉资讯内容}_{YYYYMMDD_HHMMSS}.md` | `data/documents/交叉关系总结/` |
- **文件名安全**：移除 `/ \ : * ? " < > |` 等非法字符，空格替换为 `_`。
- **时间戳**：使用系统当前执行时间，格式 `YYYYMMDD_HHMMSS`。

### 3. 引用标签规范
```markdown
## 摘要正文...
关键政策指出...[^1]。技术路线已明确...[^2]。

[^1]: [来源标题](原始URL) | 发布时间: YYYY-MM-DD
[^2]: [来源标题](原始URL) | 发布时间: YYYY-MM-DD
```
- 每个段落/关键数据后必须标注引用。
- 文末必须生成完整脚注列表，URL 必须可点击。

### 4. 分类体系（固定）
`国际形势`, `国内政策/国家`, `国内政策/广东省`, `国内政策/珠海市`, `国内政策/澳门横琴`, `大模型资讯`, `开源社区`, `众筹平台`, `智能硬件与机器人资讯`

---

## 📦 五、数据模型定义 (Pydantic)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class Category(str, Enum):
    INTERNATIONAL = "国际形势"
    POLICY_NATIONAL = "国内政策/国家"
    POLICY_GD = "国内政策/广东省"
    POLICY_ZH = "国内政策/珠海市"
    POLICY_HQ = "国内政策/澳门横琴"
    LLM = "大模型资讯"
    OPENSOURCE = "开源社区"
    CROWDFUNDING = "众筹平台"
    HARDWARE = "智能硬件与机器人资讯"

class RawArticle(BaseModel):
    title: str
    content: str
    publish_time: datetime
    source_url: str
    source_name: str
    category: Category

class ProcessedDoc(BaseModel):
    filename: str
    category: Category
    markdown_content: str  # 含 [^n] 引用
    references: List[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    is_cross_summary: bool = False
```

**SQLite 核心表结构 (`metadata.db`)**
```sql
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,
    publish_time TEXT NOT NULL,
    category TEXT NOT NULL,
    filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_hash_time ON articles(content_hash, publish_time);
```

---

## 🚀 六、分阶段执行计划 (Vibe Coding)

| 阶段 | 任务目标 | 交付物 | AI 执行指令 (Prompt) |
|:---|:---|:---|:---|
| **P1** | 配置管理 + 目录初始化 + DB 建表 | `sources.yaml`, `db_manager.py`, 目录树生成脚本 | `读取本文件，初始化项目目录结构，创建 sources.yaml 模板，实现 db_manager.py 包含 articles 表创建与 content_hash+publish_time 唯一性校验接口。输出完整代码。` |
| **P2** | 采集引擎 + 严格去重逻辑 | `collector.py`, `deduplicator.py` | `实现 RSS 与基础网页解析器。对接 P1 的 DB，实现 content_hash + publish_time 精确比对去重。重复项记录日志并跳过，新资讯返回 RawArticle 列表。提供单元测试。` |
| **P3** | LLM 处理 + Markdown 生成 + 引用注入 | `processor.py`, `prompts/summarize.txt` | `实现 Processor 模块：输入 RawArticle，调用 LLM 生成结构化摘要，严格注入 [^n] 引用标记。按规范命名并保存 Markdown 至 data/documents/{分类}/。更新 DB 记录。` |
| **P4** | 调度器 + 自然语言按需检索 | `scheduler.py`, `intent_parser.py` | `集成 APScheduler 实现每日定时任务(默认 09:00)。实现 NL 意图解析，支持指定分类/关键词检索。按需文档命名 `{query}_{timestamp}.md`。双模式统一走 P2->P3 流水线。` |
| **P5** | 交叉推理 + 关系图谱 + Streamlit UI | `cross_reasoner.py`, `graph_builder.py`, `ui/dashboard.py` | `实现多文档交叉推理模块，输出至 交叉关系总结/。基于 NetworkX+Pyvis 生成关系图谱 HTML。构建 Streamlit 仪表盘：源管理、文档浏览、图谱查看、NL 输入、手动触发按钮。` |

> 📌 **Vibe Coding 原则**：每完成一个 Phase，必须运行 `pytest` 验证核心逻辑，确认无阻断性 Bug 后再提交 `Next Phase` 指令。禁止一次性生成全量代码。

---

## 🤖 七、AI 执行协议 (系统提示词模板)

每次开启新会话时，请按以下格式加载上下文：
```
请严格遵循项目根目录下的 AGENT_EXECUTION_PLAN.md 执行开发。
当前阶段：[Phase X]
输入：[你的自然语言指令]
约束：
1. 仅编写 Python 3.10+ 代码，强制类型提示
2. 绝对遵守“内容+时间”双等去重规则
3. 文档命名、引用格式、目录路径一字不差
4. 分模块输出，附带必要注释与测试用例
5. 若需求模糊，主动询问而非假设
开始执行 Phase [X]...
```

---

## ✅ 八、最终验收清单

- [ ] `content_hash + publish_time` 精确匹配去重 100% 生效，无重复文档生成
- [ ] 所有 Markdown 文档含标准 `[^n]` 脚注，点击可跳转原始 URL
- [ ] 命名规范严格符合 `{内容/主题}_{YYYYMMDD_HHMMSS}.md`
- [ ] `交叉关系总结/` 目录独立存储推理文档与图谱文件
- [ ] `sources.yaml` 支持增删改，分类体系完整无遗漏
- [ ] Streamlit 界面覆盖：定时任务开关、NL 输入框、分类筛选、图谱交互、文档预览
- [ ] 代码模块化，无全局硬编码，配置/提示词/业务逻辑彻底解耦
- [ ] 完整 `requirements.txt` 与 `README.md`（含启动指令）

---
<!-- 🔒 **版本**: `v1.0` | 📅 **更新日期**: `2026-04-10` | 🛡️ **约束等级**: `STRICT` -->
<!-- > 将本文件置于项目根目录后，AI 将自动读取并按 Phase 顺序稳定执行。如需调整规则，请修改本文件后重启会话。 -->