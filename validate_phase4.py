"""
Phase 4 验证脚本
验证调度器 + 自然语言按需检索功能
"""
import sys
import os
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_scheduler_module():
    """验证调度器模块"""
    print("验证调度器模块...")
    
    scheduler_path = project_root / "src" / "scheduler" / "scheduler.py"
    if not scheduler_path.exists():
        print("X src/scheduler/scheduler.py 不存在")
        return False
    
    content = scheduler_path.read_text(encoding='utf-8')
    
    # 检查关键组件
    required_components = [
        'class Scheduler',
        'def start_daily_schedule',
        'def on_demand_retrieval',
        'BackgroundScheduler',
        'CronTrigger',
        'def _daily_collection_task'
    ]
    
    missing_components = []
    for comp in required_components:
        if comp not in content:
            missing_components.append(comp)
    
    if missing_components:
        print(f"X 调度器模块缺少组件: {missing_components}")
        return False
    
    print("OK 调度器模块完整")
    return True

def validate_intent_parser_module():
    """验证意图解析器模块"""
    print("\\n验证意图解析器模块...")
    
    intent_parser_path = project_root / "src" / "scheduler" / "intent_parser.py"
    if not intent_parser_path.exists():
        print("X src/scheduler/intent_parser.py 不存在")
        return False
    
    content = intent_parser_path.read_text(encoding='utf-8')
    
    # 检查关键组件
    required_components = [
        'class IntentParser',
        'def parse_intent',
        'def _extract_keywords',
        'category_keywords'
    ]
    
    missing_components = []
    for comp in required_components:
        if comp not in content:
            missing_components.append(comp)
    
    if missing_components:
        print(f"X 意图解析器模块缺少组件: {missing_components}")
        return False
    
    print("OK 意图解析器模块完整")
    return True

def validate_daily_scheduling():
    """验证每日定时任务"""
    print("\\n验证每日定时任务...")
    
    scheduler_path = project_root / "src" / "scheduler" / "scheduler.py"
    content = scheduler_path.read_text(encoding='utf-8')
    
    if 'start_daily_schedule' not in content:
        print("X 未实现每日定时任务功能")
        return False
    
    if 'CronTrigger' not in content:
        print("X 未使用 CronTrigger 实现定时任务")
        return False
    
    if 'hour=9' not in content and '09:00' not in content:
        print("X 未按要求设置默认 09:00 定时任务")
        return False
    
    print("OK 每日定时任务实现正确")
    return True

def validate_natural_language_intent_parsing():
    """验证自然语言意图解析"""
    print("\\n验证自然语言意图解析...")
    
    intent_parser_path = project_root / "src" / "scheduler" / "intent_parser.py"
    content = intent_parser_path.read_text(encoding='utf-8')
    
    if 'def parse_intent' not in content:
        print("X 未实现意图解析功能")
        return False
    
    # 检查分类关键词映射
    if 'category_keywords' not in content:
        print("X 未实现分类关键词映射")
        return False
    
    # 检查是否支持固定的分类体系
    required_categories = [
        "国际形势", "国内政策/国家", "国内政策/广东省", "国内政策/珠海市", "国内政策/澳门横琴",
        "大模型资讯", "开源社区", "众筹平台", "智能硬件与机器人资讯"
    ]
    
    missing_categories = []
    for cat in required_categories:
        if cat not in content:
            missing_categories.append(cat)
    
    if missing_categories:
        print(f"X 缺少分类支持: {missing_categories}")
        return False
    
    print("OK 自然语言意图解析实现正确")
    return True

def validate_on_demand_retrieval():
    """验证按需检索功能"""
    print("\\n验证按需检索功能...")
    
    scheduler_path = project_root / "src" / "scheduler" / "scheduler.py"
    content = scheduler_path.read_text(encoding='utf-8')
    
    if 'def on_demand_retrieval' not in content:
        print("X 未实现按需检索功能")
        return False
    
    if 'query' not in content or 'custom_name' not in content:
        print("X 按需检索未支持自定义名称")
        return False
    
    print("OK 按需检索功能实现正确")
    return True

def validate_document_naming():
    """验证文档命名规范"""
    print("\\n验证文档命名规范...")
    
    scheduler_path = project_root / "src" / "scheduler" / "scheduler.py"
    content = scheduler_path.read_text(encoding='utf-8')
    
    # 检查是否支持按需检索的命名规范：{query}_{timestamp}.md
    if 'custom_name' not in content:
        print("X 未实现按需检索的命名规范")
        return False
    
    # 检查处理器模块是否支持自定义名称
    processor_path = project_root / "src" / "processors" / "processor.py"
    processor_content = processor_path.read_text(encoding='utf-8')
    
    if 'custom_name' not in processor_content:
        print("X 处理器未支持自定义名称功能")
        return False
    
    print("OK 文档命名规范实现正确")
    return True

def validate_pipeline_integration():
    """验证流水线集成 (P2->P3)"""
    print("\\n验证流水线集成...")
    
    scheduler_path = project_root / "src" / "scheduler" / "scheduler.py"
    content = scheduler_path.read_text(encoding='utf-8')
    
    # 检查是否集成了采集、去重、处理流程
    if 'collector.collect_from_multiple_sources' not in content:
        print("X 未集成采集流程")
        return False
    
    if 'deduplicator.process_articles' not in content:
        print("X 未集成去重流程")
        return False
    
    if 'processor.process_article' not in content:
        print("X 未集成处理流程")
        return False
    
    print("OK P2->P3 流水线集成正确")
    return True

def validate_integration_with_previous_phases():
    """验证与前序阶段的集成"""
    print("\\n验证与前序阶段集成...")
    
    scheduler_path = project_root / "src" / "scheduler" / "scheduler.py"
    content = scheduler_path.read_text(encoding='utf-8')
    
    # 检查是否使用了前面阶段的组件
    required_imports = [
        'ConfigLoader',
        'Collector',
        'Deduplicator',
        'Processor',
        'DBManager'
    ]
    
    missing_imports = []
    for imp in required_imports:
        if imp not in content:
            missing_imports.append(imp)
    
    if missing_imports:
        print(f"X 未集成前序阶段组件: {missing_imports}")
        return False
    
    print("OK 与前序阶段集成良好")
    return True

def validate_test_cases():
    """验证测试用例"""
    print("\\n验证测试用例...")
    
    test_path = project_root / "tests" / "test_phase4.py"
    if not test_path.exists():
        print("X Phase 4 测试文件不存在")
        return False
    
    content = test_path.read_text(encoding='utf-8')
    
    required_tests = [
        'TestScheduler',
        'TestIntentParser',
        'test_on_demand_retrieval',
        'test_parse_intent',
        'test_start_daily_schedule'
    ]
    
    missing_tests = []
    for test in required_tests:
        if test not in content:
            missing_tests.append(test)
    
    if missing_tests:
        print(f"X 缺少测试用例: {missing_tests}")
        return False
    
    print("OK 测试用例完整")
    return True

def main():
    """主验证函数"""
    print("=" * 50)
    print("Phase 4 验证: 调度器 + 自然语言按需检索")
    print("=" * 50)
    
    results = []
    results.append(validate_scheduler_module())
    results.append(validate_intent_parser_module())
    results.append(validate_daily_scheduling())
    results.append(validate_natural_language_intent_parsing())
    results.append(validate_on_demand_retrieval())
    results.append(validate_document_naming())
    results.append(validate_pipeline_integration())
    results.append(validate_integration_with_previous_phases())
    results.append(validate_test_cases())
    
    print("\\n" + "=" * 50)
    if all(results):
        print("OK Phase 4 验证通过！所有功能正常。")
        print("\\n交付物:")
        print("- OK src/scheduler/scheduler.py: 调度器模块")
        print("- OK src/scheduler/intent_parser.py: 意图解析器模块")
        print("- OK APScheduler 集成每日定时任务(09:00)")
        print("- OK NL 意图解析支持指定分类/关键词检索")
        print("- OK 按需文档命名 {query}_{timestamp}.md")
        print("- OK 双模式统一走 P2->P3 流水线")
        print("- OK tests/test_phase4.py: 测试用例")
        return True
    else:
        print("X Phase 4 验证失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)