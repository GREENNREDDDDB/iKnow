"""Streamlit 仪表盘 - iKnow 项目用户界面"""
import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import os

from src.config.loader import ConfigLoader
from src.storage.db_manager import DBManager
from src.scheduler.scheduler import Scheduler
from src.scheduler.intent_parser import IntentParser
from src.processors.cross_reasoner import CrossReasoner
from src.processors.graph_builder import GraphBuilder
from src.collectors.collector import Collector
from src.processors.deduplicator import Deduplicator
from src.processors.processor import Processor


def initialize_session_state():
    """初始化会话状态"""
    if 'config_loader' not in st.session_state:
        st.session_state.config_loader = ConfigLoader(Path("config/sources.yaml"))
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DBManager(Path("data/metadata.db"))
    if 'collector' not in st.session_state:
        st.session_state.collector = Collector(st.session_state.db_manager)
    if 'deduplicator' not in st.session_state:
        st.session_state.deduplicator = Deduplicator(st.session_state.db_manager)
    if 'processor' not in st.session_state:
        st.session_state.processor = Processor()
    if 'intent_parser' not in st.session_state:
        st.session_state.intent_parser = IntentParser()
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = Scheduler(
            st.session_state.config_loader,
            st.session_state.collector,
            st.session_state.deduplicator,
            st.session_state.processor
        )
    if 'cross_reasoner' not in st.session_state:
        st.session_state.cross_reasoner = CrossReasoner(st.session_state.processor)
    if 'graph_builder' not in st.session_state:
        st.session_state.graph_builder = GraphBuilder()


def main():
    """主界面"""
    st.set_page_config(page_title="iKnow 资讯收集与整理系统", layout="wide")
    st.title("🔍 iKnow - 个人资讯收集与整理系统")
    
    # 初始化会话状态
    initialize_session_state()
    
    # 侧边栏导航
    st.sidebar.header("导航菜单")
    page = st.sidebar.radio("选择功能", 
                            ["📊 仪表盘", "📡 资讯源管理", "📋 文档浏览", 
                             "📈 关系图谱", "💬 自然语言检索", "⚙️ 系统控制"])
    
    if page == "📊 仪表盘":
        dashboard_page()
    elif page == "📡 资讯源管理":
        sources_management_page()
    elif page == "📋 文档浏览":
        documents_page()
    elif page == "📈 关系图谱":
        graph_page()
    elif page == "💬 自然语言检索":
        nl_query_page()
    elif page == "⚙️ 系统控制":
        system_control_page()


def dashboard_page():
    """仪表盘页面"""
    st.header("📊 系统仪表盘")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总文章数", st.session_state.db_manager.get_article_count())
    
    with col2:
        stats = st.session_state.db_manager.get_category_stats()
        if stats:
            total_categories = len(stats)
        else:
            total_categories = 0
        st.metric("资讯分类数", total_categories)
    
    with col3:
        sources = st.session_state.config_loader.get_enabled_sources()
        st.metric("活跃资讯源", len(sources))
    
    # 分类统计图表
    if stats:
        df_stats = pd.DataFrame(stats)
        st.subheader("各分类文章分布")
        st.bar_chart(df_stats.set_index('category')['count'])
    
    # 最近文章列表
    st.subheader("最近采集的文章")
    recent_articles = st.session_state.db_manager.get_all_articles(limit=10)
    if recent_articles:
        df_recent = pd.DataFrame(recent_articles)
        st.dataframe(df_recent[['filename', 'category', 'created_at']].head(10))


def sources_management_page():
    """资讯源管理页面"""
    st.header("📡 资讯源管理")
    
    # 显示现有资讯源
    sources = st.session_state.config_loader.load_sources()
    enabled_sources = [s for s in sources if s.enabled]
    disabled_sources = [s for s in sources if not s.enabled]
    
    st.subheader("启用的资讯源")
    if enabled_sources:
        df_enabled = pd.DataFrame([{
            '名称': s.name,
            '分类': s.category,
            'URL': s.url,
            '类型': s.type
        } for s in enabled_sources])
        st.dataframe(df_enabled)
    else:
        st.info("暂无启用的资讯源")
    
    st.subheader("禁用的资讯源")
    if disabled_sources:
        df_disabled = pd.DataFrame([{
            '名称': s.name,
            '分类': s.category,
            'URL': s.url,
            '类型': s.type
        } for s in disabled_sources])
        st.dataframe(df_disabled)
    else:
        st.info("暂无禁用的资讯源")
    
    # 添加新资讯源
    st.subheader("添加新资讯源")
    with st.form("add_source_form"):
        name = st.text_input("源名称")
        category = st.selectbox("分类", [
            "国际形势", "国内政策/国家", "国内政策/广东省", 
            "国内政策/珠海市", "国内政策/澳门横琴", 
            "大模型资讯", "开源社区", "众筹平台", "智能硬件与机器人资讯"
        ])
        url = st.text_input("URL")
        source_type = st.selectbox("类型", ["rss", "web"])
        enabled = st.checkbox("启用", value=True)
        
        submitted = st.form_submit_button("添加资讯源")
        if submitted and name and url:
            from src.config.loader import SourceConfig
            new_source = SourceConfig(
                name=name,
                category=category,
                url=url,
                type=source_type,
                enabled=enabled
            )
            st.session_state.config_loader.add_source(new_source)
            st.success(f"已添加资讯源: {name}")
            st.rerun()


def documents_page():
    """文档浏览页面"""
    st.header("📋 文档浏览")
    
    # 获取所有分类
    categories = st.session_state.config_loader.get_all_categories()
    
    selected_category = st.selectbox("选择分类", ["全部"] + categories)
    
    # 获取文档文件
    documents_dir = Path("data/documents")
    if selected_category and selected_category != "全部":
        category_path = documents_dir / selected_category.replace("/", "\\")
    else:
        category_path = documents_dir
    
    # 递归获取所有 md 文件
    md_files = []
    for ext in ["*.md", "*.markdown"]:
        md_files.extend(list(category_path.rglob(ext)))
    
    if md_files:
        st.subheader(f"文档列表 ({len(md_files)} 个文件)")
        
        for md_file in md_files[:50]:  # 限制显示数量
            with st.expander(f"📄 {md_file.name}"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    st.markdown(content[:2000] + ("..." if len(content) > 2000 else ""))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"查看完整文档##{md_file.name}", key=f"view_{md_file.name}"):
                            st.code(content, language='markdown')
                    with col2:
                        with open(md_file, 'rb') as f:
                            st.download_button(
                                label=f"下载文档##{md_file.name}",
                                data=f.read(),
                                file_name=md_file.name,
                                mime='text/markdown'
                            )
                except Exception as e:
                    st.error(f"读取文件失败 {md_file.name}: {str(e)}")
    else:
        st.info("暂无文档")


def graph_page():
    """关系图谱页面"""
    st.header("📈 关系图谱")
    
    # 获取图谱文件
    graphs_dir = Path("data/graphs")
    html_files = list(graphs_dir.glob("*.html"))
    
    if html_files:
        st.subheader("已生成的关系图谱")
        html_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序
        
        for html_file in html_files[:10]:  # 显示最近的10个
            st.markdown(f"**{html_file.name}**")
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                # 由于 Streamlit 不能直接嵌入外部 HTML，这里提供下载链接
                st.download_button(
                    label=f"下载图谱: {html_file.name}",
                    data=html_content,
                    file_name=html_file.name,
                    mime='text/html'
                )
    else:
        st.info("暂无生成的关系图谱")
    
    # 选择文档生成新图谱
    st.subheader("生成新关系图谱")
    
    # 获取所有文档
    documents_dir = Path("data/documents")
    md_files = list(documents_dir.rglob("*.md"))
    
    if md_files:
        selected_files = st.multiselect(
            "选择用于生成图谱的文档",
            options=md_files,
            format_func=lambda x: x.relative_to(documents_dir)
        )
        
        if st.button("生成关系图谱") and len(selected_files) >= 2:
            try:
                result = st.session_state.graph_builder.build_and_render_from_documents(selected_files)
                st.success(f"图谱生成成功！HTML 文件: {result['html'].name}")
            except Exception as e:
                st.error(f"生成图谱失败: {str(e)}")
    else:
        st.warning("没有可选的文档用于生成图谱")


def nl_query_page():
    """自然语言检索页面"""
    st.header("💬 自然语言检索")
    
    query = st.text_area("请输入您的查询需求", height=100)
    
    if st.button("执行检索") and query:
        with st.spinner("正在执行按需检索..."):
            try:
                results = st.session_state.scheduler.on_demand_retrieval(query)
                if results:
                    st.success(f"检索完成！生成了 {len(results)} 个文档")
                    for result in results:
                        st.code(result)
                else:
                    st.info("未找到相关资讯或已存在")
            except Exception as e:
                st.error(f"检索失败: {str(e)}")
    
    # 交叉推理功能
    st.subheader("🔄 多文档交叉推理")
    
    # 获取所有文档
    documents_dir = Path("data/documents")
    md_files = list(documents_dir.rglob("*.md"))
    
    if md_files:
        selected_cross_files = st.multiselect(
            "选择用于交叉推理的文档",
            options=md_files,
            format_func=lambda x: x.relative_to(documents_dir)
        )
        
        cross_title = st.text_input("交叉分析标题", "交叉关系分析")
        
        if st.button("执行交叉推理") and len(selected_cross_files) >= 2:
            with st.spinner("正在进行交叉推理..."):
                try:
                    cross_doc = st.session_state.cross_reasoner.perform_cross_reasoning(
                        selected_cross_files, 
                        custom_title=cross_title
                    )
                    
                    # 保存交叉推理文档
                    output_path = st.session_state.processor.save_document(cross_doc)
                    st.success(f"交叉推理完成！文档已保存: {output_path}")
                    
                    # 显示生成的文档内容
                    with st.expander("查看交叉推理结果"):
                        content = output_path.read_text(encoding='utf-8')
                        st.markdown(content)
                        
                except Exception as e:
                    st.error(f"交叉推理失败: {str(e)}")
    else:
        st.warning("没有可选的文档用于交叉推理")


def system_control_page():
    """系统控制页面"""
    st.header("⚙️ 系统控制")
    
    # 调度器状态
    status = st.session_state.scheduler.get_status()
    st.subheader("调度器状态")
    st.json(status)
    
    # 启动/停止每日任务
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("启动每日定时任务 (09:00)"):
            st.session_state.scheduler.start_daily_schedule(hour=9, minute=0)
            st.success("每日定时任务已启动")
            st.rerun()
    
    with col2:
        if st.button("停止每日定时任务"):
            try:
                st.session_state.scheduler.stop_daily_schedule()
                st.success("每日定时任务已停止")
                st.rerun()
            except Exception as e:
                st.error(f"停止任务失败: {str(e)}")
    
    # 手动触发采集
    if st.button("手动触发一次采集"):
        with st.spinner("正在执行手动采集..."):
            try:
                st.session_state.scheduler._daily_collection_task()
                st.success("手动采集完成")
            except Exception as e:
                st.error(f"手动采集失败: {str(e)}")
    
    # 系统信息
    st.subheader("系统信息")
    st.write(f"- 数据库路径: {st.session_state.db_manager.db_path}")
    st.write(f"- 文档存储路径: {Path('data/documents')}")
    st.write(f"- 图谱存储路径: {Path('data/graphs')}")


if __name__ == "__main__":
    main()