"""Phase 2 测试用例 - 采集引擎 + 严格去重逻辑"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.db_manager import DBManager
from src.config.loader import SourceConfig
from src.collectors.collector import Collector, RawArticle
from src.processors.deduplicator import Deduplicator


class TestCollector:
    """采集器测试"""

    def test_raw_article_model(self):
        """测试 RawArticle 数据模型"""
        article = RawArticle(
            title="Test Title",
            content="Test content",
            publish_time=datetime.now(),
            source_url="https://example.com",
            source_name="Test Source",
            category="测试分类"
        )
        
        assert article.title == "Test Title"
        assert article.content == "Test content"
        assert article.source_url == "https://example.com"
        assert article.source_name == "Test Source"
        assert article.category == "测试分类"

    def test_collector_initialization(self):
        """测试采集器初始化"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        db_manager = DBManager(db_path)
        
        collector = Collector(db_manager)
        assert collector.db_manager == db_manager
        assert collector.session is not None


class TestDeduplicator:
    """去重器测试"""

    @pytest.fixture
    def db_manager(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        return DBManager(db_path)

    @pytest.fixture
    def deduplicator(self, db_manager):
        """创建去重器"""
        return Deduplicator(db_manager)

    def test_is_duplicate_false(self, deduplicator):
        """测试非重复内容"""
        content = "New unique content"
        publish_time = datetime.now()
        assert not deduplicator.is_duplicate(content, publish_time)

    def test_is_duplicate_true(self, deduplicator):
        """测试重复内容"""
        content = "Test content for duplicate check"
        publish_time = datetime(2026, 4, 10)
        
        # 首次插入
        article = RawArticle(
            title="Test Article",
            content=content,
            publish_time=publish_time,
            source_url="https://example.com",
            source_name="Test Source",
            category="测试分类"
        )
        
        # 手动插入到数据库
        content_hash = deduplicator.db_manager.compute_hash(content)
        deduplicator.db_manager.insert_article(content_hash, publish_time, "测试分类")
        
        # 检查重复
        assert deduplicator.is_duplicate(content, publish_time)

    def test_process_articles_no_duplicates(self, deduplicator):
        """测试处理无重复的文章"""
        articles = [
            RawArticle(
                title="Article 1",
                content="Content 1",
                publish_time=datetime(2026, 4, 10),
                source_url="https://example.com/1",
                source_name="Test Source",
                category="测试分类"
            ),
            RawArticle(
                title="Article 2",
                content="Content 2", 
                publish_time=datetime(2026, 4, 10),
                source_url="https://example.com/2",
                source_name="Test Source",
                category="测试分类"
            )
        ]
        
        processed = deduplicator.process_articles(articles)
        assert len(processed) == 2
        assert processed[0].title == "Article 1"
        assert processed[1].title == "Article 2"

    def test_process_articles_with_duplicates(self, deduplicator):
        """测试处理包含重复的文章"""
        # 首先插入一篇重复的文章到数据库
        duplicate_content = "Duplicate content"
        publish_time = datetime(2026, 4, 10)
        content_hash = deduplicator.db_manager.compute_hash(duplicate_content)
        deduplicator.db_manager.insert_article(content_hash, publish_time, "测试分类")
        
        articles = [
            RawArticle(
                title="Original Article",
                content=duplicate_content,  # 这是重复的
                publish_time=publish_time,
                source_url="https://example.com/original",
                source_name="Test Source",
                category="测试分类"
            ),
            RawArticle(
                title="New Article",
                content="New content", 
                publish_time=datetime(2026, 4, 11),
                source_url="https://example.com/new",
                source_name="Test Source", 
                category="测试分类"
            )
        ]
        
        processed = deduplicator.process_articles(articles)
        assert len(processed) == 1  # 只有一篇新文章
        assert processed[0].title == "New Article"

    def test_process_empty_article_list(self, deduplicator):
        """测试处理空文章列表"""
        processed = deduplicator.process_articles([])
        assert len(processed) == 0


def test_integration_collector_deduplicator():
    """集成测试：采集器和去重器协作"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    db_manager = DBManager(db_path)
    
    # 创建采集器和去重器
    collector = Collector(db_manager)
    deduplicator = Deduplicator(db_manager)
    
    # 创建测试文章
    articles = [
        RawArticle(
            title="Integration Test 1",
            content="Integration content 1",
            publish_time=datetime(2026, 4, 10),
            source_url="https://integration-test.com/1",
            source_name="Integration Source",
            category="集成测试"
        )
    ]
    
    # 处理文章
    processed = deduplicator.process_articles(articles)
    assert len(processed) == 1
    
    # 再次尝试处理相同内容，应该被过滤
    duplicate_article = RawArticle(
        title="Integration Test Duplicate",
        content="Integration content 1",  # 相同内容
        publish_time=datetime(2026, 4, 10),  # 相同时间
        source_url="https://integration-test.com/dup",
        source_name="Integration Source",
        category="集成测试"
    )
    
    processed_duplicate = deduplicator.process_articles([duplicate_article])
    assert len(processed_duplicate) == 0  # 应该被过滤掉
    
    # 清理临时文件
    import os
    os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])