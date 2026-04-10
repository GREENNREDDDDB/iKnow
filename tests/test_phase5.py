"""Phase 5 测试用例 - 交叉推理 + 关系图谱 + Streamlit UI"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import sys
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.cross_reasoner import CrossReasoner
from src.processors.graph_builder import GraphBuilder
from src.processors.processor import Processor


class TestCrossReasoner:
    """交叉推理引擎测试"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return Processor()

    @pytest.fixture
    def cross_reasoner(self, processor):
        """创建交叉推理引擎实例"""
        return CrossReasoner(processor)

    def test_cross_reasoner_initialization(self, processor):
        """测试交叉推理引擎初始化"""
        reasoner = CrossReasoner(processor)
        assert reasoner.processor == processor

    def test_load_documents(self, cross_reasoner):
        """测试文档加载功能"""
        # 创建临时文档
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建测试文档
            doc1_path = temp_path / "test_doc1.md"
            doc1_path.write_text("# Test Document 1\nThis is content of document 1.", encoding='utf-8')
            
            doc2_path = temp_path / "test_doc2.md"
            doc2_path.write_text("# Test Document 2\nThis is content of document 2.", encoding='utf-8')
            
            # 加载文档
            contents = cross_reasoner._load_documents([doc1_path, doc2_path])
            
            assert len(contents) == 2
            assert "content of document 1" in contents[0]
            assert "content of document 2" in contents[1]

    def test_generate_cross_summary_prompt(self, cross_reasoner):
        """测试交叉总结提示词生成"""
        contents = ["Content of document 1", "Content of document 2"]
        topics = ["AI", "Technology"]
        
        prompt = cross_reasoner._generate_cross_summary_prompt(contents, topics)
        
        assert "分析以下多个文档之间的关联关系" in prompt
        assert "特别关注以下主题: AI, Technology" in prompt
        assert "文档 1:" in prompt
        assert "文档 2:" in prompt

    def test_perform_cross_reasoning(self, cross_reasoner):
        """测试交叉推理功能"""
        # 创建临时文档
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建测试文档
            doc1_path = temp_path / "test_doc1.md"
            doc1_path.write_text("# Test Document 1\nThis is content of document 1 about AI.", encoding='utf-8')
            
            doc2_path = temp_path / "test_doc2.md"
            doc2_path.write_text("# Test Document 2\nThis is content of document 2 about technology.", encoding='utf-8')
            
            # 执行交叉推理
            result = cross_reasoner.perform_cross_reasoning(
                [doc1_path, doc2_path], 
                topics=["AI", "Technology"],
                custom_title="Test Cross Analysis"
            )
            
            assert result.filename.startswith("Test_Cross_Analysis_")
            assert result.category == "交叉关系总结"
            assert "交叉关系分析报告" in result.markdown_content
            assert result.is_cross_summary


class TestGraphBuilder:
    """关系图谱构建器测试"""

    @pytest.fixture
    def graph_builder(self):
        """创建图谱构建器实例"""
        return GraphBuilder()

    def test_extract_entities(self, graph_builder):
        """测试实体提取"""
        content = "人工智能技术在2023年取得了重大进展，特别是在自然语言处理领域。"
        entities = graph_builder._extract_entities(content)
        
        assert len(entities) > 0
        # 检查是否提取到了一些预期的实体
        found_expected = any(ent in entities for ent in ["人工智能", "技术", "2023", "自然语言处理"])
        assert found_expected

    def test_build_graph(self, graph_builder):
        """测试图谱构建"""
        contents = [
            "人工智能技术在2023年取得了重大进展",
            "机器学习是人工智能的一个重要分支",
            "2023年人工智能领域有很多突破"
        ]
        titles = ["Doc1", "Doc2", "Doc3"]
        
        graph = graph_builder.build_graph(contents, titles)
        
        assert len(graph.nodes()) == 3
        assert "Doc1" in graph.nodes()
        assert "Doc2" in graph.nodes()
        assert "Doc3" in graph.nodes()

    def test_render_graph(self, graph_builder):
        """测试图谱渲染"""
        contents = [
            "人工智能技术在2023年取得了重大进展",
            "机器学习是人工智能的一个重要分支"
        ]
        titles = ["Doc1", "Doc2"]
        
        graph = graph_builder.build_graph(contents, titles)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_graph.html"
            
            result_path = graph_builder.render_graph(graph, output_path)
            
            assert result_path.exists()
            assert result_path.suffix == ".html"

    def test_export_graph_data(self, graph_builder):
        """测试图谱数据导出"""
        contents = [
            "人工智能技术在2023年取得了重大进展",
            "机器学习是人工智能的一个重要分支"
        ]
        titles = ["Doc1", "Doc2"]
        
        graph = graph_builder.build_graph(contents, titles)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_graph.json"
            
            result_path = graph_builder.export_graph_data(graph, output_path)
            
            assert result_path.exists()
            assert result_path.suffix == ".json"
            
            # 验证 JSON 内容
            with open(result_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert "nodes" in data
                assert "edges" in data
                assert "metadata" in data
                assert data["metadata"]["node_count"] == 2

    def test_build_and_render_from_documents(self, graph_builder):
        """测试从文档构建并渲染图谱"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建测试文档
            doc1_path = temp_path / "doc1.md"
            doc1_path.write_text("# Doc 1\n人工智能技术进展", encoding='utf-8')
            
            doc2_path = temp_path / "doc2.md"
            doc2_path.write_text("# Doc 2\n机器学习应用", encoding='utf-8')
            
            output_dir = temp_path / "output"
            
            result = graph_builder.build_and_render_from_documents([doc1_path, doc2_path], output_dir)
            
            assert "html" in result
            assert "json" in result
            assert "graph" in result
            assert result["html"].exists()
            assert result["json"].exists()


def test_integration_cross_reasoner_with_processor():
    """集成测试：交叉推理器与处理器的集成"""
    processor = Processor()
    cross_reasoner = CrossReasoner(processor)
    
    # 验证交叉推理器使用了处理器的功能
    assert cross_reasoner.processor == processor


def test_integration_graph_builder_with_system():
    """集成测试：图谱构建器与其他组件的兼容性"""
    graph_builder = GraphBuilder()
    
    # 测试基本功能
    contents = ["Test content 1", "Test content 2"]
    titles = ["Title 1", "Title 2"]
    
    graph = graph_builder.build_graph(contents, titles)
    
    assert len(graph.nodes()) == 2
    assert len(graph.edges()) >= 0  # 可能没有连接的节点


if __name__ == "__main__":
    pytest.main([__file__, "-v"])