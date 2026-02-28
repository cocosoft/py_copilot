"""
技能市场服务

提供主流技能市场的数据获取和管理功能
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SkillMarketplace:
    """技能市场配置"""
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
class MarketplaceSkill:
    """市场技能信息"""
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


# 预定义的主流技能市场
PREDEFINED_MARKETPLACES: Dict[str, SkillMarketplace] = {
    "claude": SkillMarketplace(
        id="claude",
        name="Claude Skills",
        name_zh="Claude技能市场",
        url="https://claudate.com/en/marketplace",
        description="Official Claude skills marketplace with curated AI skills",
        description_zh="Claude官方技能市场，提供精选的AI技能",
        icon="🎯",
        enabled=True,
        supports_search=True,
        supports_install=False,
        categories=["Productivity", "Development", "Writing", "Analysis", "Creative"]
    ),
    "skillsmp": SkillMarketplace(
        id="skillsmp",
        name="Skills MP",
        name_zh="Skills MP市场",
        url="https://skillsmp.com/",
        description="Community-driven skills marketplace for AI assistants",
        description_zh="社区驱动的AI助手技能市场",
        icon="🌟",
        enabled=True,
        supports_search=True,
        supports_install=False,
        categories=["Business", "Education", "Entertainment", "Utilities", "Development"]
    ),
    "skillhub": SkillMarketplace(
        id="skillhub",
        name="SkillHub",
        name_zh="SkillHub技能库",
        url="https://www.skillhub.club/skills",
        description="Comprehensive skill library with community contributions",
        description_zh="综合技能库，包含社区贡献的技能",
        icon="📚",
        enabled=True,
        supports_search=True,
        supports_install=False,
        categories=["Productivity", "Development", "Design", "Marketing", "Research"]
    ),
    "github": SkillMarketplace(
        id="github",
        name="GitHub",
        name_zh="GitHub社区",
        url="https://github.com",
        description="Open source skills from GitHub repositories",
        description_zh="来自GitHub仓库的开源技能",
        icon="🐙",
        enabled=True,
        supports_search=True,
        supports_install=True,
        categories=["Open Source", "Development", "Tools", "Integration"]
    ),
    "local": SkillMarketplace(
        id="local",
        name="Local Skills",
        name_zh="本地技能",
        url="",
        description="Skills installed locally on your system",
        description_zh="安装在您系统上的本地技能",
        icon="💻",
        enabled=True,
        supports_search=True,
        supports_install=True,
        categories=["User Created", "System", "Custom"]
    )
}


# 模拟的技能市场数据（实际应用中应该从API获取）
MARKETPLACE_SKILLS_DATA: Dict[str, List[Dict[str, Any]]] = {
    "claude": [
        {
            "id": "claude-web-search",
            "name": "Web Search Pro",
            "description": "Advanced web search with real-time results and source verification",
            "category": "Productivity",
            "author": "Claude Team",
            "version": "2.1.0",
            "rating": 4.8,
            "downloads": 125000,
            "official": True,
            "popular": True,
            "icon": "🔍",
            "tags": ["search", "web", "research"],
            "last_updated": "2024-01-15"
        },
        {
            "id": "claude-code-assistant",
            "name": "Code Assistant",
            "description": "Intelligent code completion, review, and debugging helper",
            "category": "Development",
            "author": "Claude Team",
            "version": "3.0.2",
            "rating": 4.9,
            "downloads": 98000,
            "official": True,
            "popular": True,
            "icon": "💻",
            "tags": ["coding", "development", "debugging"],
            "last_updated": "2024-01-20"
        },
        {
            "id": "claude-document-analyzer",
            "name": "Document Analyzer",
            "description": "Extract insights from PDFs, Word docs, and text files",
            "category": "Analysis",
            "author": "Claude Team",
            "version": "1.5.0",
            "rating": 4.7,
            "downloads": 76000,
            "official": True,
            "popular": True,
            "icon": "📄",
            "tags": ["documents", "analysis", "pdf"],
            "last_updated": "2024-01-10"
        },
        {
            "id": "claude-writing-coach",
            "name": "Writing Coach",
            "description": "Improve your writing with AI-powered suggestions and editing",
            "category": "Writing",
            "author": "Claude Team",
            "version": "2.0.1",
            "rating": 4.6,
            "downloads": 65000,
            "official": True,
            "popular": False,
            "icon": "✍️",
            "tags": ["writing", "editing", "content"],
            "last_updated": "2024-01-18"
        },
        {
            "id": "claude-data-visualizer",
            "name": "Data Visualizer",
            "description": "Create charts and visualizations from your data",
            "category": "Analysis",
            "author": "Claude Team",
            "version": "1.2.0",
            "rating": 4.5,
            "downloads": 42000,
            "official": True,
            "popular": False,
            "icon": "📊",
            "tags": ["data", "visualization", "charts"],
            "last_updated": "2024-01-12"
        }
    ],
    "skillsmp": [
        {
            "id": "skillsmp-email-manager",
            "name": "Email Manager",
            "description": "Smart email drafting, organization, and response suggestions",
            "category": "Business",
            "author": "SkillsMP Community",
            "version": "1.8.0",
            "rating": 4.4,
            "downloads": 35000,
            "official": False,
            "popular": True,
            "icon": "📧",
            "tags": ["email", "communication", "productivity"],
            "last_updated": "2024-01-14"
        },
        {
            "id": "skillsmp-meeting-summarizer",
            "name": "Meeting Summarizer",
            "description": "Automatically summarize meeting transcripts and action items",
            "category": "Business",
            "author": "SkillsMP Community",
            "version": "2.1.0",
            "rating": 4.6,
            "downloads": 28000,
            "official": False,
            "popular": True,
            "icon": "📝",
            "tags": ["meetings", "summary", "productivity"],
            "last_updated": "2024-01-16"
        },
        {
            "id": "skillsmp-language-tutor",
            "name": "Language Tutor",
            "description": "Learn languages with personalized AI tutoring sessions",
            "category": "Education",
            "author": "SkillsMP Community",
            "version": "1.5.0",
            "rating": 4.7,
            "downloads": 22000,
            "official": False,
            "popular": True,
            "icon": "🌍",
            "tags": ["language", "learning", "education"],
            "last_updated": "2024-01-11"
        },
        {
            "id": "skillsmp-task-automator",
            "name": "Task Automator",
            "description": "Automate repetitive tasks and workflows",
            "category": "Utilities",
            "author": "SkillsMP Community",
            "version": "1.3.0",
            "rating": 4.3,
            "downloads": 18000,
            "official": False,
            "popular": False,
            "icon": "⚡",
            "tags": ["automation", "workflow", "productivity"],
            "last_updated": "2024-01-08"
        }
    ],
    "skillhub": [
        {
            "id": "skillhub-research-assistant",
            "name": "Research Assistant",
            "description": "Comprehensive research helper with citation management",
            "category": "Research",
            "author": "SkillHub Club",
            "version": "2.0.0",
            "rating": 4.8,
            "downloads": 45000,
            "official": False,
            "popular": True,
            "icon": "🔬",
            "tags": ["research", "academic", "citations"],
            "last_updated": "2024-01-19"
        },
        {
            "id": "skillhub-design-critic",
            "name": "Design Critic",
            "description": "Get AI feedback on your designs and UI/UX",
            "category": "Design",
            "author": "SkillHub Club",
            "version": "1.4.0",
            "rating": 4.5,
            "downloads": 32000,
            "official": False,
            "popular": True,
            "icon": "🎨",
            "tags": ["design", "ui", "ux", "feedback"],
            "last_updated": "2024-01-13"
        },
        {
            "id": "skillhub-marketing-strategist",
            "name": "Marketing Strategist",
            "description": "AI-powered marketing strategy and campaign planning",
            "category": "Marketing",
            "author": "SkillHub Club",
            "version": "1.6.0",
            "rating": 4.4,
            "downloads": 26000,
            "official": False,
            "popular": False,
            "icon": "📈",
            "tags": ["marketing", "strategy", "campaign"],
            "last_updated": "2024-01-17"
        },
        {
            "id": "skillhub-content-calendar",
            "name": "Content Calendar",
            "description": "Plan and schedule content across platforms",
            "category": "Marketing",
            "author": "SkillHub Club",
            "version": "1.2.0",
            "rating": 4.2,
            "downloads": 19000,
            "official": False,
            "popular": False,
            "icon": "📅",
            "tags": ["content", "calendar", "scheduling"],
            "last_updated": "2024-01-09"
        }
    ],
    "github": [
        {
            "id": "github-mcp-server",
            "name": "GitHub MCP Server",
            "description": "MCP server for GitHub API integration",
            "category": "Open Source",
            "author": "modelcontextprotocol",
            "version": "1.0.0",
            "rating": 4.9,
            "downloads": 100000,
            "official": True,
            "popular": True,
            "icon": "🐙",
            "tags": ["github", "api", "integration"],
            "last_updated": "2024-01-20"
        },
        {
            "id": "github-file-system",
            "name": "File System MCP",
            "description": "MCP server for local file system operations",
            "category": "Open Source",
            "author": "modelcontextprotocol",
            "version": "1.0.0",
            "rating": 4.7,
            "downloads": 85000,
            "official": True,
            "popular": True,
            "icon": "📁",
            "tags": ["filesystem", "local", "files"],
            "last_updated": "2024-01-18"
        }
    ]
}


class SkillMarketplaceService:
    """技能市场服务类"""

    def __init__(self):
        self.marketplaces = PREDEFINED_MARKETPLACES.copy()
        self.custom_marketplaces: Dict[str, SkillMarketplace] = {}

    def get_all_marketplaces(self) -> List[SkillMarketplace]:
        """获取所有启用的市场"""
        all_marketplaces = {**self.marketplaces, **self.custom_marketplaces}
        return [mp for mp in all_marketplaces.values() if mp.enabled]

    def get_marketplace(self, marketplace_id: str) -> Optional[SkillMarketplace]:
        """获取指定市场"""
        if marketplace_id in self.custom_marketplaces:
            return self.custom_marketplaces[marketplace_id]
        return self.marketplaces.get(marketplace_id)

    def add_custom_marketplace(self, marketplace: SkillMarketplace) -> bool:
        """添加自定义市场"""
        try:
            self.custom_marketplaces[marketplace.id] = marketplace
            logger.info(f"添加自定义技能市场: {marketplace.name}")
            return True
        except Exception as e:
            logger.error(f"添加自定义技能市场失败: {e}")
            return False

    def remove_custom_marketplace(self, marketplace_id: str) -> bool:
        """移除自定义市场"""
        if marketplace_id in self.custom_marketplaces:
            del self.custom_marketplaces[marketplace_id]
            logger.info(f"移除自定义技能市场: {marketplace_id}")
            return True
        return False

    def get_marketplace_skills(
        self,
        marketplace_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[MarketplaceSkill]:
        """获取市场技能列表"""
        skills = []

        # 确定要查询的市场
        if marketplace_id:
            marketplace_ids = [marketplace_id] if marketplace_id in MARKETPLACE_SKILLS_DATA else []
        else:
            marketplace_ids = list(MARKETPLACE_SKILLS_DATA.keys())

        # 从各市场获取技能
        for mp_id in marketplace_ids:
            mp_data = MARKETPLACE_SKILLS_DATA.get(mp_id, [])
            marketplace = self.get_marketplace(mp_id)

            for skill_data in mp_data:
                # 应用分类筛选
                if category and skill_data.get("category") != category:
                    continue

                # 应用搜索筛选
                if search:
                    search_lower = search.lower()
                    if (search_lower not in skill_data.get("name", "").lower() and
                        search_lower not in skill_data.get("description", "").lower()):
                        continue

                skill = MarketplaceSkill(
                    id=skill_data["id"],
                    name=skill_data["name"],
                    description=skill_data["description"],
                    category=skill_data["category"],
                    marketplace=mp_id,
                    marketplace_url=marketplace.url if marketplace else "",
                    author=skill_data["author"],
                    version=skill_data["version"],
                    rating=skill_data.get("rating", 0.0),
                    downloads=skill_data.get("downloads", 0),
                    official=skill_data.get("official", False),
                    popular=skill_data.get("popular", False),
                    icon=skill_data.get("icon"),
                    tags=skill_data.get("tags", []),
                    last_updated=skill_data.get("last_updated")
                )
                skills.append(skill)

        # 按下载量排序
        skills.sort(key=lambda x: x.downloads, reverse=True)
        return skills

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for mp in self.get_all_marketplaces():
            categories.update(mp.categories)
        return sorted(list(categories))


# 全局技能市场服务实例
skill_marketplace_service = SkillMarketplaceService()
