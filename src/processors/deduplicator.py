"""去重核心逻辑模块"""
import hashlib
import re
from datetime import datetime
from typing import List
import logging

from src.storage.db_manager import DBManager
from src.collectors.collector import RawArticle


class Deduplicator:
    """去重器 - 专门处理去重逻辑"""
    
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    def is_duplicate(self, content: str, publish_time: datetime) -> bool:
        """检查是否为重复内容"""
        return self.db_manager.is_duplicate(content, publish_time)

    def process_articles(self, articles: List[RawArticle]) -> List[RawArticle]:
        """处理文章列表，过滤重复内容"""
        processed_articles = []
        
        for article in articles:
            if self.is_duplicate(article.content, article.publish_time):
                self.logger.info(f"跳过重复文章: {article.title}")
                continue
            
            # 插入数据库记录
            content_hash = self.db_manager.compute_hash(article.content)
            article_id = self.db_manager.insert_article(
                content_hash=content_hash,
                publish_time=article.publish_time,
                category=article.category,
                filename=f"{article.title[:50].replace('/', '_').replace(':', '_')}.md"
            )
            
            processed_articles.append(article)
            self.logger.info(f"处理新文章: {article.title}, ID: {article_id}")
        
        self.logger.info(f"共处理 {len(processed_articles)} 篇新文章，过滤掉 {len(articles) - len(processed_articles)} 篇重复文章")
        return processed_articles