"""
工具市场服务

提供主流工具市场的数据获取和管理功能
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ToolMarketplace:
    """工具市场配置"""
    id: str
    name: str
    name_zh: str
    url: str
    description: str
    description_zh: str
    icon: str
    enabled: bool = True
    api_endpoint: Optional[str] = None
    api_key_required: bool = False
    supports_search: bool = False
    supports_install: bool = False
    categories: List[str] = field(default_factory=list)


@dataclass
class MarketplaceTool:
    """市场工具信息"""
    id: str
    name: str
    description: str
    category: str
    marketplace: str
    marketplace_url: str
    author: str
    version: str
    rating: float = 0.0
    downloads: int = 0
    installed: bool = False
    official: bool = False
    popular: bool = False
    icon: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    tool_type: str = "local"  # local, api, script


# 预定义的主流工具市场
PREDEFINED_MARKETPLACES: Dict[str, ToolMarketplace] = {
    "github": ToolMarketplace(
        id="github",
        name="GitHub",
        name_zh="GitHub社区",
        url="https://github.com",
        description="Open source tools from GitHub repositories",
        description_zh="来自GitHub仓库的开源工具",
        icon="🐙",
        enabled=True,
        supports_search=True,
        supports_install=True,
        categories=["Development", "Productivity", "Data", "Automation", "Integration"]
    ),
    "pypi": ToolMarketplace(
        id="pypi",
        name="PyPI",
        name_zh="Python包索引",
        url="https://pypi.org",
        description="Python packages that can be used as tools",
        description_zh="可用作工具的Python包",
        icon="🐍",
        enabled=True,
        supports_search=True,
        supports_install=True,
        categories=["Python", "Library", "CLI", "API", "Data Processing"]
    ),
    "npm": ToolMarketplace(
        id="npm",
        name="npm",
        name_zh="npm包市场",
        url="https://www.npmjs.com",
        description="Node.js packages and CLI tools",
        description_zh="Node.js包和命令行工具",
        icon="📦",
        enabled=True,
        supports_search=True,
        supports_install=True,
        categories=["Node.js", "CLI", "Web", "Build Tools", "Utilities"]
    ),
    "dockerhub": ToolMarketplace(
        id="dockerhub",
        name="Docker Hub",
        name_zh="Docker Hub",
        url="https://hub.docker.com",
        description="Containerized tools and applications",
        description_zh="容器化工具和应用",
        icon="🐳",
        enabled=True,
        supports_search=True,
        supports_install=True,
        categories=["Container", "DevOps", "Database", "Web Server", "Monitoring"]
    ),
    "local": ToolMarketplace(
        id="local",
        name="Local Tools",
        name_zh="本地工具",
        url="",
        description="Tools installed locally on your system",
        description_zh="安装在您系统上的本地工具",
        icon="💻",
        enabled=True,
        supports_search=True,
        supports_install=True,
        categories=["User Created", "System", "Custom"]
    )
}


# 模拟的工具市场数据
MARKETPLACE_TOOLS_DATA: Dict[str, List[Dict[str, Any]]] = {
    "github": [
        {
            "id": "github-httpie",
            "name": "HTTPie",
            "description": "Modern command line HTTP client",
            "category": "Development",
            "author": "jakubroztocil",
            "version": "3.2.0",
            "rating": 4.8,
            "downloads": 500000,
            "official": True,
            "popular": True,
            "icon": "🌐",
            "tags": ["http", "api", "cli"],
            "last_updated": "2024-01-15",
            "tool_type": "cli"
        },
        {
            "id": "github-ripgrep",
            "name": "ripgrep",
            "description": "Fast line-oriented search tool",
            "category": "Development",
            "author": "BurntSushi",
            "version": "14.0.0",
            "rating": 4.9,
            "downloads": 800000,
            "official": True,
            "popular": True,
            "icon": "🔍",
            "tags": ["search", "grep", "cli"],
            "last_updated": "2024-01-20",
            "tool_type": "cli"
        },
        {
            "id": "github-fd",
            "name": "fd",
            "description": "Simple, fast and user-friendly alternative to find",
            "category": "Productivity",
            "author": "sharkdp",
            "version": "9.0.0",
            "rating": 4.7,
            "downloads": 300000,
            "official": True,
            "popular": True,
            "icon": "📁",
            "tags": ["find", "search", "filesystem"],
            "last_updated": "2024-01-10",
            "tool_type": "cli"
        },
        {
            "id": "github-exa",
            "name": "eza",
            "description": "Modern replacement for ls with icons and colors",
            "category": "Productivity",
            "author": "eza-community",
            "version": "0.17.0",
            "rating": 4.6,
            "downloads": 200000,
            "official": True,
            "popular": False,
            "icon": "📂",
            "tags": ["ls", "filesystem", "cli"],
            "last_updated": "2024-01-12",
            "tool_type": "cli"
        }
    ],
    "pypi": [
        {
            "id": "pypi-requests",
            "name": "requests",
            "description": "Python HTTP library for humans",
            "category": "Development",
            "author": "psf",
            "version": "2.31.0",
            "rating": 4.9,
            "downloads": 10000000,
            "official": True,
            "popular": True,
            "icon": "🌐",
            "tags": ["http", "api", "network"],
            "last_updated": "2024-01-18",
            "tool_type": "library"
        },
        {
            "id": "pypi-pandas",
            "name": "pandas",
            "description": "Data analysis and manipulation library",
            "category": "Data Processing",
            "author": "pandas-dev",
            "version": "2.1.0",
            "rating": 4.8,
            "downloads": 15000000,
            "official": True,
            "popular": True,
            "icon": "📊",
            "tags": ["data", "analysis", "dataframe"],
            "last_updated": "2024-01-22",
            "tool_type": "library"
        },
        {
            "id": "pypi-rich",
            "name": "rich",
            "description": "Rich text and beautiful formatting in the terminal",
            "category": "Development",
            "author": "willmcgugan",
            "version": "13.7.0",
            "rating": 4.7,
            "downloads": 5000000,
            "official": True,
            "popular": True,
            "icon": "🎨",
            "tags": ["terminal", "formatting", "cli"],
            "last_updated": "2024-01-16",
            "tool_type": "library"
        },
        {
            "id": "pypi-typer",
            "name": "typer",
            "description": "Build great CLIs with Python type hints",
            "category": "CLI",
            "author": "tiangolo",
            "version": "0.9.0",
            "rating": 4.6,
            "downloads": 2000000,
            "official": True,
            "popular": False,
            "icon": "⌨️",
            "tags": ["cli", "argparse", "typing"],
            "last_updated": "2024-01-14",
            "tool_type": "library"
        }
    ],
    "npm": [
        {
            "id": "npm-prettier",
            "name": "prettier",
            "description": "Opinionated code formatter",
            "category": "Build Tools",
            "author": "prettier",
            "version": "3.2.0",
            "rating": 4.8,
            "downloads": 20000000,
            "official": True,
            "popular": True,
            "icon": "✨",
            "tags": ["formatter", "code", "javascript"],
            "last_updated": "2024-01-19",
            "tool_type": "cli"
        },
        {
            "id": "npm-eslint",
            "name": "eslint",
            "description": "Pluggable JavaScript linter",
            "category": "Build Tools",
            "author": "eslint",
            "version": "8.56.0",
            "rating": 4.7,
            "downloads": 25000000,
            "official": True,
            "popular": True,
            "icon": "🔍",
            "tags": ["linter", "javascript", "code-quality"],
            "last_updated": "2024-01-21",
            "tool_type": "cli"
        },
        {
            "id": "npm-http-server",
            "name": "http-server",
            "description": "Simple zero-configuration command-line http server",
            "category": "Web",
            "author": "http-party",
            "version": "14.1.0",
            "rating": 4.5,
            "downloads": 8000000,
            "official": True,
            "popular": True,
            "icon": "🌐",
            "tags": ["server", "http", "static"],
            "last_updated": "2024-01-11",
            "tool_type": "cli"
        }
    ],
    "dockerhub": [
        {
            "id": "docker-nginx",
            "name": "nginx",
            "description": "Official Nginx web server image",
            "category": "Web Server",
            "author": "nginx",
            "version": "1.25.0",
            "rating": 4.9,
            "downloads": 1000000000,
            "official": True,
            "popular": True,
            "icon": "🌐",
            "tags": ["web-server", "proxy", "http"],
            "last_updated": "2024-01-20",
            "tool_type": "container"
        },
        {
            "id": "docker-postgres",
            "name": "postgres",
            "description": "Official PostgreSQL database image",
            "category": "Database",
            "author": "postgres",
            "version": "16.1",
            "rating": 4.8,
            "downloads": 500000000,
            "official": True,
            "popular": True,
            "icon": "🐘",
            "tags": ["database", "sql", "postgresql"],
            "last_updated": "2024-01-18",
            "tool_type": "container"
        },
        {
            "id": "docker-redis",
            "name": "redis",
            "description": "Official Redis in-memory data store",
            "category": "Database",
            "author": "redis",
            "version": "7.2.0",
            "rating": 4.7,
            "downloads": 400000000,
            "official": True,
            "popular": True,
            "icon": "🔴",
            "tags": ["cache", "database", "nosql"],
            "last_updated": "2024-01-15",
            "tool_type": "container"
        }
    ]
}


class ToolMarketplaceService:
    """工具市场服务类"""

    def __init__(self):
        self.marketplaces = PREDEFINED_MARKETPLACES.copy()
        self.custom_marketplaces: Dict[str, ToolMarketplace] = {}

    def get_all_marketplaces(self) -> List[ToolMarketplace]:
        """获取所有启用的市场"""
        all_marketplaces = {**self.marketplaces, **self.custom_marketplaces}
        return [mp for mp in all_marketplaces.values() if mp.enabled]

    def get_marketplace(self, marketplace_id: str) -> Optional[ToolMarketplace]:
        """获取指定市场"""
        if marketplace_id in self.custom_marketplaces:
            return self.custom_marketplaces[marketplace_id]
        return self.marketplaces.get(marketplace_id)

    def add_custom_marketplace(self, marketplace: ToolMarketplace) -> bool:
        """添加自定义市场"""
        try:
            self.custom_marketplaces[marketplace.id] = marketplace
            logger.info(f"添加自定义工具市场: {marketplace.name}")
            return True
        except Exception as e:
            logger.error(f"添加自定义工具市场失败: {e}")
            return False

    def remove_custom_marketplace(self, marketplace_id: str) -> bool:
        """移除自定义市场"""
        if marketplace_id in self.custom_marketplaces:
            del self.custom_marketplaces[marketplace_id]
            logger.info(f"移除自定义工具市场: {marketplace_id}")
            return True
        return False

    def get_marketplace_tools(
        self,
        marketplace_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[MarketplaceTool]:
        """获取市场工具列表"""
        tools = []

        # 确定要查询的市场
        if marketplace_id:
            marketplace_ids = [marketplace_id] if marketplace_id in MARKETPLACE_TOOLS_DATA else []
        else:
            marketplace_ids = list(MARKETPLACE_TOOLS_DATA.keys())

        # 从各市场获取工具
        for mp_id in marketplace_ids:
            mp_data = MARKETPLACE_TOOLS_DATA.get(mp_id, [])
            marketplace = self.get_marketplace(mp_id)

            for tool_data in mp_data:
                # 应用分类筛选
                if category and tool_data.get("category") != category:
                    continue

                # 应用搜索筛选
                if search:
                    search_lower = search.lower()
                    if (search_lower not in tool_data.get("name", "").lower() and
                        search_lower not in tool_data.get("description", "").lower()):
                        continue

                tool = MarketplaceTool(
                    id=tool_data["id"],
                    name=tool_data["name"],
                    description=tool_data["description"],
                    category=tool_data["category"],
                    marketplace=mp_id,
                    marketplace_url=marketplace.url if marketplace else "",
                    author=tool_data["author"],
                    version=tool_data["version"],
                    rating=tool_data.get("rating", 0.0),
                    downloads=tool_data.get("downloads", 0),
                    official=tool_data.get("official", False),
                    popular=tool_data.get("popular", False),
                    icon=tool_data.get("icon"),
                    tags=tool_data.get("tags", []),
                    last_updated=tool_data.get("last_updated"),
                    tool_type=tool_data.get("tool_type", "local")
                )
                tools.append(tool)

        # 按下载量排序
        tools.sort(key=lambda x: x.downloads, reverse=True)
        return tools

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for mp in self.get_all_marketplaces():
            categories.update(mp.categories)
        return sorted(list(categories))


# 全局工具市场服务实例
tool_marketplace_service = ToolMarketplaceService()
