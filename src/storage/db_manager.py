"""SQLite 数据库管理模块"""
import sqlite3
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
from contextlib import contextmanager


class DBManager:
    """数据库管理器"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表结构"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT NOT NULL,
                    publish_time TEXT NOT NULL,
                    category TEXT NOT NULL,
                    filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(content_hash, publish_time)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash_time 
                ON articles(content_hash, publish_time)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    url TEXT NOT NULL,
                    type TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    @staticmethod
    def normalize_content(content: str) -> str:
        """清洗内容用于去重"""
        # 去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', content)
        # 去除首尾空白
        text = text.strip()
        # 去除连续空格和换行
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def compute_hash(content: str) -> str:
        """计算内容的 MD5 哈希值"""
        normalized = DBManager.normalize_content(content)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def normalize_time(publish_time: datetime) -> str:
        """标准化发布时间到 ISO 8601 格式"""
        return publish_time.strftime('%Y-%m-%d')

    def is_duplicate(self, content: str, publish_time: datetime) -> bool:
        """检查是否为重复内容"""
        content_hash = self.compute_hash(content)
        time_str = self.normalize_time(publish_time)
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM articles WHERE content_hash = ? AND publish_time = ?",
                (content_hash, time_str)
            )
            return cursor.fetchone() is not None

    def insert_article(self, content_hash: str, publish_time: datetime, 
                      category: str, filename: Optional[str] = None) -> int:
        """插入新文章记录"""
        time_str = self.normalize_time(publish_time)
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO articles (content_hash, publish_time, category, filename)
                   VALUES (?, ?, ?, ?)""",
                (content_hash, time_str, category, filename)
            )
            return cursor.lastrowid

    def get_article_by_hash(self, content_hash: str) -> Optional[dict]:
        """根据哈希值获取文章"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM articles WHERE content_hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_articles_by_category(self, category: str, limit: int = 100) -> List[dict]:
        """按分类获取文章列表"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM articles WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                (category, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_articles(self, limit: int = 1000) -> List[dict]:
        """获取所有文章"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM articles ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_article_count(self) -> int:
        """获取文章总数"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM articles")
            return cursor.fetchone()['count']

    def get_category_stats(self) -> List[dict]:
        """获取各分类的文章统计"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT category, COUNT(*) as count 
                   FROM articles 
                   GROUP BY category 
                   ORDER BY count DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]
