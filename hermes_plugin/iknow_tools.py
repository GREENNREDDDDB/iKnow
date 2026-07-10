"""
iKnow 资讯采集与图谱工具集 (Hermes Agent 插件)

将该文件放置于 hermes-agent 的 tools/ 或 plugins/ 目录下，
即可让 Hermes 拥有全自动去重采集、知识库检索和图谱生成能力。
"""
import sys
from pathlib import Path
from typing import Dict, Any

# =====================================================================
# 环境准备：将 iKnow 的源码路径加入系统环境变量，以便能在 WSL2 中导入
# 请根据你在 WSL2 中实际的 iKnow 项目挂载路径进行修改，例如：/mnt/d/4_DOCUMENTS/0_Learning/0_Projects/iKnow
# =====================================================================
IKNOW_ROOT = "/mnt/d/4_DOCUMENTS/0_Learning/0_Projects/iKnow"
if IKNOW_ROOT not in sys.path:
    sys.path.append(IKNOW_ROOT)

try:
    from tools.registry import registry
except ImportError:
    # 兼容脱离 hermes-agent 环境的静态检查
    class MockRegistry:
        def register(self, *args, **kwargs): pass
    registry = MockRegistry()

from src.config.loader import ConfigLoader
from src.storage.db_manager import DBManager
from src.collectors.collector import Collector
from src.processors.deduplicator import Deduplicator
from src.processors.graph_builder import GraphBuilder

# 初始化 iKnow 核心组件
_iknow_config_path = Path(IKNOW_ROOT) / "config" / "sources.yaml"
_iknow_db_path = Path(IKNOW_ROOT) / "data" / "metadata.db"
_iknow_graphs_dir = Path(IKNOW_ROOT) / "data" / "graphs"

_config_loader = ConfigLoader(_iknow_config_path)
_db_manager = DBManager(_iknow_db_path)
_collector = Collector(_db_manager)
_deduplicator = Deduplicator(_db_manager)
_graph_builder = GraphBuilder()


def iknow_trigger_collection_handler(args: Dict[str, Any]) -> str:
    """触发所有启用的资讯源进行采集，并返回去重后的新文章摘要"""
    sources = _config_loader.get_enabled_sources()
    if not sources:
        return "没有找到启用的资讯源，请检查 sources.yaml 配置。"
    
    raw_articles = _collector.collect_from_multiple_sources(sources)
    unique_articles = _deduplicator.process_articles(raw_articles)
    
    if not unique_articles:
        return f"扫描了 {len(sources)} 个源，没有发现新文章（全部为重复内容）。"
    
    result = f"成功采集到 {len(unique_articles)} 篇新文章：\n\n"
    for i, article in enumerate(unique_articles, 1):
        result += f"{i}. [{article.category}] {article.title}\n"
        result += f"   内容预览: {article.content[:150]}...\n"
        result += f"   来源: {article.source_url}\n\n"
        
    return result + "\n作为 AI，请根据用户需求，对上述资讯进行深度总结、交叉推理或排版输出。"


def iknow_search_articles_handler(args: Dict[str, Any]) -> str:
    """从 iKnow 的本地 SQLite 数据库中检索已采集的历史文章"""
    category = args.get("category")
    limit = args.get("limit", 10)
    
    if category:
        articles = _db_manager.get_articles_by_category(category, limit)
    else:
        articles = _db_manager.get_all_articles(limit)
        
    if not articles:
        return "未检索到相关的历史文章。"
        
    result = f"检索到以下历史文章（按时间倒序）：\n\n"
    for idx, art in enumerate(articles, 1):
        # 此时取回的是 DB 行，可能需要根据具体 DB 结构解析
        # 假设 db 存储了 title, url (目前DB似乎只存了 hash 和 file，我们需要稍后优化 DB 存储 title/content)
        result += f"- 分类: {art['category']} | 文件名: {art['filename']} | 发布时间: {art['publish_time']}\n"
        
    return result


def iknow_generate_graph_handler(args: Dict[str, Any]) -> str:
    """提取文章实体，生成关系图谱 HTML"""
    # 此处为简化逻辑，实际可读取指定文章路径
    docs_dir = Path(IKNOW_ROOT) / "data" / "documents"
    md_files = list(docs_dir.rglob("*.md"))[:10]  # 取最近的10篇作为演示
    
    if not md_files:
        return "没有找到用于生成图谱的 Markdown 文档。"
        
    try:
        result_paths = _graph_builder.build_and_render_from_documents(md_files, _iknow_graphs_dir)
        return f"图谱生成成功！HTML 渲染文件路径: {result_paths['html']}\n请在浏览器中打开此文件查看可视化实体关系网络。"
    except Exception as e:
        return f"生成图谱时发生错误: {str(e)}"


# ------------------------------------------------------------------
# 工具注册到 Hermes
# ------------------------------------------------------------------
registry.register(
    name="iknow_trigger_collection",
    toolset="iknow",
    schema={
        "name": "iknow_trigger_collection",
        "description": "Trigger the iKnow news collector. Crawls RSS and Web sources, filters out duplicates, and returns the content of newly discovered articles.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    handler=iknow_trigger_collection_handler,
    emoji="📰"
)

registry.register(
    name="iknow_search_articles",
    toolset="iknow",
    schema={
        "name": "iknow_search_articles",
        "description": "Search the local iKnow SQLite database for historically collected articles.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The specific category to filter by (e.g., '大模型资讯', '国际形势'). Leave empty for all."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of articles to return (default: 10)."
                }
            }
        }
    },
    handler=iknow_search_articles_handler,
    emoji="🔍"
)

registry.register(
    name="iknow_generate_graph",
    toolset="iknow",
    schema={
        "name": "iknow_generate_graph",
        "description": "Generate a visual relationship graph (HTML) from recent articles using NetworkX and Pyvis.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    handler=iknow_generate_graph_handler,
    emoji="🕸️"
)
