"""Phase 4 测试用例 - 调度器 + 自然语言按需检索"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import sys
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.loader import ConfigLoader
from src.collectors.collector import Collector, RawArticle
from src.processors.deduplicator import Deduplicator
from src.processors.processor import Processor
from src.storage.db_manager import DBManager
from src.scheduler.intent_parser import IntentParser
from src.scheduler.scheduler import Scheduler


class TestIntentParser:
    """意图解析器测试"""

    @pytest.fixture
    def intent_parser(self):
        """创建意图解析器实例"""
        return IntentParser()

    def test_parse_intent_international(self, intent_parser):
        """测试国际形势意图解析"""
        query = "帮我找一下最新的国际形势分析"
        result = intent_parser.parse_intent(query)
        
        assert result["category"] == "国际形势"
        assert "国际" in result["matched_keywords"]
        assert "形势" in result["keywords"]

    def test_parse_intent_domestic_policy(self, intent_parser):
        """测试国内政策意图解析"""
        query = "国家最近有什么新的政策发布吗"
        result = intent_parser.parse_intent(query)
        
        assert result["category"] == "国内政策/国家"
        assert "国家" in result["matched_keywords"]
        assert "政策" in result["keywords"]

    def test_parse_intent_guangdong(self, intent_parser):
        """测试广东政策意图解析"""
        query = "广东最近有什么新政策"
        result = intent_parser.parse_intent(query)
        
        assert result["category"] == "国内政策/广东省"
        assert "广东" in result["matched_keywords"]

    def test_parse_intent_default(self, intent_parser):
        """测试默认分类意图解析"""
        query = "随便找些有趣的信息"
        result = intent_parser.parse_intent(query)
        
        assert result["category"] == "大模型资讯"  # 默认分类
        assert not result["matched_keywords"]  # 没有匹配特定关键词

    def test_extract_keywords(self, intent_parser):
        """测试关键词提取"""
        query = "关于人工智能和机器学习的最新进展"
        result = intent_parser.parse_intent(query)
        
        assert "人工智能" in result["keywords"] or "AI" in result["keywords"]
        assert "机器学习" in result["keywords"] or "learning" in result["keywords"]

    def test_get_available_categories(self, intent_parser):
        """测试获取可用分类"""
        categories = intent_parser.get_available_categories()
        
        assert "国际形势" in categories
        assert "国内政策/国家" in categories
        assert "大模型资讯" in categories
        assert len(categories) > 0


class TestScheduler:
    """调度器测试"""

    @pytest.fixture
    def setup_scheduler(self):
        """设置调度器测试环境"""
        # 创建临时数据库
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        db_manager = DBManager(db_path)
        config_loader = ConfigLoader(Path("config/sources.yaml"))
        
        # 创建必要的组件
        collector = Collector(db_manager)
        deduplicator = Deduplicator(db_manager)
        processor = Processor()
        
        scheduler = Scheduler(config_loader, collector, deduplicator, processor)
        
        yield scheduler, db_manager, config_loader
        
        # 清理
        import os
        os.unlink(db_path)

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        # 创建临时数据库
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        db_manager = DBManager(db_path)
        config_loader = ConfigLoader(Path("config/sources.yaml"))
        
        collector = Collector(db_manager)
        deduplicator = Deduplicator(db_manager)
        processor = Processor()
        
        scheduler = Scheduler(config_loader, collector, deduplicator, processor)
        
        assert scheduler.config_loader == config_loader
        assert scheduler.collector == collector
        assert scheduler.deduplicator == deduplicator
        assert scheduler.processor == processor
        assert scheduler.scheduler is not None
        
        # 清理
        import os
        os.unlink(db_path)

    def test_get_status(self, setup_scheduler):
        """测试获取调度器状态"""
        scheduler, _, _ = setup_scheduler
        
        status = scheduler.get_status()
        
        assert "scheduler_running" in status
        assert "jobs_count" in status
        assert "jobs" in status
        assert isinstance(status["jobs_count"], int)

    def test_start_daily_schedule(self, setup_scheduler):
        """测试启动每日定时任务"""
        scheduler, _, _ = setup_scheduler
        
        # 启动每日定时任务
        scheduler.start_daily_schedule(hour=9, minute=0)
        
        # 检查是否有任务被添加
        status = scheduler.get_status()
        assert status["jobs_count"] >= 1  # 可能已经有其他任务
        
        # 检查是否存在 daily_collection 任务
        job_exists = any(job["id"] == "daily_collection" for job in status["jobs"])
        assert job_exists

    def test_on_demand_retrieval_basic(self, setup_scheduler):
        """测试基本的按需检索功能"""
        scheduler, _, config_loader = setup_scheduler
        
        # 确保有可用的源
        sources = config_loader.get_enabled_sources()
        if not sources:
            # 如果没有配置源，创建一个测试源
            from src.config.loader import SourceConfig
            test_source = SourceConfig(
                name="Test Source",
                category="大模型资讯",
                url="https://example.com",
                type="web"
            )
            config_loader.add_source(test_source)
        
        # 执行按需检索
        results = scheduler.on_demand_retrieval("最新的AI技术进展")
        
        # 结果可能是空的（如果没有实际的网络源），但我们至少要确保没有抛出异常
        assert isinstance(results, list)

    def test_intent_parser_integration(self, setup_scheduler):
        """测试意图解析器集成"""
        scheduler, _, _ = setup_scheduler
        
        # 测试调度器内部的意图解析
        intent = scheduler.intent_parser.parse_intent("国际形势如何")
        
        assert intent["category"] == "国际形势"
        assert "国际" in intent["matched_keywords"]


def test_integration_scheduler_with_all_components():
    """集成测试：调度器与所有组件的兼容性"""
    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    try:
        db_manager = DBManager(db_path)
        config_loader = ConfigLoader(Path("config/sources.yaml"))
        
        # 创建所有必需的组件
        collector = Collector(db_manager)
        deduplicator = Deduplicator(db_manager)
        processor = Processor()
        
        # 创建调度器
        scheduler = Scheduler(config_loader, collector, deduplicator, processor)
        
        # 测试调度器状态
        status = scheduler.get_status()
        assert "scheduler_running" in status
        
        # 测试意图解析
        intent_result = scheduler.intent_parser.parse_intent("帮我找最新的大模型资讯")
        assert intent_result["category"] == "大模型资讯"
        
        # 关闭调度器
        scheduler.shutdown()
        
    finally:
        # 清理临时数据库
        import os
        os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])