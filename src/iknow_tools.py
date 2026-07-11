"""
iKnow 核心工具集 - 基于 Hermes Agent 深度重构
完全拥抱 Hermes 的工具调用、模型调度与网页浏览能力。
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# =====================================================================
# 兼容 Hermes 注册表
# =====================================================================
try:
    from tools.registry import registry
except ImportError:
    class MockRegistry:
        def register(self, *args, **kwargs): pass
    registry = MockRegistry()

# =====================================================================
# 配置与路径
# =====================================================================
IKNOW_ROOT = Path("/mnt/d/4_DOCUMENTS/0_Learning/0_Projects/iKnow") if sys.platform != "win32" else Path("d:/4_DOCUMENTS/0_Learning/0_Projects/iKnow")
DATA_DIR = IKNOW_ROOT / "data"
DOCS_DIR = DATA_DIR / "documents"
GRAPHS_DIR = DATA_DIR / "graphs"
SOURCES_FILE = IKNOW_ROOT / "config" / "sources.json" # 从 yaml 迁移到更易被 LLM 处理的 json

# 初始化目录
for d in [DOCS_DIR, GRAPHS_DIR, SOURCES_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

if not SOURCES_FILE.exists():
    SOURCES_FILE.write_text(json.dumps({"sources": []}, ensure_ascii=False))

# =====================================================================
# 自动同步 GitHub 逻辑
# =====================================================================
def _sync_to_github(commit_msg: str) -> str:
    """执行 Git 提交和推送，自动将生成的文档上传至 GitHub"""
    try:
        cwd = str(IKNOW_ROOT)
        # 添加 data 目录下的所有变动
        subprocess.run(["git", "add", "data/"], cwd=cwd, check=True, capture_output=True)
        
        # 检查是否有变更，如果没有变更则跳过
        status = subprocess.run(["git", "status", "--porcelain", "data/"], cwd=cwd, capture_output=True, text=True)
        if not status.stdout.strip():
            return "（没有检测到新文件，跳过 Git 同步）"
        
        # 提交并推送
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=cwd, check=True, capture_output=True)
        subprocess.run(["git", "push"], cwd=cwd, check=True, capture_output=True)
        return "（文件已成功同步至 GitHub 仓库）"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        return f"（Git 同步失败: {error_msg}）"
    except Exception as e:
        return f"（Git 同步出现异常: {str(e)}）"


# =====================================================================
# 1. 目标网站管理模块 (CRUD)
# =====================================================================
def iknow_manage_sources_handler(args: Dict[str, Any]) -> str:
    """管理 iKnow 资讯源（增删查改）"""
    action = args.get("action")
    name = args.get("name")
    url = args.get("url")
    category = args.get("category", "默认分类")
    
    try:
        data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        sources = data.get("sources", [])
        
        if action == "list":
            if not sources:
                return "当前没有配置任何资讯源。"
            res = "当前资讯源列表：\n"
            for s in sources:
                res += f"- [{s['category']}] {s['name']} : {s['url']}\n"
            return res
            
        elif action == "add":
            if any(s['name'] == name for s in sources):
                return f"源 '{name}' 已存在。"
            sources.append({"name": name, "url": url, "category": category})
            SOURCES_FILE.write_text(json.dumps({"sources": sources}, ensure_ascii=False, indent=2))
            return f"成功添加源: {name}"
            
        elif action == "remove":
            new_sources = [s for s in sources if s['name'] != name]
            if len(new_sources) == len(sources):
                return f"未找到名为 '{name}' 的源。"
            SOURCES_FILE.write_text(json.dumps({"sources": new_sources}, ensure_ascii=False, indent=2))
            return f"成功删除源: {name}"
            
        return "未知的 action，请使用 list, add, 或 remove。"
    except Exception as e:
        return f"操作失败: {str(e)}"

registry.register(
    name="iknow_manage_sources",
    toolset="iknow",
    schema={
        "name": "iknow_manage_sources",
        "description": "Manage target websites/sources for iKnow (Create, Read, Delete).",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "add", "remove"]},
                "name": {"type": "string", "description": "Name of the source (required for add/remove)"},
                "url": {"type": "string", "description": "URL of the source (required for add)"},
                "category": {"type": "string", "description": "Category of the source"}
            },
            "required": ["action"]
        }
    },
    handler=iknow_manage_sources_handler,
    emoji="📡"
)


# =====================================================================
# 2. 网页资源获取流转 (结合 Hermes web_extract)
# =====================================================================
def iknow_get_pending_tasks_handler(args: Dict[str, Any]) -> str:
    """获取今天需要采集的源列表，提示 LLM 去调用 web_extract"""
    try:
        data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        sources = data.get("sources", [])
        if not sources:
            return "没有可用的资讯源，请先使用 iknow_manage_sources 添加。"
            
        res = "以下是需要采集的资讯源。请使用内置的 `web_extract` 或 `web_search` 工具访问这些 URL，并提取核心内容：\n\n"
        for s in sources:
            res += f"- 分类: {s['category']} | URL: {s['url']}\n"
        res += "\n读取完成后，请对内容进行总结、去重，并调用 `iknow_save_document` 保存。"
        return res
    except Exception as e:
        return f"获取失败: {str(e)}"

registry.register(
    name="iknow_get_pending_tasks",
    toolset="iknow",
    schema={
        "name": "iknow_get_pending_tasks",
        "description": "Get the list of target URLs that need to be processed today. The agent should use its native web tools to read them.",
        "parameters": {"type": "object", "properties": {}}
    },
    handler=iknow_get_pending_tasks_handler,
    emoji="📋"
)


# =====================================================================
# 3 & 4. 核心业务：文档存储与图谱渲染
# =====================================================================
def iknow_save_document_handler(args: Dict[str, Any]) -> str:
    """保存 LLM 处理好的 Markdown 总结文档，并同步到 GitHub"""
    category = args.get("category", "未分类")
    keyword = args.get("keyword", "资讯")
    content = args.get("content", "")
    sources = args.get("sources", [])
    
    # 将源链接附加到文档末尾
    if sources:
        content += "\n\n---\n### 🔗 来源参考\n"
        for idx, source in enumerate(sources, 1):
            title = source.get("title", f"来源 {idx}")
            url = source.get("url", "#")
            content += f"{idx}. [{title}]({url})\n"
    
    try:
        cat_dir = DOCS_DIR / category.replace("/", "_")
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{timestamp}_{safe_keyword}.md"
        
        filepath = cat_dir / filename
        filepath.write_text(content, encoding="utf-8")
        
        git_status = _sync_to_github(f"docs: auto-save document {filename}")
        
        return f"文档已成功保存至: {filepath}\n{git_status}"
    except Exception as e:
        return f"保存失败: {str(e)}"

registry.register(
    name="iknow_save_document",
    toolset="iknow",
    schema={
        "name": "iknow_save_document",
        "description": "Save the summarized markdown content to the local knowledge base, and automatically sync to GitHub. Naming convention: [timestamp]_[keyword].md",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category of the document (e.g., '大模型资讯')"},
                "keyword": {"type": "string", "description": "Core keyword representing the content, used for the filename."},
                "content": {"type": "string", "description": "The full markdown content with inline citations like [1]."},
                "sources": {
                    "type": "array",
                    "description": "List of source URLs and titles used to generate this summary. These will be appended at the end of the document.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the source article/page"},
                            "url": {"type": "string", "description": "URL of the source"}
                        },
                        "required": ["title", "url"]
                    }
                }
            },
            "required": ["category", "keyword", "content", "sources"]
        }
    },
    handler=iknow_save_document_handler,
    emoji="💾"
)

def iknow_render_graph_handler(args: Dict[str, Any]) -> str:
    """
    接收 LLM 提取的实体和关系，利用 NetworkX + Pyvis 渲染本地 HTML。
    完全取代了原来正则提取实体的硬编码逻辑。
    """
    nodes = args.get("nodes", [])
    edges = args.get("edges", [])
    category = args.get("category", "未分类")
    keyword = args.get("keyword", "知识图谱")
    
    if not nodes or not edges:
        return "节点或边为空，无法生成图谱。"
        
    try:
        import networkx as nx
        from pyvis.network import Network
        
        G = nx.Graph()
        for node in nodes:
            G.add_node(node.get("id"), label=node.get("label", node.get("id")), type=node.get("type", "entity"))
            
        for edge in edges:
            G.add_edge(edge.get("source"), edge.get("target"), label=edge.get("relation", ""), weight=edge.get("weight", 1))
            
        net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
        net.from_nx(G)
        
        # 将图谱直接保存在对应的文档目录下，方便同页渲染
        cat_dir = DOCS_DIR / category.replace("/", "_")
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{timestamp}_{safe_keyword}_graph.html"
        
        output_path = cat_dir / filename
        net.save_graph(str(output_path))
        
        # 寻找同分类下最新的 markdown 文档，将图谱 iframe 嵌入其中
        md_files = list(cat_dir.glob("*.md"))
        if md_files:
            latest_md = sorted(md_files, key=lambda x: x.stat().st_mtime)[-1]
            iframe_html = f'\n\n---\n### 🕸️ 知识关系图谱\n<iframe src="./{filename}" width="100%" height="600px" frameborder="0" style="border: 1px solid #eee; border-radius: 8px;"></iframe>\n'
            with open(latest_md, "a", encoding="utf-8") as f:
                f.write(iframe_html)
        
        git_status = _sync_to_github(f"docs: auto-save graph {filename} and embed in doc")
        
        return f"关系图谱已成功渲染并保存至: {output_path}\n{git_status}"
    except ImportError:
        return "缺少依赖: 请在环境中安装 networkx 和 pyvis (pip install networkx pyvis)"
    except Exception as e:
        return f"图谱渲染失败: {str(e)}"

registry.register(
    name="iknow_render_graph",
    toolset="iknow",
    schema={
        "name": "iknow_render_graph",
        "description": "Render a knowledge graph HTML file using provided nodes and edges, and automatically sync to GitHub. Naming convention: [timestamp]_[keyword].html",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category of the document (e.g., '大模型资讯')"},
                "keyword": {"type": "string", "description": "Core keyword representing the graph, used for the filename."},
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "label": {"type": "string"},
                            "type": {"type": "string"}
                        },
                        "required": ["id"]
                    }
                },
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "relation": {"type": "string"}
                        },
                        "required": ["source", "target"]
                    }
                }
            },
            "required": ["category", "keyword", "nodes", "edges"]
        }
    },
    handler=iknow_render_graph_handler,
    emoji="🕸️"
)
