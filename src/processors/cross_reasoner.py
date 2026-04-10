"""交叉推理引擎模块 - 多文档关系推理"""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging
import json
import re

from src.collectors.collector import RawArticle
from src.processors.processor import Processor, ProcessedDoc


class CrossReasoner:
    """交叉推理引擎 - 对多个文档进行关系推理"""
    
    def __init__(self, processor: Processor):
        self.processor = processor
        self.logger = logging.getLogger(__name__)

    def _load_documents(self, file_paths: List[Path]) -> List[str]:
        """加载文档内容"""
        contents = []
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    contents.append(content)
                    self.logger.info(f"已加载文档: {file_path.name}")
            except Exception as e:
                self.logger.error(f"加载文档失败 {file_path}: {str(e)}")
                continue
        return contents

    def _generate_cross_summary_prompt(self, contents: List[str], topics: List[str] = None) -> str:
        """生成交叉推理提示词"""
        prompt = "请分析以下多个文档之间的关联关系和交叉影响：\n\n"
        
        for i, content in enumerate(contents, 1):
            prompt += f"文档 {i}:\n{content[:1000]}...\n\n"  # 限制每个文档的长度
        
        prompt += "请分析：\n"
        prompt += "1. 这些文档之间的关联关系\n"
        prompt += "2. 可能存在的交叉影响或相互作用\n"
        prompt += "3. 重要的共同主题或趋势\n"
        prompt += "4. 潜在的因果关系或时间序列关系\n"
        prompt += "5. 综合结论和未来展望\n\n"
        
        if topics:
            prompt += f"特别关注以下主题: {', '.join(topics)}\n\n"
        
        prompt += "请以 Markdown 格式输出分析结果，并在适当位置添加引用标记[^n]，最后列出参考文献。"
        
        return prompt

    def _simulate_llm_response(self, prompt: str) -> str:
        """模拟 LLM 响应（实际部署时替换为真实 LLM 调用）"""
        # 这里是模拟实现，实际部署时需要替换为真实的 LLM 调用
        summary = "# 交叉关系分析报告\n\n"
        summary += "## 1. 文档关联关系\n\n"
        summary += "通过分析多个文档，发现以下关联关系：\n\n"
        summary += "- 文档之间存在主题相关性\n"
        summary += "- 部分文档涉及相同事件的不同角度\n"
        summary += "- 时间序列上的前后呼应关系\n\n"
        summary += "## 2. 交叉影响分析\n\n"
        summary += "文档间的交叉影响主要体现在：\n\n"
        summary += "- 政策变化对市场的影响\n"
        summary += "- 技术发展对行业的影响\n"
        summary += "- 国际事件对国内的影响\n\n"
        summary += "## 3. 共同主题与趋势\n\n"
        summary += "识别出的主要共同主题包括：\n\n"
        summary += "- 人工智能技术发展\n"
        summary += "- 政策法规变化\n"
        summary += "- 市场趋势演进\n\n"
        summary += "## 4. 因果关系分析\n\n"
        summary += "潜在的因果关系包括：\n\n"
        summary += "- A事件导致B现象\n"
        summary += "- 政策出台引发市场反应\n\n"
        summary += "## 5. 综合结论\n\n"
        summary += "综合分析表明，各文档反映的趋势相互印证，形成了较为一致的发展脉络。[^1]\n\n"
        summary += "[^1]: 交叉分析结果，基于多个文档的综合推理"
        
        return summary

    def perform_cross_reasoning(self, file_paths: List[Path], 
                              topics: List[str] = None, 
                              custom_title: str = "交叉关系分析") -> ProcessedDoc:
        """执行交叉推理"""
        self.logger.info(f"开始执行交叉推理，文档数量: {len(file_paths)}")
        
        if len(file_paths) < 2:
            raise ValueError("交叉推理至少需要2个文档")
        
        # 加载文档内容
        contents = self._load_documents(file_paths)
        
        if not contents:
            raise ValueError("未能加载任何文档内容")
        
        # 生成提示词
        prompt = self._generate_cross_summary_prompt(contents, topics)
        
        # 获取 LLM 响应
        summary_content = self._simulate_llm_response(prompt)
        
        # 生成交叉推理文档
        timestamp = datetime.now()
        filename = self.processor._generate_filename(
            title=custom_title,
            timestamp=timestamp,
            is_cross_summary=True
        )
        
        # 创建交叉推理文档
        cross_doc = ProcessedDoc(
            filename=filename,
            category="交叉关系总结",  # 固定分类
            markdown_content=summary_content,
            references=[{
                'ref_id': i+1,
                'title': path.name,
                'url': str(path),
                'publish_time': timestamp.strftime('%Y-%m-%d')
            } for i, path in enumerate(file_paths)],
            is_cross_summary=True
        )
        
        self.logger.info(f"交叉推理完成: {filename}")
        return cross_doc

    def batch_cross_reasoning(self, document_groups: List[List[Path]], 
                           titles: List[str] = None) -> List[ProcessedDoc]:
        """批量执行交叉推理"""
        results = []
        
        for i, group in enumerate(document_groups):
            title = titles[i] if titles and i < len(titles) else f"交叉分析组_{i+1}"
            result = self.perform_cross_reasoning(group, custom_title=title)
            results.append(result)
        
        return results