# 🤖 项目上下文：个人资讯收集与整理 Agent

## 🎯 核心目标

构建一个基于 Python 的自动化资讯处理系统，实现权威源多分类采集、精准去重、LLM 结构化整理、关系图谱可视化、交叉推理总结。支持 **每日定时全自动运行** 与 **自然语言按需检索** 双模式。

## 🛠️ 技术栈规范（仅供参考，具体以实际情况进行优化）

- **语言**: Python 3.10+ (强制类型提示 `typing`)
- **调度**: `APScheduler` (cron/interval)
- **采集**: `feedparser` (RSS), `requests` + `BeautifulSoup`/`playwright` (网页)
- **存储**: `SQLite` (元数据索引), `Markdown` (文档), `JSON` (图谱缓存)
- **AI/LLM**: `OpenAI SDK` / `LangChain` (适配 gpt-4o-mini / 本地 Qwen)
- **可视化**: `NetworkX` (图计算) + `Pyvis` (Streamlit 交互渲染)
- **UI**: `Streamlit` (单页控制台)
- **配置**: `PyYAML` + 环境变量隔离

## 📁 标准目录结构

```text
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
│   └── cache/                  # 图谱JSON/向量缓存(可选)
├── ui/                         # 前端界面
│   └── dashboard.py             # Streamlit 主界面
├── tests/                      # 单元测试
├── requirements.txt             # 项目依赖
└── claude.md                   # 项目说明文档
```

