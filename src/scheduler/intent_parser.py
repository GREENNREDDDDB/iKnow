"""意图解析器模块 - 用于解析用户的自然语言查询"""
from typing import Dict, List, Any
import re


class IntentParser:
    """意图解析器 - 解析自然语言查询"""
    
    def __init__(self):
        # 预定义的分类映射
        self.category_keywords = {
            "国际形势": ["国际", "世界", "国外", "外交", "全球", "环球", "海外", "联合国", "世卫组织", "global", "international", "world"],
            "国内政策/国家": ["国家", "中央", "国务院", "全国人大", "国策", "全国", "中央政府", "国家政策", "national", "country"],
            "国内政策/广东省": ["广东", "粤", "珠三角", "粤港澳", "广府", "南粤", "深圳", "广州", "东莞", "佛山", "guangdong", "GD"],
            "国内政策/珠海市": ["珠海", "珠海南", "横琴新区", "斗门", "金湾", "香洲", "zhuhai", "ZHH"],
            "国内政策/澳门横琴": ["横琴", "澳门", "Macao", "Hengqin", "粤澳合作", "自贸区"],
            "大模型资讯": ["AI", "人工智能", "大模型", "LLM", "ChatGPT", "gpt", "模型", "机器学习", "深度学习", "neural", "transformer"],
            "开源社区": ["开源", "GitHub", "GitLab", "git", "开源软件", "repository", "code", "programming", "development"],
            "众筹平台": ["众筹", "kickstarter", "indiegogo", "融资", "funding", "创业", "项目资金"],
            "智能硬件与机器人资讯": ["硬件", "机器人", "robot", "hardware", "iot", "智能设备", "无人机", "芯片", "sensor", "embedded"]
        }

    def parse_intent(self, query: str) -> Dict[str, Any]:
        """解析用户查询意图"""
        query_lower = query.lower()
        
        # 尝试识别分类
        detected_category = None
        matched_keywords = []
        
        for category, keywords in self.category_keywords.items():
            category_matches = [kw for kw in keywords if kw.lower() in query_lower]
            if category_matches:
                detected_category = category
                matched_keywords.extend(category_matches)
                break  # 找到第一个匹配的分类就停止
        
        # 如果没有检测到分类，使用默认分类
        if not detected_category:
            detected_category = "大模型资讯"  # 默认分类
        
        # 提取关键词
        extracted_keywords = self._extract_keywords(query)
        
        return {
            "category": detected_category,
            "keywords": extracted_keywords,
            "matched_keywords": matched_keywords,
            "original_query": query,
            "confidence": len(matched_keywords) > 0  # 如果匹配到关键词，则置信度高
        }

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 移除标点符号，保留中文、英文和数字
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
        words = cleaned.split()
        
        # 过滤掉常见的停用词
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', 
            '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', 
            '这', '那', '它', '他', '她', '们', '这个', '那个', '这些', '那些', '什么', '怎么',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        }
        
        keywords = [word for word in words if word not in stopwords and len(word) > 1]
        return keywords[:5]  # 最多返回5个关键词

    def get_available_categories(self) -> List[str]:
        """获取所有可用的分类"""
        return list(self.category_keywords.keys())