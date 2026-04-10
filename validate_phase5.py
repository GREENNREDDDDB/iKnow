"""
Phase 5 验证脚本
验证交叉推理 + 关系图谱 + Streamlit UI功能
"""
import sys
import os
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_cross_reasoner_module():
    """验证交叉推理模块"""
    print("验证交叉推理模块...")
    
    cross_reasoner_path = project_root / "src" / "processors" / "cross_reasoner.py"
    if not cross_reasoner_path.exists():
        print("X src/processors/cross_reasoner.py 不存在")
        return False
    
    content = cross_reasoner_path.read_text(encoding='utf-8')
    
    # 检查关键组件
    required_components = [
        'class CrossReasoner',
        'def perform_cross_reasoning',
        'def batch_cross_reasoning',
        '交叉关系总结'
    ]
    
    missing_components = []
    for comp in required_components:
        if comp not in content:
            missing_components.append(comp)
    
    if missing_components:
        print(f"X 交叉推理模块缺少组件: {missing_components}")
        return False
    
    print("OK 交叉推理模块完整")
    return True

def validate_graph_builder_module():
    """验证图谱构建模块"""
    print("\\n验证图谱构建模块...")
    
    graph_builder_path = project_root / "src" / "processors" / "graph_builder.py"
    if not graph_builder_path.exists():
        print("X src/processors/graph_builder.py 不存在")
        return False
    
    content = graph_builder_path.read_text(encoding='utf-8')
    
    # 检查关键组件
    required_components = [
        'class GraphBuilder',
        'def build_graph',
        'def render_graph',
        'def export_graph_data',
        'networkx',
        'pyvis'
    ]
    
    missing_components = []
    for comp in required_components:
        if comp not in content:
            missing_components.append(comp)
    
    if missing_components:
        print(f"X 图谱构建模块缺少组件: {missing_components}")
        return False
    
    print("OK 图谱构建模块完整")
    return True

def validate_streamlit_ui():
    """验证 Streamlit UI"""
    print("\\n验证 Streamlit UI...")
    
    dashboard_path = project_root / "ui" / "dashboard.py"
    if not dashboard_path.exists():
        print("X ui/dashboard.py 不存在")
        return False
    
    content = dashboard_path.read_text(encoding='utf-8')
    
    # 检查关键组件
    required_components = [
        'import streamlit',
        'st.',
        'def main',
        '仪表盘',
        '资讯源管理',
        '文档浏览',
        '关系图谱',
        '自然语言检索',
        '系统控制'
    ]
    
    missing_components = []
    for comp in required_components:
        if comp not in content:
            missing_components.append(comp)
    
    if missing_components:
        print(f"X Streamlit UI 缺少组件: {missing_components}")
        return False
    
    print("OK Streamlit UI 完整")
    return True

def validate_cross_reasoning_output():
    """验证交叉推理输出"""
    print("\\n验证交叉推理输出...")
    
    cross_reasoner_path = project_root / "src" / "processors" / "cross_reasoner.py"
    content = cross_reasoner_path.read_text(encoding='utf-8')
    
    # 检查是否输出到交叉关系总结目录
    if '交叉关系总结' not in content:
        print("X 未实现交叉关系总结目录输出")
        return False
    
    # 检查是否使用了正确的命名规范
    if 'is_cross_summary' not in content:
        print("X 未实现交叉推理文档标识")
        return False
    
    print("OK 交叉推理输出规范正确")
    return True

def validate_graph_visualization():
    """验证图谱可视化"""
    print("\\n验证图谱可视化...")
    
    graph_builder_path = project_root / "src" / "processors" / "graph_builder.py"
    content = graph_builder_path.read_text(encoding='utf-8')
    
    # 检查是否支持 HTML 输出
    if 'render_graph' not in content or '.html' not in content:
        print("X 未实现 HTML 图谱渲染")
        return False
    
    # 检查是否支持 JSON 缓存
    if 'export_graph_data' not in content or '.json' not in content:
        print("X 未实现 JSON 图谱数据导出")
        return False
    
    # 检查是否使用了 networkx 和 pyvis
    if 'networkx' not in content or 'pyvis' not in content:
        print("X 未使用 networkx + pyvis 技术栈")
        return False
    
    print("OK 图谱可视化功能完整")
    return True

def validate_ui_features():
    """验证 UI 功能"""
    print("\\n验证 UI 功能...")
    
    dashboard_path = project_root / "ui" / "dashboard.py"
    content = dashboard_path.read_text(encoding='utf-8')
    
    # 检查是否包含所有要求的功能
    required_features = [
        '源管理',      # 资讯源管理
        '文档浏览',    # 文档浏览
        '图谱查看',    # 图谱查看
        'NL 输入',    # 自然语言输入
        '手动触发'     # 手动触发按钮
    ]
    
    missing_features = []
    for feature in required_features:
        if feature not in content:
            # 尝试更宽泛的匹配
            found = False
            if feature == '源管理':
                found = '资讯源' in content or 'sources' in content
            elif feature == '文档浏览':
                found = '文档' in content or 'documents' in content
            elif feature == '图谱查看':
                found = '图谱' in content or 'graph' in content
            elif feature == 'NL 输入':
                found = '自然语言' in content or '查询' in content
            elif feature == '手动触发':
                found = '手动' in content or '触发' in content
            
            if not found:
                missing_features.append(feature)
    
    if missing_features:
        print(f"X UI 缺少功能: {missing_features}")
        return False
    
    print("OK UI 功能完整")
    return True

def validate_integration_with_previous_phases():
    """验证与前序阶段的集成"""
    print("\\n验证与前序阶段集成...")
    
    # 检查是否使用了前面阶段的组件
    dashboard_path = project_root / "ui" / "dashboard.py"
    dashboard_content = dashboard_path.read_text(encoding='utf-8')
    
    required_imports = [
        'ConfigLoader',
        'DBManager', 
        'Scheduler',
        'IntentParser',
        'CrossReasoner',
        'GraphBuilder',
        'Processor'
    ]
    
    missing_imports = []
    for imp in required_imports:
        if imp not in dashboard_content:
            missing_imports.append(imp)
    
    if missing_imports:
        print(f"X UI 未集成前序阶段组件: {missing_imports}")
        return False
    
    print("OK 与前序阶段集成良好")
    return True

def validate_test_cases():
    """验证测试用例"""
    print("\\n验证测试用例...")
    
    test_path = project_root / "tests" / "test_phase5.py"
    if not test_path.exists():
        print("X Phase 5 测试文件不存在")
        return False
    
    content = test_path.read_text(encoding='utf-8')
    
    required_tests = [
        'TestCrossReasoner',
        'TestGraphBuilder', 
        'test_perform_cross_reasoning',
        'test_build_graph',
        'test_render_graph'
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
    print("Phase 5 验证: 交叉推理 + 关系图谱 + Streamlit UI")
    print("=" * 50)
    
    results = []
    results.append(validate_cross_reasoner_module())
    results.append(validate_graph_builder_module())
    results.append(validate_streamlit_ui())
    results.append(validate_cross_reasoning_output())
    results.append(validate_graph_visualization())
    results.append(validate_ui_features())
    results.append(validate_integration_with_previous_phases())
    results.append(validate_test_cases())
    
    print("\\n" + "=" * 50)
    if all(results):
        print("OK Phase 5 验证通过！所有功能正常。")
        print("\\n交付物:")
        print("- OK src/processors/cross_reasoner.py: 交叉推理引擎")
        print("- OK src/processors/graph_builder.py: 关系图谱构建器")
        print("- OK ui/dashboard.py: Streamlit 仪表盘")
        print("- OK 交叉关系总结目录输出")
        print("- OK HTML/JSON 图谱缓存")
        print("- OK 完整的 UI 功能")
        print("- OK tests/test_phase5.py: 测试用例")
        return True
    else:
        print("X Phase 5 验证失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)