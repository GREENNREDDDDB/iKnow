"""Phase 1 测试用例"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.db_manager import DBManager
from src.config.loader import ConfigLoader, SourceConfig


class TestDBManager:
    """数据库管理器测试"""

    @pytest.fixture
    def db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        return DBManager(db_path)

    def test_init_db(self, db):
        """测试数据库初始化"""
        assert db.db_path.exists()

    def test_normalize_content(self):
        """测试内容清洗"""
        content = "  Hello   World  \n\n  Test  "
        normalized = DBManager.normalize_content(content)
        assert normalized == "Hello World Test"

    def test_normalize_content_html(self):
        """测试 HTML 标签去除"""
        content = "<p>Hello</p>  <b>World</b>"
        normalized = DBManager.normalize_content(content)
        assert normalized == "Hello World"

    def test_compute_hash(self):
        """测试哈希计算"""
        content1 = "Hello World"
        content2 = "Hello World"
        content3 = "Different Content"
        
        hash1 = DBManager.compute_hash(content1)
        hash2 = DBManager.compute_hash(content2)
        hash3 = DBManager.compute_hash(content3)
        
        assert hash1 == hash2
        assert hash1 != hash3

    def test_is_duplicate_false(self, db):
        """测试非重复内容"""
        content = "New unique content"
        publish_time = datetime.now()
        assert not db.is_duplicate(content, publish_time)

    def test_is_duplicate_true(self, db):
        """测试重复内容"""
        content = "Test content for duplicate check"
        publish_time = datetime(2026, 4, 10)
        
        # 首次插入
        content_hash = DBManager.compute_hash(content)
        db.insert_article(content_hash, publish_time, "测试分类")
        
        # 检查重复
        assert db.is_duplicate(content, publish_time)

    def test_insert_article(self, db):
        """测试插入文章"""
        content = "Article content"
        publish_time = datetime(2026, 4, 10)
        content_hash = DBManager.compute_hash(content)
        
        article_id = db.insert_article(content_hash, publish_time, "测试分类", "test_file.md")
        assert article_id > 0

    def test_get_article_by_hash(self, db):
        """测试根据哈希获取文章"""
        content = "Findable article"
        publish_time = datetime(2026, 4, 10)
        content_hash = DBManager.compute_hash(content)
        db.insert_article(content_hash, publish_time, "测试分类", "test.md")
        
        article = db.get_article_by_hash(content_hash)
        assert article is not None
        assert article['category'] == "测试分类"

    def test_get_articles_by_category(self, db):
        """测试按分类获取文章"""
        for i in range(3):
            content = f"Category article {i}"
            publish_time = datetime(2026, 4, 10)
            content_hash = DBManager.compute_hash(content)
            db.insert_article(content_hash, publish_time, "测试分类")
        
        articles = db.get_articles_by_category("测试分类")
        assert len(articles) == 3

    def test_get_article_count(self, db):
        """测试文章计数"""
        assert db.get_article_count() == 0
        
        content = "Count test"
        publish_time = datetime.now()
        content_hash = DBManager.compute_hash(content)
        db.insert_article(content_hash, publish_time, "测试")
        
        assert db.get_article_count() == 1


class TestConfigLoader:
    """配置加载器测试"""

    @pytest.fixture
    def config_loader(self, tmp_path):
        """创建临时配置加载器"""
        # 创建临时 sources.yaml
        yaml_content = """
sources:
  - name: "Test Source 1"
    category: "测试分类"
    url: "https://example.com/rss"
    type: "rss"
    enabled: true
  - name: "Test Source 2"
    category: "测试分类"
    url: "https://example.com/web"
    type: "web"
    enabled: false
"""
        yaml_path = tmp_path / "sources.yaml"
        yaml_path.write_text(yaml_content, encoding='utf-8')
        
        return ConfigLoader(yaml_path)

    def test_load_sources(self, config_loader):
        """测试加载配置"""
        sources = config_loader.load_sources()
        assert len(sources) == 2

    def test_get_enabled_sources(self, config_loader):
        """测试获取启用的源"""
        enabled = config_loader.get_enabled_sources()
        assert len(enabled) == 1
        assert enabled[0].name == "Test Source 1"

    def test_get_sources_by_category(self, config_loader):
        """测试按分类获取源"""
        sources = config_loader.get_sources_by_category("测试分类")
        assert len(sources) == 1  # 只有启用的

    def test_get_all_categories(self, config_loader):
        """测试获取所有分类"""
        categories = config_loader.get_all_categories()
        assert "测试分类" in categories

    def test_add_source(self, config_loader, tmp_path):
        """测试添加源"""
        new_source = SourceConfig(
            name="New Source",
            category="新分类",
            url="https://new.example.com",
            type="rss"
        )
        config_loader.add_source(new_source)
        
        sources = config_loader.get_enabled_sources()
        assert len(sources) == 2
        assert any(s.name == "New Source" for s in sources)

    def test_remove_source(self, config_loader):
        """测试移除源"""
        result = config_loader.remove_source("Test Source 1")
        assert result is True
        
        sources = config_loader.get_enabled_sources()
        assert len(sources) == 0

    def test_remove_nonexistent_source(self, config_loader):
        """测试移除不存在的源"""
        result = config_loader.remove_source("Nonexistent")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
