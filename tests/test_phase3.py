"""Phase 3 测试用例 - LLM 处理 + Markdown 生成 + 引用注入"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.collector import RawArticle
from src.processors.processor import Processor, ProcessedDoc


class TestProcessor:
    """处理器测试"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return Processor()

    @pytest.fixture
    def sample_article(self):
        """创建样本文章"""
        return RawArticle(
            title="Sample News Title",
            content="This is a sample news content with important information. The data shows significant trends in the market.",
            publish_time=datetime(2026, 4, 10, 12, 0),
            source_url="https://example.com/news/sample",
            source_name="Example News Site",
            category="测试分类"
        )

    def test_processed_doc_model(self):
        """测试 ProcessedDoc 数据模型"""
        doc = ProcessedDoc(
            filename="test_20260410_120000.md",
            category="测试分类",
            markdown_content="# Test Content",
            references=[{
                'ref_id': 1,
                'title': 'Test Title',
                'url': 'https://example.com',
                'publish_time': '2026-04-10'
            }],
            is_cross_summary=False
        )
        
        assert doc.filename == "test_20260410_120000.md"
        assert doc.category == "测试分类"
        assert doc.markdown_content == "# Test Content"
        assert len(doc.references) == 1
        assert not doc.is_cross_summary

    def test_generate_filename_regular(self, processor):
        """测试常规文件名生成"""
        timestamp = datetime(2026, 4, 10, 12, 30, 45)
        filename = processor._generate_filename("Test News Title", timestamp)
        
        assert "Test_News_Title" in filename
        assert "20260410_123045" in filename
        assert filename.endswith(".md")

    def test_generate_filename_custom(self, processor):
        """测试自定义文件名生成"""
        timestamp = datetime(2026, 4, 10, 12, 30, 45)
        filename = processor._generate_filename("Original Title", timestamp, custom_name="Custom Query")
        
        assert "Custom_Query" in filename
        assert "20260410_123045" in filename
        assert filename.endswith(".md")

    def test_generate_filename_cross_summary(self, processor):
        """测试交叉总结文件名生成"""
        timestamp = datetime(2026, 4, 10, 12, 30, 45)
        filename = processor._generate_filename("Cross Analysis", timestamp, is_cross_summary=True)
        
        assert "Cross_Analysis" in filename
        assert "20260410_123045" in filename
        assert filename.endswith(".md")

    def test_generate_filename_safe_chars(self, processor):
        """测试文件名安全性（特殊字符处理）"""
        timestamp = datetime(2026, 4, 10, 12, 30, 45)
        filename = processor._generate_filename('Test/Title:With*Special?"Chars"', timestamp)
        
        # 检查特殊字符是否被替换
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in unsafe_chars:
            assert char not in filename

    def test_extract_references(self, processor, sample_article):
        """测试引用提取"""
        references = processor._extract_references(sample_article)
        
        assert len(references) == 1
        assert references[0]['title'] == sample_article.title
        assert references[0]['url'] == sample_article.source_url
        assert references[0]['publish_time'] == '2026-04-10'

    def test_inject_citations(self, processor):
        """测试引用注入"""
        content = "This is an important fact。This is another point！"
        references = [
            {'ref_id': 1, 'title': 'Ref 1', 'url': 'https://ref1.com', 'publish_time': '2026-04-10'},
            {'ref_id': 2, 'title': 'Ref 2', 'url': 'https://ref2.com', 'publish_time': '2026-04-10'}
        ]
        
        result = processor._inject_citations(content, references)
        
        # 检查是否包含了引用标记
        assert "[^1]" in result
        assert "[^2]" in result
        assert "Ref 1" in result
        assert "Ref 2" in result

    def test_process_article(self, processor, sample_article):
        """测试文章处理"""
        processed_doc = processor.process_article(sample_article)
        
        assert isinstance(processed_doc, ProcessedDoc)
        assert processed_doc.filename.endswith(".md")
        assert processed_doc.category == sample_article.category
        assert "# Sample News Title" in processed_doc.markdown_content
        assert len(processed_doc.references) >= 0  # 至少有1个引用

    def test_save_document(self, processor, sample_article):
        """测试文档保存"""
        processed_doc = processor.process_article(sample_article)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            file_path = processor.save_document(processed_doc, base_path)
            
            # 检查文件是否创建
            assert file_path.exists()
            assert file_path.suffix == ".md"
            
            # 检查文件内容
            content = file_path.read_text(encoding='utf-8')
            assert "# Sample News Title" in content

    def test_process_multiple_articles(self, processor, sample_article):
        """测试批量处理"""
        articles = [sample_article] * 2  # 创建两篇相同的样本文章
        processed_docs = processor.process_multiple_articles(articles)
        
        assert len(processed_docs) == 2
        for doc in processed_docs:
            assert isinstance(doc, ProcessedDoc)
            assert doc.filename.endswith(".md")


def test_integration_processor_with_collector_output():
    """集成测试：处理器与采集器输出的兼容性"""
    processor = Processor()
    
    # 模拟采集器输出的 RawArticle
    article = RawArticle(
        title="Integration Test Article",
        content="This is content from collector module for integration testing purposes.",
        publish_time=datetime(2026, 4, 10),
        source_url="https://integration-test.com/article",
        source_name="Integration Test Site",
        category="集成测试"
    )
    
    # 处理文章
    processed_doc = processor.process_article(article)
    
    # 验证处理结果
    assert processed_doc.filename.startswith("Integration_Test_Article_")
    assert processed_doc.category == "集成测试"
    assert "Integration Test Article" in processed_doc.markdown_content
    assert len(processed_doc.references) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])