"""LLM 处理器模块 - 生成结构化摘要和引用标记"""
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging
from string import Template

from pydantic import BaseModel, Field
from src.collectors.collector import RawArticle
from src.config.loader import SourceConfig


class ProcessedDoc(BaseModel):
    """处理后的文档模型"""
    filename: str
    category: str
    markdown_content: str  # 含 [^n] 引用
    references: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    is_cross_summary: bool = False


class Processor:
    """处理器 - 将 RawArticle 转换为带引用的 Markdown 文档"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        # 创建提示词模板目录
        prompts_dir = Path("config/prompts")
        prompts_dir.mkdir(exist_ok=True)
        
        # 创建摘要提示词模板
        self._create_prompt_templates()
    
    def _create_prompt_templates(self):
        """创建提示词模板"""
        # 摘要生成提示词
        summarize_template = """请将以下资讯内容整理成结构化摘要：

原文标题: $title
原文内容: $content
来源网址: $source_url
发布时间: $publish_time
资讯分类: $category

要求：
1. 保持原文的核心信息和关键数据
2. 使用 Markdown 格式组织内容，包括标题、列表等
3. 在每个重要观点或数据后添加引用标记，格式为 [^n]
4. 在文档末尾提供完整的引用列表，格式如下：
   [^1]: [来源标题](原始URL) | 发布时间: YYYY-MM-DD
   [^2]: [来源标题](原始URL) | 发布时间: YYYY-MM-DD
5. 确保引用链接可点击
6. 语言简洁明了，突出重点

摘要内容:"""
        
        template_path = Path("config/prompts/summarize.txt")
        if not template_path.exists():
            template_path.write_text(summarize_template, encoding='utf-8')
    
    def _generate_filename(self, title: str, timestamp: datetime, category: str = None, 
                          is_cross_summary: bool = False, custom_name: str = None) -> str:
        """生成符合规范的文件名"""
        # 根据是否为交叉总结使用不同的命名规则
        if is_cross_summary:
            # 交叉关系推理: {交叉资讯内容}_{YYYYMMDD_HHMMSS}.md
            safe_title = re.sub(r'[\/:*?"<>|]', '_', title[:50] if title else "交叉总结")
            filename = f"{safe_title}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        elif custom_name:
            # 自然语言按需: {用户指定内容名}_{YYYYMMDD_HHMMSS}.md
            safe_name = re.sub(r'[\/:*?"<>|]', '_', custom_name[:50])
            filename = f"{safe_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        else:
            # 定时自动采集: {资讯核心主题}_{YYYYMMDD_HHMMSS}.md
            safe_title = re.sub(r'[\/:*?"<>|]', '_', title[:50] if title else "资讯")
            filename = f"{safe_title}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        
        return filename
    
    def _extract_references(self, article: RawArticle) -> List[Dict[str, Any]]:
        """提取引用信息"""
        return [{
            'ref_id': 1,
            'title': article.title,
            'url': article.source_url,
            'publish_time': article.publish_time.strftime('%Y-%m-%d')
        }]
    
    def _inject_citations(self, content: str, references: List[Dict[str, Any]]) -> str:
        """在内容中注入引用标记"""
        # 简单的引用注入策略：在句子结束前添加引用标记
        sentences = re.split(r'([。！？.!?])', content)
        result_parts = []
        ref_counter = 1
        
        for i, part in enumerate(sentences):
            result_parts.append(part)
            # 在句子结束后添加引用标记（跳过一些短的连接词）
            if re.search(r'[。！？.!?]', part) and len(part.strip()) > 2:
                if ref_counter <= len(references):
                    result_parts.append(f"[^{ref_counter}]")
                    ref_counter += 1
        
        content_with_citations = "".join(result_parts)
        
        # 添加引用列表
        if references:
            content_with_citations += "\n\n"
            for ref in references:
                content_with_citations += f"[^{ref['ref_id']}]: [{ref['title']}]({ref['url']}) | 发布时间: {ref['publish_time']}\n"
        
        return content_with_citations
    
    def _generate_summary_with_llm(self, article: RawArticle) -> str:
        """使用 LLM 生成摘要（模拟实现，因为没有真实的 API 调用）"""
        # 这里是模拟实现，实际部署时需要替换为真实的 LLM 调用
        # 为了演示目的，我们直接返回格式化的 Markdown 内容
        
        # 简化处理：直接将内容转换为 Markdown 格式
        content = f"# {article.title}\n\n"
        
        # 将长内容分成段落
        paragraphs = article.content.split('\n')
        for para in paragraphs:
            if para.strip():
                content += f"{para.strip()}\n\n"
        
        return content
    
    def process_article(self, article: RawArticle, custom_name: str = None, 
                       is_cross_summary: bool = False) -> ProcessedDoc:
        """处理单篇文章，生成带引用的 Markdown 文档"""
        try:
            # 生成文件名
            filename = self._generate_filename(
                title=article.title,
                timestamp=datetime.now(),
                category=article.category,
                is_cross_summary=is_cross_summary,
                custom_name=custom_name
            )
            
            # 提取引用
            references = self._extract_references(article)
            
            # 生成摘要内容
            summary_content = self._generate_summary_with_llm(article)
            
            # 注入引用标记
            markdown_content = self._inject_citations(summary_content, references)
            
            # 创建处理后的文档对象
            processed_doc = ProcessedDoc(
                filename=filename,
                category=article.category,
                markdown_content=markdown_content,
                references=references,
                is_cross_summary=is_cross_summary
            )
            
            self.logger.info(f"成功处理文章: {article.title} -> {filename}")
            return processed_doc
            
        except Exception as e:
            self.logger.error(f"处理文章时出错: {str(e)}")
            raise
    
    def save_document(self, processed_doc: ProcessedDoc, base_path: Path = None) -> Path:
        """保存文档到相应分类目录"""
        if base_path is None:
            base_path = Path("data/documents")
        
        # 根据分类确定保存路径
        category_path = base_path / processed_doc.category.replace("/", "\\")
        
        # 如果是交叉总结，特殊处理路径
        if processed_doc.is_cross_summary:
            category_path = base_path / "交叉关系总结"
        
        category_path.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = category_path / processed_doc.filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(processed_doc.markdown_content)
        
        self.logger.info(f"文档已保存: {file_path}")
        return file_path
    
    def process_multiple_articles(self, articles: List[RawArticle], 
                                custom_names: List[str] = None,
                                is_cross_summary: bool = False) -> List[ProcessedDoc]:
        """批量处理多篇文章"""
        processed_docs = []
        
        for i, article in enumerate(articles):
            custom_name = custom_names[i] if custom_names and i < len(custom_names) else None
            doc = self.process_article(article, custom_name, is_cross_summary)
            processed_docs.append(doc)
        
        return processed_docs