# iKnow - 个人资讯收集与整理 Agent

一个基于 Python 的自动化资讯处理系统，实现权威源多分类采集、精准去重、LLM 结构化整理、关系图谱可视化、交叉推理总结。支持 **每日定时全自动运行** 与 **自然语言按需检索** 双模式。

## 🚀 功能特性

### 1. 双模式采集
- **每日定时全自动检索**：每天 09:00 自动从配置的权威网站采集最新资讯
- **自然语言按需定向检索**：通过自然语言查询特定主题的资讯

### 2. 精准去重
- 基于 `内容 + 发布时间` 严格比对，零重复处理
- 使用 MD5 哈希和时间戳双重验证

### 3. 结构化输出
- 生成带引用标签的 Markdown 文档
- 按分类与时间戳归档

### 4. 交叉推理
- 支持多选分类/文档进行 LLM 关系推理
- 输出至专属的交叉关系总结目录

### 5. 可视化图谱
- 自动构建并渲染资讯实体关系网络
- 支持 HTML 交互式查看

### 6. 源可配置
- 权威网站列表支持 YAML 动态管理
- 支持 AI 推荐增补

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **调度**: APScheduler (cron/interval)
- **采集**: feedparser (RSS), requests + BeautifulSoup4 (网页)
- **存储**: SQLite (元数据索引), Markdown (文档), JSON (图谱缓存)
- **AI/LLM**: OpenAI SDK / LangChain (适配 gpt-4o-mini / 本地 Qwen)
- **可视化**: NetworkX (图计算) + Pyvis (Streamlit 交互渲染)
- **UI**: Streamlit (单页控制台)
- **配置**: PyYAML + 环境变量隔离

## 📁 目录结构

```
iKnow/
├── config/                     # 配置根目录
│   ├── sources.yaml            # 资讯源定义（分类/URL/类型/开关）
│   └── prompts/                # LLM 提示词模板库
├── src/                        # 核心源码目录
│   ├── config/                 # 配置加载与热更新
│   ├── collectors/             # RSS/网页采集路由
│   ├── processors/             # 去重/摘要/图谱/交叉推理
│   ├── storage/                # SQLite元数据/Markdown管理/图谱序列化
│   ├── scheduler/              # APScheduler 定时与按需任务
│   └── utils/                  # 时间戳/日志/哈希工具
├── data/                       # 数据存储目录
│   ├── documents/              # 分类存储整理文档
│   │   ├── 国际形势/
│   │   ├── 国内政策/国家/广东/珠海/横琴/
│   │   ├── 大模型资讯/
│   │   ├── 开源社区/
│   │   ├── 众筹平台/
│   │   ├── 智能硬件与机器人/
│   │   └── 交叉关系总结/       # 交叉推理输出专用
│   └── graphs/                 # 关系图谱 HTML/JSON 缓存
├── ui/                         # 前端界面
│   └── dashboard.py             # Streamlit 主界面
├── tests/                      # 单元测试
├── requirements.txt             # 项目依赖
└── README.md                   # 项目说明文档
```

## 📋 分类体系

固定分类体系：
- `国际形势`
- `国内政策/国家`
- `国内政策/广东省`
- `国内政策/珠海市`
- `国内政策/澳门横琴`
- `大模型资讯`
- `开源社区`
- `众筹平台`
- `智能硬件与机器人资讯`

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Streamlit UI

```bash
streamlit run ui/dashboard.py
```

### 3. 配置资讯源

编辑 `config/sources.yaml` 文件，添加您需要监控的 RSS 或网页链接。

### 4. 使用系统

- 通过 Web 界面进行各种操作
- 设置定时任务
- 执行自然语言查询
- 查看生成的文档和关系图谱

## 📊 使用场景

### 定时自动采集
- 系统会在每天 09:00 自动从所有启用的资讯源采集最新信息
- 自动去重，避免重复处理
- 按照 `{资讯核心主题}_{YYYYMMDD_HHMMSS}.md` 格式命名并保存到对应分类目录

### 自然语言按需检索
- 通过自然语言输入框输入查询需求
- 系统自动解析意图并从相关分类的资讯源检索
- 按照 `{用户指定内容名}_{YYYYMMDD_HHMMSS}.md` 格式命名并保存

### 交叉关系推理
- 选择多个文档进行交叉分析
- 系统生成关系推理报告
- 按照 `{交叉资讯内容}_{YYYYMMDD_HHMMSS}.md` 格式命名并保存到交叉关系总结目录

## 🏗️ 架构设计

系统采用模块化设计，各组件职责分明：

- **Config**: 负责配置加载和验证
- **Collectors**: 负责从 RSS 和网页采集原始数据
- **Processors**: 负责去重、LLM 处理、交叉推理、图谱构建
- **Storage**: 负责数据库管理和文档存储
- **Scheduler**: 负责定时任务和按需检索调度
- **UI**: 提供用户交互界面

## 🧪 测试

项目包含完整的单元测试，覆盖所有主要功能模块：

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定阶段的测试
python -m pytest tests/test_phase1.py
python -m pytest tests/test_phase2.py
# ... etc
```

## 📈 引用格式

所有生成的文档都包含标准的引用格式：

```markdown
关键政策指出...[^1]。技术路线已明确...[^2]。

[^1]: [来源标题](原始URL) | 发布时间: YYYY-MM-DD
[^2]: [来源标题](原始URL) | 发布时间: YYYY-MM-DD
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## ©️ 许可证

[MIT License](LICENSE)