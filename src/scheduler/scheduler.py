"""调度器模块 - 定时任务和按需检索"""
from datetime import datetime
from typing import List, Dict, Any
import logging
from pathlib import Path
import re

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from src.config.loader import ConfigLoader
from src.collectors.collector import Collector, RawArticle
from src.processors.deduplicator import Deduplicator
from src.processors.processor import Processor
from src.storage.db_manager import DBManager


class IntentParser:
    """意图解析器 - 解析自然语言查询"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 预定义的分类映射
        self.category_keywords = {
            "国际形势": ["国际", "世界", "国外", "外交", "global", "international"],
            "国内政策/国家": ["国家", "中央", "国务院", "全国人大", "国策", "national"],
            "国内政策/广东省": ["广东", "粤", "珠三角", "粤港澳", "guangdong"],
            "国内政策/珠海市": ["珠海", "zhuhai", "珠海南"],
            "国内政策/澳门横琴": ["横琴", "澳门", "mao", "hengqin"],
            "大模型资讯": ["AI", "人工智能", "大模型", "LLM", "ChatGPT", "gpt", "model"],
            "开源社区": ["开源", "GitHub", "git", "开源软件", "repository", "code"],
            "众筹平台": ["众筹", "kickstarter", "indiegogo", "融资", "funding"],
            "智能硬件与机器人资讯": ["硬件", "机器人", "robot", "hardware", "iot", "智能设备"]
        }

    def parse_intent(self, query: str) -> Dict[str, Any]:
        """解析用户查询意图"""
        query_lower = query.lower()
        
        # 尝试识别分类
        detected_category = None
        for category, keywords in self.category_keywords.items():
            if any(keyword.lower() in query_lower for keyword in keywords):
                detected_category = category
                break
        
        # 如果没有检测到分类，默认使用第一个匹配的分类
        if not detected_category:
            detected_category = "大模型资讯"  # 默认分类
        
        # 提取关键词
        keywords = self._extract_keywords(query)
        
        return {
            "category": detected_category,
            "keywords": keywords,
            "original_query": query
        }

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 移除标点符号，保留中文、英文和数字
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
        words = cleaned.split()
        
        # 过滤掉常见的停用词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        keywords = [word for word in words if word not in stopwords and len(word) > 1]
        return keywords[:5]  # 最多返回5个关键词


class Scheduler:
    """调度器 - 管理定时任务和按需检索"""
    
    def __init__(self, config_loader: ConfigLoader, collector: Collector, 
                 deduplicator: Deduplicator, processor: Processor):
        self.config_loader = config_loader
        self.collector = collector
        self.deduplicator = deduplicator
        self.processor = processor
        self.intent_parser = IntentParser()
        
        self.scheduler = BackgroundScheduler()
        self.logger = logging.getLogger(__name__)
        
        # 设置日志级别
        self.scheduler.start()

    def start_daily_schedule(self, hour: int = 9, minute: int = 0):
        """启动每日定时任务，默认 09:00"""
        self.logger.info(f"设置每日 {hour:02d}:{minute:02d} 定时任务")
        
        # 添加每日定时采集任务
        self.scheduler.add_job(
            func=self._daily_collection_task,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_collection',
            name='每日资讯采集任务',
            replace_existing=True
        )
        
        self.logger.info(f"每日定时任务已设置: {hour:02d}:{minute:02d}")
        if hour == 9 and minute == 0:
            self.logger.info("使用默认时间 09:00")

    def stop_daily_schedule(self):
        """停止每日定时任务"""
        self.scheduler.remove_job('daily_collection', jobstore='default')
        self.logger.info("每日定时任务已停止")

    def _daily_collection_task(self):
        """每日采集任务的具体实现"""
        self.logger.info("开始执行每日资讯采集任务")
        
        try:
            # 获取所有启用的资讯源
            sources = self.config_loader.get_enabled_sources()
            self.logger.info(f"发现 {len(sources)} 个启用的资讯源")
            
            # 从所有源采集文章
            raw_articles = self.collector.collect_from_multiple_sources(sources)
            self.logger.info(f"从所有源采集到 {len(raw_articles)} 篇原始文章")
            
            # 去重处理
            unique_articles = self.deduplicator.process_articles(raw_articles)
            self.logger.info(f"去重后剩余 {len(unique_articles)} 篇唯一文章")
            
            # 处理并保存文章
            for article in unique_articles:
                try:
                    processed_doc = self.processor.process_article(article)
                    self.processor.save_document(processed_doc)
                    self.logger.info(f"已处理并保存: {processed_doc.filename}")
                except Exception as e:
                    self.logger.error(f"处理文章 {article.title} 时出错: {str(e)}")
            
            self.logger.info("每日资讯采集任务完成")
            
        except Exception as e:
            self.logger.error(f"每日采集任务执行失败: {str(e)}")

    def on_demand_retrieval(self, query: str) -> List[str]:
        """按需检索 - 根据自然语言查询获取资讯"""
        self.logger.info(f"执行按需检索: {query}")
        
        # 解析用户意图
        intent = self.intent_parser.parse_intent(query)
        category = intent["category"]
        keywords = intent["keywords"]
        
        self.logger.info(f"解析意图 - 分类: {category}, 关键词: {keywords}")
        
        # 获取指定分类的资讯源
        sources = self.config_loader.get_sources_by_category(category)
        if not sources:
            self.logger.warning(f"未找到分类 '{category}' 的资讯源")
            return []
        
        self.logger.info(f"找到 {len(sources)} 个 {category} 类别的资讯源")
        
        # 从指定源采集文章
        raw_articles = self.collector.collect_from_multiple_sources(sources)
        self.logger.info(f"从 {category} 类别源采集到 {len(raw_articles)} 篇原始文章")
        
        # 去重处理
        unique_articles = self.deduplicator.process_articles(raw_articles)
        self.logger.info(f"去重后剩余 {len(unique_articles)} 篇唯一文章")
        
        # 处理并保存文章（使用查询作为自定义名称）
        saved_files = []
        for article in unique_articles:
            try:
                processed_doc = self.processor.process_article(
                    article, 
                    custom_name=query[:30]  # 使用查询的前30个字符作为文件名
                )
                file_path = self.processor.save_document(processed_doc)
                saved_files.append(str(file_path))
                self.logger.info(f"已处理并保存按需检索结果: {processed_doc.filename}")
            except Exception as e:
                self.logger.error(f"处理按需检索文章 {article.title} 时出错: {str(e)}")
        
        self.logger.info(f"按需检索完成，共保存 {len(saved_files)} 个文件")
        return saved_files

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        jobs = self.scheduler.get_jobs()
        job_info = []
        
        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None
            })
        
        return {
            "scheduler_running": self.scheduler.running,
            "jobs_count": len(jobs),
            "jobs": job_info,
            "active_sources_count": len(self.config_loader.get_enabled_sources()),
            "categories_count": len(self.config_loader.get_all_categories())
        }

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        self.logger.info("调度器已关闭")