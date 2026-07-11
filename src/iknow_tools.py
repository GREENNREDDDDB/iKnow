"""
iKnow 核心工具集 - 基于 Hermes Agent 深度重构
完全拥抱 Hermes 的工具调用、模型调度与网页浏览能力。
"""

import sys
import json
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
    """保存 LLM 处理好的 Markdown 总结文档"""
    category = args.get("category", "未分类")
    title = args.get("title", "未命名资讯")
    content = args.get("content", "")
    
    try:
        cat_dir = DOCS_DIR / category.replace("/", "_")
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}_{timestamp}.md"
        
        filepath = cat_dir / filename
        filepath.write_text(content, encoding="utf-8")
        
        return f"文档已成功保存至: {filepath}"
    except Exception as e:
        return f"保存失败: {str(e)}"

registry.register(
    name="iknow_save_document",
    toolset="iknow",
    schema={
        "name": "iknow_save_document",
        "description": "Save the summarized markdown content to the local knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string", "description": "The full markdown content with citations [^n]."}
            },
            "required": ["category", "title", "content"]
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
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = GRAPHS_DIR / f"knowledge_graph_{timestamp}.html"
        net.save_graph(str(output_path))
        
        return f"关系图谱已成功渲染并保存至: {output_path}"
    except ImportError:
        return "缺少依赖: 请在环境中安装 networkx 和 pyvis (pip install networkx pyvis)"
    except Exception as e:
        return f"图谱渲染失败: {str(e)}"

registry.register(
    name="iknow_render_graph",
    toolset="iknow",
    schema={
        "name": "iknow_render_graph",
        "description": "Render a knowledge graph HTML file using provided nodes and edges extracted by the LLM.",
        "parameters": {
            "type": "object",
            "properties": {
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
            "required": ["nodes", "edges"]
        }
    },
    handler=iknow_render_graph_handler,
    emoji="🕸️"
)
