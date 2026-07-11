# 🧠 iKnow - 个人资讯收集与整理系统

iKnow 已经从一个传统的独立 Python 爬虫项目，全面进化为 **[Hermes Agent](https://github.com/NousResearch/hermes-agent) 的原生插件架构**。

通过完全拥抱 AI Agent 的工具调用（Tool Calling）和网页浏览能力，iKnow 实现了从资讯获取、去重总结、知识图谱渲染到跨平台网页托管的**端到端全自动化闭环**。

---

## 🎯 核心特性

- **🤖 Agent 驱动抓取**：废弃了传统的 DOM 解析爬虫。通过 Hermes 内置的 `web_extract` 工具，由大模型自主浏览网页并提取核心内容，具备极强的反爬虫对抗和结构容错能力。
- **📝 结构化阅读与总结**：Agent 会自动提炼数百字的高质量资讯简报，并**强制要求在文档正文和文末提供可溯源的真实引用链接**。
- **🕸️ 零代码知识图谱**：废弃了正则表达式实体提取。由大模型深层理解文章逻辑，提取核心 Nodes 与 Edges，利用底层的 NetworkX + Pyvis 自动渲染出交互式的 HTML 关系网络。
- **☁️ 零维护云端托管**：每当产生新的总结或图谱，底层插件会自动触发 Git 提交，配合 GitHub Actions 自动编译出优雅的 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 网页知识库，随时随地在手机或微信上阅读。

---

## 📁 极简项目结构

```text
iKnow/
├── .github/
│   └── workflows/
│       └── deploy-docs.yml      # GitHub Actions 网页自动部署配置
├── config/
│   └── sources.json             # 关注源列表（由 Agent 自动管理增删查改）
├── data/                        # MkDocs Web 渲染的数据源
│   ├── documents/               # Agent 生成的资讯简报 (分类存储)
│   ├── graphs/                  # 生成的知识图谱 HTML
│   └── index.md                 # Web 欢迎主页
├── src/
│   └── iknow_tools.py           # 核心代码：挂载在 Hermes 上的插件工具集
├── CLAUDE.md                    # 内部开发与架构约束规范
├── mkdocs.yml                   # Web 知识库站点配置文件
└── README.md
```

---

## 🚀 部署与使用指南

### 1. 挂载插件到 Hermes Agent
假设你正在使用 WSL2 并安装了 [hermes-agent](https://github.com/NousResearch/hermes-agent)。你只需要将本项目的核心工具文件软链接到 Hermes 的工具目录下即可：

```bash
# 进入你的 hermes-agent 安装目录
cd /home/user/.hermes/hermes-agent

# 将 iKnow 工具集挂载进去 (请将后面的路径替换为你实际的项目路径)
ln -sf /mnt/d/4_DOCUMENTS/0_Learning/0_Projects/iKnow/src/iknow_tools.py tools/iknow_tools.py
```

### 2. 与 Agent 交互 (Prompt 示例)

配置完成后，打开 Hermes Agent 的聊天窗口（终端或绑定的微信机器人），你可以直接用自然语言使唤它：

#### 场景 A：管理关注源
> "调用 `iknow_manage_sources` 帮我看一下目前有哪些关注的资讯源。然后帮我添加一个新的关注源：『量子位』，网址是 `https://www.qbitai.com`，分类写『大模型资讯』。"

#### 场景 B：执行每日抓取工作流
> "调用 `iknow_get_pending_tasks` 获取今日需要采集的网站。请你去浏览其中的大模型资讯网站，阅读它的头条新闻，然后写一篇简短总结，并使用 `iknow_save_document` 保存，`category` 写'大模型资讯'，`keyword` 提取文章关键词。最后调用 `iknow_render_graph` 生成一个包含核心节点的关系图谱。"

#### 场景 C：设置定时任务
> "每天早上 8:30 分，自动执行上述的抓取、总结、保存和画图的流程。"

### 3. 查看知识库网页
当 Agent 告诉你任务完成后，底层插件已经自动将生成的文件 Push 到了当前 GitHub 仓库。
请前往 `https://<你的GitHub用户名>.github.io/<仓库名>/`，即可在手机或电脑上沉浸式阅读最新的专属资讯早报。

---

## 🔧 依赖要求

iKnow 的插件工具依赖于部分 Python 库来渲染图谱。请在运行 Hermes 的虚拟环境（venv）中安装：

```bash
pip install networkx pyvis
```