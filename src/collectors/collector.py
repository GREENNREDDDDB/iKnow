"""采集引擎模块 - RSS 和网页采集器"""
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import List, Optional
import time
import logging
from pathlib import Path

from src.config.loader import SourceConfig
from src.storage.db_manager import DBManager
from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    """原始文章数据模型"""
    title: str
    content: str
    publish_time: datetime
    source_url: str
    source_name: str
    category: str
    summary: Optional[str] = None  # 可选摘要


class Collector:
    """采集器基类"""
    
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)

    def collect_from_source(self, source: SourceConfig) -> List[RawArticle]:
        """从单个源采集数据"""
        if source.type.lower() == 'rss':
            return self._collect_from_rss(source)
        elif source.type.lower() == 'web':
            return self._collect_from_web(source)
        else:
            self.logger.warning(f"未知的源类型: {source.type}")
            return []

    def _collect_from_rss(self, source: SourceConfig) -> List[RawArticle]:
        """从 RSS 源采集"""
        try:
            response = self.session.get(source.url, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries:
                # 解析发布时间
                publish_time = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    publish_time = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    publish_time = datetime(*entry.updated_parsed[:6])
                
                # 获取内容
                content = entry.summary if hasattr(entry, 'summary') else ''
                if hasattr(entry, 'content') and entry.content:
                    content = entry.content[0].value if isinstance(entry.content, list) else str(entry.content)
                
                # 检查是否重复
                if self.db_manager.is_duplicate(content, publish_time):
                    self.logger.info(f"发现重复内容，跳过: {entry.title}")
                    continue
                
                article = RawArticle(
                    title=getattr(entry, 'title', 'Untitled'),
                    content=content,
                    publish_time=publish_time,
                    source_url=getattr(entry, 'link', source.url),
                    source_name=source.name,
                    category=source.category
                )
                articles.append(article)
                
            self.logger.info(f"从 {source.name} 采集到 {len(articles)} 篇新文章")
            return articles
            
        except Exception as e:
            self.logger.error(f"采集 RSS 源 {source.name} 时出错: {str(e)}")
            return []

    def _collect_from_web(self, source: SourceConfig) -> List[RawArticle]:
        """从网页采集"""
        try:
            response = self.session.get(source.url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试提取页面内容 - 这里使用通用方法，实际项目中可能需要针对特定网站定制
            title_tag = soup.find(['title', 'h1'])
            title = title_tag.get_text().strip() if title_tag else 'Untitled'
            
            # 尝试找到主要内容区域
            content_selectors = [
                'article', '.content', '#content', '.post-content', 
                '.entry-content', 'main', '.main-content'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                # 如果没找到特定内容区域，使用 body
                content_element = soup.find('body')
            
            content = content_element.get_text().strip() if content_element else soup.get_text().strip()
            
            # 限制内容长度以避免过大的文本
            if len(content) > 10000:
                content = content[:10000] + "... [内容截断]"
            
            publish_time = datetime.now()  # 网页通常没有明确的发布时间，使用采集时间
            
            # 检查是否重复
            if self.db_manager.is_duplicate(content, publish_time):
                self.logger.info(f"发现重复内容，跳过: {title}")
                return []
            
            article = RawArticle(
                title=title,
                content=content,
                publish_time=publish_time,
                source_url=source.url,
                source_name=source.name,
                category=source.category
            )
            
            self.logger.info(f"从 {source.name} 采集到 1 篇新文章")
            return [article]
            
        except Exception as e:
            self.logger.error(f"采集网页源 {source.name} 时出错: {str(e)}")
            return []

    def collect_from_multiple_sources(self, sources: List[SourceConfig]) -> List[RawArticle]:
        """从多个源采集数据"""
        all_articles = []
        
        for source in sources:
            if not source.enabled:
                continue
                
            self.logger.info(f"开始采集源: {source.name}")
            articles = self.collect_from_source(source)
            all_articles.extend(articles)
            
            # 避免请求过于频繁
            time.sleep(1)
        
        return all_articles


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