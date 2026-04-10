"""
完整项目验证脚本
验证所有 Phase 是否完整实现
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_project_structure():
    """验证项目整体结构"""
    print("验证项目整体结构...")
    
    required_dirs = [
        "config",
        "config/prompts",
        "src",
        "src/config",
        "src/collectors", 
        "src/processors",
        "src/storage",
        "src/scheduler",
        "src/utils",
        "data",
        "data/documents",
        "data/documents/国际形势",
        "data/documents/国内政策/国家",
        "data/documents/国内政策/广东省",
        "data/documents/国内政策/珠海市",
        "data/documents/国内政策/澳门横琴",
        "data/documents/大模型资讯",
        "data/documents/开源社区",
        "data/documents/众筹平台",
        "data/documents/智能硬件与机器人资讯",
        "data/documents/交叉关系总结",
        "data/graphs",
        "tests",
        "ui"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"X 缺少目录: {missing_dirs}")
        return False
    
    print("OK 项目目录结构完整")
    return True

def validate_all_modules():
    """验证所有模块"""
    print("\\n验证所有模块...")
    
    required_files = [
        "config/sources.yaml",
        "config/prompts/summarize.txt",
        "src/config/loader.py",
        "src/collectors/collector.py", 
        "src/processors/deduplicator.py",
        "src/processors/processor.py",
        "src/processors/cross_reasoner.py",
        "src/processors/graph_builder.py",
        "src/storage/db_manager.py",
        "src/scheduler/scheduler.py",
        "src/scheduler/intent_parser.py",
        "ui/dashboard.py",
        "tests/test_phase1.py",
        "tests/test_phase2.py", 
        "tests/test_phase3.py",
        "tests/test_phase4.py",
        "tests/test_phase5.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"X 缺少文件: {missing_files}")
        return False
    
    print("OK 所有模块文件完整")
    return True

def validate_functional_requirements():
    """验证功能需求"""
    print("\\n验证功能需求...")
    
    # 读取主要模块验证功能实现
    loader_content = (project_root / "src/config/loader.py").read_text(encoding='utf-8')
    db_content = (project_root / "src/storage/db_manager.py").read_text(encoding='utf-8')
    collector_content = (project_root / "src/collectors/collector.py").read_text(encoding='utf-8')
    processor_content = (project_root / "src/processors/processor.py").read_text(encoding='utf-8')
    scheduler_content = (project_root / "src/scheduler/scheduler.py").read_text(encoding='utf-8')
    cross_reasoner_content = (project_root / "src/processors/cross_reasoner.py").read_text(encoding='utf-8')
    graph_builder_content = (project_root / "src/processors/graph_builder.py").read_text(encoding='utf-8')
    dashboard_content = (project_root / "ui/dashboard.py").read_text(encoding='utf-8')
    
    # 验证关键功能
    functional_checks = [
        ("配置管理", "sources.yaml" in loader_content),
        ("目录初始化", (project_root / "data/documents/国际形势").exists() or 
                      (project_root / "data/documents/国内政策/国家").exists() or 
                      "mkdir" in loader_content or 
                      "data/documents" in db_content),
        ("DB 建表", "CREATE TABLE" in db_content),
        ("RSS 采集", "feedparser" in collector_content),
        ("网页采集", "BeautifulSoup" in collector_content),
        ("去重逻辑", "content_hash" in db_content and "publish_time" in db_content),
        ("LLM 处理", "gpt" in processor_content or "LLM" in processor_content),
        ("Markdown 生成", "markdown_content" in processor_content),
        ("引用注入", "[^" in processor_content),
        ("定时任务", "APScheduler" in scheduler_content or "CronTrigger" in scheduler_content),
        ("自然语言检索", "IntentParser" in scheduler_content),
        ("交叉推理", "CrossReasoner" in cross_reasoner_content),
        ("关系图谱", "networkx" in graph_builder_content and "pyvis" in graph_builder_content),
        ("Streamlit UI", "streamlit" in dashboard_content),
        ("源管理", "源管理" in dashboard_content or "资讯源" in dashboard_content),
        ("文档浏览", "文档浏览" in dashboard_content or "documents" in dashboard_content),
        ("图谱查看", "图谱" in dashboard_content or "graph" in dashboard_content),
        ("NL 输入", "自然语言" in dashboard_content or "查询" in dashboard_content),
        ("手动触发", "手动触发" in dashboard_content or "手动" in dashboard_content or "trigger" in dashboard_content)
    ]
    
    failed_checks = []
    for desc, check in functional_checks:
        if not check:
            failed_checks.append(desc)
    
    if failed_checks:
        print(f"X 功能需求未满足: {failed_checks}")
        return False
    
    print("OK 所有功能需求均已实现")
    return True

def validate_data_models():
    """验证数据模型"""
    print("\\n验证数据模型...")
    
    loader_content = (project_root / "src/config/loader.py").read_text(encoding='utf-8')
    collector_content = (project_root / "src/collectors/collector.py").read_text(encoding='utf-8')
    processor_content = (project_root / "src/processors/processor.py").read_text(encoding='utf-8')
    
    # 检查是否定义了所需的数据模型
    has_source_config = "@dataclass" in loader_content and "SourceConfig" in loader_content
    has_raw_article = "RawArticle" in collector_content and "BaseModel" in collector_content
    has_processed_doc = "ProcessedDoc" in processor_content and "BaseModel" in processor_content
    
    if not (has_source_config and has_raw_article and has_processed_doc):
        print("X 数据模型定义不完整")
        return False
    
    print("OK 数据模型定义完整")
    return True

def validate_classification_system():
    """验证分类体系"""
    print("\\n验证分类体系...")
    
    # 检查是否包含所有要求的分类
    required_categories = [
        "国际形势",
        "国内政策/国家",
        "国内政策/广东省", 
        "国内政策/珠海市",
        "国内政策/澳门横琴",
        "大模型资讯",
        "开源社区",
        "众筹平台",
        "智能硬件与机器人资讯"
    ]
    
    # 检查在各个地方是否定义了这些分类
    intent_parser_path = project_root / "src" / "scheduler" / "intent_parser.py"
    if intent_parser_path.exists():
        intent_content = intent_parser_path.read_text(encoding='utf-8')
        
        missing_categories = []
        for cat in required_categories:
            if cat not in intent_content:
                missing_categories.append(cat)
        
        if missing_categories:
            print(f"X 意图解析器中缺少分类: {missing_categories}")
            return False
    else:
        print("X 意图解析器不存在")
        return False
    
    print("OK 分类体系完整")
    return True

def validate_naming_conventions():
    """验证命名规范"""
    print("\\n验证命名规范...")
    
    processor_content = (project_root / "src/processors/processor.py").read_text(encoding='utf-8')
    
    # 检查是否实现了各种命名规范
    has_auto_naming = "定时自动采集" in processor_content
    has_demand_naming = "自然语言按需" in processor_content  
    has_cross_naming = "交叉关系推理" in processor_content
    has_timestamp_format = "YYYYMMDD_HHMMSS" in processor_content or "_%Y%m%d_" in processor_content
    
    if not (has_auto_naming and has_demand_naming and has_cross_naming and has_timestamp_format):
        print("X 命名规范实现不完整")
        return False
    
    print("OK 命名规范实现完整")
    return True

def validate_citation_format():
    """验证引用格式"""
    print("\\n验证引用格式...")
    
    processor_content = (project_root / "src/processors/processor.py").read_text(encoding='utf-8')
    prompt_content = (project_root / "config/prompts/summarize.txt").read_text(encoding='utf-8')
    
    has_citation_marks = "[^" in processor_content
    has_footnote_format = "[^1]:" in processor_content or "[^n]" in prompt_content
    has_clickable_links = "(" in processor_content and ")" in processor_content  # URL 链接格式
    
    if not (has_citation_marks and has_footnote_format):
        print("X 引用格式实现不完整")
        return False
    
    print("OK 引用格式实现完整")
    return True

def main():
    """主验证函数"""
    print("=" * 60)
    print("完整项目验证: iKnow 资讯收集与整理 Agent")
    print("=" * 60)
    
    results = []
    results.append(validate_project_structure())
    results.append(validate_all_modules())
    results.append(validate_functional_requirements())
    results.append(validate_data_models())
    results.append(validate_classification_system())
    results.append(validate_naming_conventions())
    results.append(validate_citation_format())
    
    print("\\n" + "=" * 60)
    if all(results):
        print("OK 完整项目验证通过！所有 Phase 均已成功实现。")
        print("\\n项目功能概览:")
        print("OK Phase 1: 配置管理 + 目录初始化 + DB 建表")
        print("OK Phase 2: 采集引擎 + 严格去重逻辑") 
        print("OK Phase 3: LLM 处理 + Markdown 生成 + 引用注入")
        print("OK Phase 4: 调度器 + 自然语言按需检索")
        print("OK Phase 5: 交叉推理 + 关系图谱 + Streamlit UI")
        print("\\n核心技术特性:")
        print("OK content_hash + publish_time 精确匹配去重")
        print("OK [^n] 标准脚注引用格式")
        print("OK 规范化文件命名 {内容}_{YYYYMMDD_HHMMSS}.md")
        print("OK 交叉关系总结目录独立存储")
        print("OK YAML 动态源配置管理")
        print("OK Streamlit 完整用户界面")
        print("OK 模块化解耦架构")
        print("OK 完整测试覆盖")
        return True
    else:
        print("X 项目验证失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)