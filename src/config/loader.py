"""配置加载与校验模块"""
from pathlib import Path
from typing import List, Dict, Any
import yaml
from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    """资讯源配置"""
    name: str
    category: str
    url: str
    type: str  # 'rss' 或 'web'
    enabled: bool = True


@dataclass
class AppConfig:
    """应用配置"""
    sources: List[SourceConfig] = field(default_factory=list)
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    config_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "config")

    @property
    def db_path(self) -> Path:
        return self.data_dir / "metadata.db"

    @property
    def documents_dir(self) -> Path:
        return self.data_dir / "documents"

    @property
    def graphs_dir(self) -> Path:
        return self.data_dir / "graphs"

    @property
    def sources_yaml_path(self) -> Path:
        return self.config_dir / "sources.yaml"

    @property
    def prompts_dir(self) -> Path:
        return self.config_dir / "prompts"


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: Path | None = None):
        self.config = AppConfig()
        if config_path:
            self.config.sources_yaml_path = config_path
        self._sources: List[SourceConfig] = []

    def load_sources(self) -> List[SourceConfig]:
        """加载资讯源配置"""
        yaml_path = self.config.sources_yaml_path
        if not yaml_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {yaml_path}")

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self._sources = []
        for item in data.get('sources', []):
            source = SourceConfig(
                name=item['name'],
                category=item['category'],
                url=item['url'],
                type=item['type'],
                enabled=item.get('enabled', True)
            )
            self._sources.append(source)

        return self._sources

    def get_enabled_sources(self) -> List[SourceConfig]:
        """获取启用的资讯源"""
        if not self._sources:
            self.load_sources()
        return [s for s in self._sources if s.enabled]

    def get_sources_by_category(self, category: str) -> List[SourceConfig]:
        """按分类获取资讯源"""
        if not self._sources:
            self.load_sources()
        return [s for s in self._sources if s.category == category and s.enabled]

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        if not self._sources:
            self.load_sources()
        return list(set(s.category for s in self._sources if s.enabled))

    def add_source(self, source: SourceConfig) -> None:
        """添加资讯源"""
        if not self._sources:
            self.load_sources()
        self._sources.append(source)
        self._save_sources()

    def remove_source(self, name: str) -> bool:
        """移除资讯源"""
        if not self._sources:
            self.load_sources()
        original_len = len(self._sources)
        self._sources = [s for s in self._sources if s.name != name]
        if len(self._sources) < original_len:
            self._save_sources()
            return True
        return False

    def _save_sources(self) -> None:
        """保存资讯源配置到 YAML"""
        data = {
            'sources': [
                {
                    'name': s.name,
                    'category': s.category,
                    'url': s.url,
                    'type': s.type,
                    'enabled': s.enabled
                }
                for s in self._sources
            ]
        }
        with open(self.config.sources_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
