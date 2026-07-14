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
def iknow_manage_sources_handler(args: Dict[str, Any], **kwargs) -> str:
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
def iknow_get_pending_tasks_handler(args: Dict[str, Any], **kwargs) -> str:
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
def _format_sources_block(sources: List[Dict]) -> str:
    """格式化来源参考块"""
    if not sources:
        return ""
    block = "\n\n---\n### 🔗 来源参考\n"
    for idx, source in enumerate(sources, 1):
        title = source.get("title", f"来源 {idx}")
        url = source.get("url", "#")
        block += f"{idx}. [{title}]({url})\n"
    return block


def _regenerate_toc(content: str) -> str:
    """从文档内容中提取 ### 标题，重新生成目录"""
    import re
    # 提取所有 ### 开头的标题（文章标题），排除来源参考和图谱等元数据节
    toc_entries = [t for t in re.findall(r'^###\s+(.+)$', content, re.MULTILINE)
                   if not any(skip in t for skip in ['🔗', '🕸️', '来源参考', '知识关系'])]
    if not toc_entries:
        return content
    
    toc = "\n## 📋 今日概览\n\n"
    for i, title in enumerate(toc_entries, 1):
        # 清理标题中的 markdown 链接语法用于锚点
        anchor = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', title).strip().replace(' ', '-').lower()
        toc += f"| {i} | [{title.strip()}](#{anchor}) |\n"
    
    # 替换或插入 TOC
    # 先移除旧的 TOC 块（如果在文档中存在）
    content = re.sub(r'\n## 📋 今日概览\n\n(\|.*\n)*\n?', '\n', content)
    
    # 在第一个 ## 标题之前插入新的 TOC（在 # 标题之后）
    first_h2 = re.search(r'\n## ', content)
    if first_h2:
        pos = first_h2.start()
        content = content[:pos] + '\n' + toc + content[pos:]
    else:
        # 在文档头之后插入
        lines = content.split('\n')
        # 找到第一段 header 结束（空行或 --- 后）
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith('# ') and i < 3:
                insert_at = i + 1
            elif line.strip() == '' and insert_at > 0:
                insert_at = i + 1
                break
        lines.insert(insert_at, toc)
        content = '\n'.join(lines)
    
    return content


def iknow_save_document_handler(args: Dict[str, Any], **kwargs) -> str:
    """保存 LLM 处理好的 Markdown 总结文档，并同步到 GitHub。
    
    支持两种模式：
    - mode='single' (默认): 每篇文章单独保存为 {timestamp}_{keyword}.md
    - mode='daily': 所有文章追加到当天汇总 {YYYYMMDD}.md，自动管理目录
    """
    category = args.get("category", "未分类")
    keyword = args.get("keyword", "资讯")
    content = args.get("content", "")
    sources = args.get("sources", [])
    mode = args.get("mode", "single")
    
    try:
        cat_dir = DOCS_DIR / category.replace("/", "_")
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        if mode == "daily":
            # 每日汇总模式：所有文章存入 {YYYYMMDD}.md
            date_str = datetime.now().strftime("%Y%m%d")
            date_display = datetime.now().strftime("%Y年%m月%d日")
            filename = f"{date_str}.md"
            filepath = cat_dir / filename
            
            # 给文章内容加来源
            content_with_sources = content + _format_sources_block(sources)
            
            if filepath.exists():
                # 追加模式
                existing = filepath.read_text(encoding="utf-8")
                # 检查是否已存在相同标题的节（去重）
                # 用 ### 标题的第一行来判断
                title_match = content.strip().split('\n')[0]
                if title_match.startswith('### ') and title_match in existing:
                    return f"⏭️ 跳过重复文章（已存在于 {filename}）: {title_match}"
                
                # 在最后一个 ### 节之后追加，或在文档末尾追加
                new_content = existing.rstrip() + "\n\n---\n\n" + content_with_sources
                # 重新生成 TOC
                new_content = _regenerate_toc(new_content)
                # 更新最后更新时间
                import re
                new_content = re.sub(
                    r'\*最后更新: .*\*',
                    f'*最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}*',
                    new_content
                )
            else:
                # 新建日汇总
                header = f"# {category} — {date_display}\n\n"
                header += f"> 📅 创建于 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                header += "---\n"
                new_content = header + content_with_sources
                new_content = _regenerate_toc(new_content)
                new_content += f"\n\n---\n\n*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
            
            filepath.write_text(new_content, encoding="utf-8")
            git_status = _sync_to_github(f"docs: daily update {category}/{filename}")
            
            article_count = new_content.count('\n### ') 
            return f"📄 每日汇总已更新: {filepath}\n📊 当前收录 {article_count} 篇文章\n{git_status}"
        
        else:
            # 单篇模式（向后兼容）
            content_with_sources = content + _format_sources_block(sources)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{timestamp}_{safe_keyword}.md"
            
            filepath = cat_dir / filename
            filepath.write_text(content_with_sources, encoding="utf-8")
            
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
                "mode": {"type": "string", "enum": ["single", "daily"], "description": "Save mode: 'single' (default) creates a separate file per article; 'daily' appends to {YYYYMMDD}.md with auto TOC + dedup."},
                "category": {"type": "string", "description": "Category of the document (e.g., '大模型资讯')"},
                "keyword": {"type": "string", "description": "Core keyword representing the content, used for the filename in 'single' mode."},
                "content": {"type": "string", "description": "The full markdown content. In 'daily' mode, each article should start with '### N. Title' for TOC generation."},
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

def iknow_render_graph_handler(args: Dict[str, Any], **kwargs) -> str:
    """
    接收 LLM 提取的实体和关系，利用 NetworkX + Pyvis 渲染本地 HTML。
    支持 daily 模式：自动将图谱嵌入当天的日汇总文档。
    """
    nodes = args.get("nodes", [])
    edges = args.get("edges", [])
    category = args.get("category", "未分类")
    keyword = args.get("keyword", "知识图谱")
    mode = args.get("mode", "single")
    target_document = args.get("target_document", None)  # 可选：指定目标 .md 文件名
    
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
        
        cat_dir = DOCS_DIR / category.replace("/", "_")
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
        
        if mode == "daily":
            # 每日模式：图谱命名为 {YYYMMDD}_{keyword}_graph.html
            date_str = datetime.now().strftime("%Y%m%d")
            graph_filename = f"{date_str}_{safe_keyword}_graph.html"
            # 目标文档：指定文件 > 当天的日汇总 > 最新 .md
            if target_document:
                target_md = cat_dir / target_document
            else:
                daily_md = cat_dir / f"{date_str}.md"
                if daily_md.exists():
                    target_md = daily_md
                else:
                    md_files = list(cat_dir.glob("*.md"))
                    target_md = sorted(md_files, key=lambda x: x.stat().st_mtime)[-1] if md_files else None
        else:
            # 单篇模式：保持原有命名逻辑
            graph_filename = f"{timestamp}_{safe_keyword}_graph.html"
            md_files = list(cat_dir.glob("*.md"))
            target_md = sorted(md_files, key=lambda x: x.stat().st_mtime)[-1] if md_files else None
        
        output_path = cat_dir / graph_filename
        net.save_graph(str(output_path))
        
        # 将图谱 iframe 嵌入目标文档
        if target_md and target_md.exists():
            iframe_html = f'\n\n---\n### 🕸️ 知识关系图谱\n<iframe src="./{graph_filename}" width="100%" height="600px" frameborder="0" style="border: 1px solid #eee; border-radius: 8px;"></iframe>\n'
            with open(target_md, "a", encoding="utf-8") as f:
                f.write(iframe_html)
            embed_target = str(target_md)
        else:
            embed_target = "无（未找到目标文档）"
        
        git_status = _sync_to_github(f"docs: auto-save graph {graph_filename} and embed in doc")
        
        return f"关系图谱已成功渲染并保存至: {output_path}\n嵌入目标: {embed_target}\n{git_status}"
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
                "mode": {"type": "string", "enum": ["single", "daily"], "description": "Mode: 'single' (default) matches latest .md; 'daily' targets today's {YYYYMMDD}.md."},
                "category": {"type": "string", "description": "Category of the document (e.g., '大模型资讯')"},
                "keyword": {"type": "string", "description": "Core keyword representing the graph, used for the filename."},
                "target_document": {"type": "string", "description": "Optional: explicit target .md filename (e.g., '20260714.md'). Overrides auto-detection."},
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
