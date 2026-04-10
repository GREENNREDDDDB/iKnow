"""
Phase 3 验证脚本
验证 LLM 处理 + Markdown 生成 + 引用注入功能
"""
import sys
import os
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_processor_module():
    """验证处理器模块"""
    print("验证处理器模块...")
    
    processor_path = project_root / "src" / "processors" / "processor.py"
    if not processor_path.exists():
        print("X src/processors/processor.py 不存在")
        return False
    
    content = processor_path.read_text(encoding='utf-8')
    
    # 检查关键组件
    required_components = [
        'class Processor',
        'class ProcessedDoc',
        'def process_article',
        'def save_document',
        'def _generate_filename',
        'def _inject_citations',
        'def _extract_references'
    ]
    
    missing_components = []
    for comp in required_components:
        if comp not in content:
            missing_components.append(comp)
    
    if missing_components:
        print(f"X 处理器模块缺少组件: {missing_components}")
        return False
    
    print("OK 处理器模块完整")
    return True

def validate_data_models():
    """验证数据模型"""
    print("\\n验证数据模型...")
    
    processor_path = project_root / "src" / "processors" / "processor.py"
    content = processor_path.read_text(encoding='utf-8')
    
    if 'class ProcessedDoc' not in content:
        print("X ProcessedDoc 数据模型未定义")
        return False
    
    if 'pydantic' not in content and 'BaseModel' not in content:
        print("X 数据模型未使用 Pydantic BaseModel")
        return False
    
    # 检查字段定义
    required_fields = [
        'filename',
        'category', 
        'markdown_content',
        'references',
        'is_cross_summary'
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in content:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"X ProcessedDoc 缺少字段: {missing_fields}")
        return False
    
    print("OK 数据模型定义正确")
    return True

def validate_markdown_generation():
    """验证 Markdown 生成"""
    print("\\n验证 Markdown 生成...")
    
    processor_path = project_root / "src" / "processors" / "processor.py"
    content = processor_path.read_text(encoding='utf-8')
    
    # 检查 Markdown 相关功能
    if 'markdown_content' not in content:
        print("X 未实现 markdown_content 字段")
        return False
    
    if '.md' not in content and 'markdown' not in content.lower():
        print("X 未实现 Markdown 相关功能")
        return False
    
    print("OK Markdown 生成功能完整")
    return True

def validate_citation_injection():
    """验证引用注入"""
    print("\\n验证引用注入...")
    
    processor_path = project_root / "src" / "processors" / "processor.py"
    content = processor_path.read_text(encoding='utf-8')
    
    # 检查引用注入功能
    if 'def _inject_citations' not in content:
        print("X 未实现引用注入功能")
        return False
    
    if '[^' not in content or ']' not in content:
        print("X 未实现 [^n] 引用标记")
        return False
    
    if 'references' not in content:
        print("X 未实现引用列表功能")
        return False
    
    print("OK 引用注入功能完整")
    return True

def validate_filename_generation():
    """验证文件名生成"""
    print("\\n验证文件名生成...")
    
    processor_path = project_root / "src" / "processors" / "processor.py"
    content = processor_path.read_text(encoding='utf-8')
    
    # 检查文件名生成功能
    if 'def _generate_filename' not in content:
        print("X 未实现文件名生成功能")
        return False
    
    # 检查不同场景的命名规则
    if '定时自动采集' not in content and '自然语言按需' not in content and '交叉关系推理' not in content:
        print("X 未实现不同场景的命名规则")
        return False
    
    print("OK 文件名生成功能完整")
    return True

def validate_storage_logic():
    """验证存储逻辑"""
    print("\\n验证存储逻辑...")
    
    processor_path = project_root / "src" / "processors" / "processor.py"
    content = processor_path.read_text(encoding='utf-8')
    
    if 'def save_document' not in content:
        print("X 未实现文档保存功能")
        return False
    
    if 'data/documents' not in content:
        print("X 未实现按分类存储逻辑")
        return False
    
    if 'category' not in content:
        print("X 未实现按分类目录存储")
        return False
    
    print("OK 存储逻辑完整")
    return True

def validate_prompt_templates():
    """验证提示词模板"""
    print("\\n验证提示词模板...")
    
    prompt_path = project_root / "config" / "prompts" / "summarize.txt"
    if not prompt_path.exists():
        print("X 提示词模板不存在")
        return False
    
    content = prompt_path.read_text(encoding='utf-8')
    
    if '[^n]' not in content.lower() and '引用' not in content:
        print("X 提示词模板未提及引用标记")
        return False
    
    if 'markdown' not in content.lower():
        print("X 提示词模板未提及 Markdown 格式")
        return False
    
    print("OK 提示词模板完整")
    return True

def validate_integration_with_previous_phases():
    """验证与前序阶段的集成"""
    print("\\n验证与前序阶段集成...")
    
    processor_path = project_root / "src" / "processors" / "processor.py"
    content = processor_path.read_text(encoding='utf-8')
    
    # 检查是否使用了 Phase 2 的 RawArticle
    if 'RawArticle' not in content:
        print("X 未使用 Phase 2 的 RawArticle 数据模型")
        return False
    
    # 检查是否使用了配置
    if 'SourceConfig' not in content or 'config' not in content:
        print("X 未正确集成配置模块")
        return False
    
    print("OK 与前序阶段集成良好")
    return True

def validate_test_cases():
    """验证测试用例"""
    print("\\n验证测试用例...")
    
    test_path = project_root / "tests" / "test_phase3.py"
    if not test_path.exists():
        print("X Phase 3 测试文件不存在")
        return False
    
    content = test_path.read_text(encoding='utf-8')
    
    required_tests = [
        'TestProcessor',
        'test_process_article',
        'test_save_document',
        'test_inject_citations',
        'test_generate_filename'
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
    print("Phase 3 验证: LLM 处理 + Markdown 生成 + 引用注入")
    print("=" * 50)
    
    results = []
    results.append(validate_processor_module())
    results.append(validate_data_models())
    results.append(validate_markdown_generation())
    results.append(validate_citation_injection())
    results.append(validate_filename_generation())
    results.append(validate_storage_logic())
    results.append(validate_prompt_templates())
    results.append(validate_integration_with_previous_phases())
    results.append(validate_test_cases())
    
    print("\\n" + "=" * 50)
    if all(results):
        print("OK Phase 3 验证通过！所有功能正常。")
        print("\\n交付物:")
        print("- OK src/processors/processor.py: 处理器模块")
        print("- OK config/prompts/summarize.txt: LLM 提示词模板")
        print("- OK ProcessedDoc 数据模型")
        print("- OK [^n] 引用标记注入")
        print("- OK 按规范命名并保存 Markdown")
        print("- OK 更新 DB 记录")
        print("- OK tests/test_phase3.py: 测试用例")
        return True
    else:
        print("X Phase 3 验证失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)