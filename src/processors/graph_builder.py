"""关系图谱构建模块 - 构建和渲染资讯实体关系网络"""
import networkx as nx
from pyvis.network import Network
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging
import re


class GraphBuilder:
    """图谱构建器 - 构建和渲染资讯实体关系网络"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _extract_entities(self, content: str) -> List[str]:
        """从内容中提取实体"""
        # 简单的实体提取：提取名词、专有名词等
        # 这里使用简单的正则表达式，实际应用中可以使用 NLP 库
        entities = []
        
        # 提取中文词汇（2个字以上）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        entities.extend(chinese_words)
        
        # 提取英文单词（3个字母以上）
        english_words = re.findall(r'[A-Z][a-z]{2,}', content)
        entities.extend(english_words)
        
        # 提取数字（年份等）
        years = re.findall(r'20\d{2}', content)
        entities.extend(years)
        
        # 去重并返回
        return list(set(entities))[:50]  # 限制实体数量

    def _find_relationships(self, contents: List[str], titles: List[str]) -> List[tuple]:
        """查找实体间的关系"""
        relationships = []
        
        # 为每个文档提取实体
        doc_entities = []
        for i, content in enumerate(contents):
            entities = self._extract_entities(content)
            doc_entities.append({
                'doc_idx': i,
                'title': titles[i] if i < len(titles) else f"文档{i}",
                'entities': entities
            })
        
        # 查找实体间的关系
        for i in range(len(doc_entities)):
            for j in range(i+1, len(doc_entities)):
                doc_i = doc_entities[i]
                doc_j = doc_entities[j]
                
                # 找到共同实体
                common_entities = set(doc_i['entities']) & set(doc_j['entities'])
                
                for entity in common_entities:
                    relationships.append((doc_i['title'], doc_j['title'], entity))
        
        return relationships

    def build_graph(self, contents: List[str], titles: List[str] = None) -> nx.Graph:
        """构建关系图谱"""
        if titles is None:
            titles = [f"文档{i+1}" for i in range(len(contents))]
        
        # 创建图
        G = nx.Graph()
        
        # 添加节点（文档）
        for title in titles:
            G.add_node(title, type='document')
        
        # 查找关系并添加边
        relationships = self._find_relationships(contents, titles)
        
        for source, target, relationship in relationships:
            if G.has_edge(source, target):
                # 如果边已存在，增加权重
                G[source][target]['weight'] += 1
                G[source][target]['relationships'].append(relationship)
            else:
                # 添加新边
                G.add_edge(source, target, weight=1, relationships=[relationship])
        
        self.logger.info(f"构建图谱完成: {len(G.nodes())} 个节点, {len(G.edges())} 条边")
        return G

    def render_graph(self, graph: nx.Graph, output_path: Path, title: str = "资讯关系图谱") -> Path:
        """渲染图谱为 HTML"""
        # 创建 Pyvis 网络
        net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
        
        # 设置选项
        net.set_options("""
        var options = {
          "nodes": {
            "size": 20,
            "font": {
              "size": 14
            }
          },
          "edges": {
            "width": 2,
            "font": {
              "size": 12
            }
          },
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
          }
        }
        """)
        
        # 添加节点
        for node in graph.nodes():
            node_attrs = graph.nodes[node]
            # 根据节点类型设置不同颜色
            color = "#FF9999" if node_attrs.get('type') == 'document' else "#99CCFF"
            net.add_node(node, label=node, color=color, title=node)
        
        # 添加边
        for edge in graph.edges():
            edge_attrs = graph.edges[edge]
            weight = edge_attrs.get('weight', 1)
            relationships = edge_attrs.get('relationships', [])
            
            # 设置边的标签为关系描述
            label = f"{weight} 个共同实体" if relationships else ""
            net.add_edge(edge[0], edge[1], label=label, width=weight)
        
        # 保存为 HTML
        net.save_graph(str(output_path))
        
        self.logger.info(f"图谱已保存: {output_path}")
        return output_path

    def export_graph_data(self, graph: nx.Graph, output_path: Path) -> Path:
        """导出图谱数据为 JSON"""
        graph_data = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "node_count": len(graph.nodes()),
                "edge_count": len(graph.edges())
            }
        }
        
        # 导出节点
        for node in graph.nodes():
            node_attrs = graph.nodes[node]
            graph_data["nodes"].append({
                "id": node,
                "label": node,
                "attributes": node_attrs
            })
        
        # 导出边
        for edge in graph.edges():
            edge_attrs = graph.edges[edge]
            graph_data["edges"].append({
                "source": edge[0],
                "target": edge[1],
                "attributes": edge_attrs
            })
        
        # 保存为 JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"图谱数据已导出: {output_path}")
        return output_path

    def build_and_render_from_documents(self, file_paths: List[Path], output_dir: Path = None) -> Dict[str, Path]:
        """从文档构建并渲染图谱"""
        if output_dir is None:
            output_dir = Path("data/graphs")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 读取文档内容
        contents = []
        titles = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    contents.append(content)
                    titles.append(file_path.stem)
                    self.logger.info(f"已加载文档: {file_path.name}")
            except Exception as e:
                self.logger.error(f"加载文档失败 {file_path}: {str(e)}")
                continue
        
        if not contents:
            raise ValueError("未能加载任何文档内容")
        
        # 构建图谱
        graph = self.build_graph(contents, titles)
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = output_dir / f"graph_{timestamp}.html"
        json_path = output_dir / f"graph_data_{timestamp}.json"
        
        # 渲染图谱
        html_file = self.render_graph(graph, html_path, f"资讯关系图谱_{timestamp}")
        json_file = self.export_graph_data(graph, json_path)
        
        return {
            "html": html_file,
            "json": json_file,
            "graph": graph
        }