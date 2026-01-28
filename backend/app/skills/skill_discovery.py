"""
技能发现机制模块

负责扫描技能目录、解析技能元数据、构建技能注册表
"""
import os
import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

# 修复导入路径问题
import sys
from pathlib import Path

# 添加父目录到Python路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# 从app.schemas导入
from app.schemas.skill_metadata import SkillMetadata, SkillDependency

# 定义技能分类枚举（临时修复）
class SkillCategory:
    """技能分类枚举"""
    DESIGN = "design"
    DOCUMENT = "document"
    DATA = "data"
    COMMUNICATION = "communication"
    DEVELOPMENT = "development"
    UTILITY = "utility"

logger = logging.getLogger(__name__)


class SkillDiscovery:
    """技能发现器类"""
    
    def __init__(self, skills_base_path: str = None):
        """初始化技能发现器
        
        Args:
            skills_base_path: 技能基础路径，默认为当前模块所在目录
        """
        if skills_base_path is None:
            self.skills_base_path = Path(__file__).parent / "skills"
        else:
            self.skills_base_path = Path(skills_base_path)
        
        self.skills_registry: Dict[str, SkillMetadata] = {}
        
    def scan_skills_directory(self) -> List[str]:
        """扫描技能目录，返回发现的技能路径列表
        
        Returns:
            技能路径列表
        """
        logger.info(f"开始扫描技能目录: {self.skills_base_path}")
        
        if not self.skills_base_path.exists():
            logger.error(f"技能目录不存在: {self.skills_base_path}")
            return []
        
        skill_dirs = []
        for item in self.skills_base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 检查是否包含SKILL.md文件
                skill_md_path = item / "SKILL.md"
                if skill_md_path.exists():
                    skill_dirs.append(str(item))
                    logger.debug(f"发现技能目录: {item.name}")
        
        logger.info(f"共发现 {len(skill_dirs)} 个技能目录")
        return skill_dirs
    
    def parse_skill_metadata(self, skill_path: str) -> Optional[SkillMetadata]:
        """解析技能元数据
        
        Args:
            skill_path: 技能目录路径
            
        Returns:
            技能元数据对象，解析失败返回None
        """
        skill_dir = Path(skill_path)
        skill_md_path = skill_dir / "SKILL.md"
        
        if not skill_md_path.exists():
            logger.error(f"技能元数据文件不存在: {skill_md_path}")
            return None
        
        try:
            # 读取SKILL.md文件
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析YAML frontmatter
            metadata = self._parse_frontmatter(content)
            if not metadata:
                logger.warning(f"技能 {skill_dir.name} 缺少有效的YAML frontmatter")
                return None
            
            # 构建技能元数据对象
            skill_metadata = self._build_skill_metadata(metadata, skill_dir)
            
            logger.info(f"成功解析技能元数据: {skill_dir.name}")
            return skill_metadata
            
        except Exception as e:
            logger.error(f"解析技能元数据失败 {skill_dir.name}: {e}")
            return None
    
    def _parse_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """解析YAML frontmatter
        
        Args:
            content: 文件内容
            
        Returns:
            解析出的元数据字典
        """
        lines = content.split('\n')
        
        # 检查是否包含YAML frontmatter
        if len(lines) < 2 or lines[0] != '---':
            return None
        
        frontmatter_lines = []
        for line in lines[1:]:
            if line == '---':
                break
            frontmatter_lines.append(line)
        
        if not frontmatter_lines:
            return None
        
        try:
            frontmatter_content = '\n'.join(frontmatter_lines)
            metadata = yaml.safe_load(frontmatter_content)
            return metadata if isinstance(metadata, dict) else None
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误: {e}")
            return None
    
    def _build_skill_metadata(self, metadata: Dict[str, Any], skill_dir: Path) -> SkillMetadata:
        """构建技能元数据对象
        
        Args:
            metadata: 解析出的元数据字典
            skill_dir: 技能目录路径
            
        Returns:
            技能元数据对象
        """
        # 基础信息
        skill_id = metadata.get('name', skill_dir.name)
        name = metadata.get('name', skill_dir.name)
        description = metadata.get('description', '')
        
        # 分类映射
        category_mapping = {
            'algorithmic-art': SkillCategory.DESIGN,
            'canvas-design': SkillCategory.DESIGN,
            'frontend-design': SkillCategory.DESIGN,
            'docx': SkillCategory.DOCUMENT,
            'pdf': SkillCategory.DOCUMENT,
            'pptx': SkillCategory.DOCUMENT,
            'doc-coauthoring': SkillCategory.DOCUMENT,
            'data-analysis': SkillCategory.DATA,
            'internal-comms': SkillCategory.COMMUNICATION,
            'mcp-builder': SkillCategory.DEVELOPMENT,
            'brand-guidelines': SkillCategory.UTILITY
        }
        
        category = category_mapping.get(skill_id, SkillCategory.UTILITY)
        
        # 依赖分析
        dependencies = self._analyze_dependencies(skill_dir)
        
        # 入口点分析
        entry_point = self._analyze_entry_point(skill_dir)
        
        # 构建技能元数据
        skill_metadata = SkillMetadata(
            skill_id=skill_id,
            name=name,
            description=description,
            version=metadata.get('version', '1.0.0'),
            category=category,
            tags=metadata.get('tags', []),
            author=metadata.get('author', 'Unknown'),
            author_email=metadata.get('author_email'),
            license=metadata.get('license', 'MIT'),
            status=SkillStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            entry_point=entry_point,
            dependencies=dependencies,
            usage_count=0,
            avg_rating=0.0
        )
        
        return skill_metadata
    
    def _analyze_dependencies(self, skill_dir: Path) -> List[SkillDependency]:
        """分析技能依赖
        
        Args:
            skill_dir: 技能目录路径
            
        Returns:
            依赖列表
        """
        dependencies = []
        
        # 检查requirements.txt文件
        requirements_path = skill_dir / "requirements.txt"
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 解析依赖项
                            parts = line.split('==')
                            package_name = parts[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else "*"
                            
                            dependency = SkillDependency(
                                package_name=package_name,
                                version=version,
                                required=True,
                                source="pypi"
                            )
                            dependencies.append(dependency)
            except Exception as e:
                logger.warning(f"解析requirements.txt失败 {skill_dir.name}: {e}")
        
        # 检查package.json文件
        package_json_path = skill_dir / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    
                deps = package_data.get('dependencies', {})
                for package_name, version in deps.items():
                    dependency = SkillDependency(
                        package_name=package_name,
                        version=version,
                        required=True,
                        source="npm"
                    )
                    dependencies.append(dependency)
                    
            except Exception as e:
                logger.warning(f"解析package.json失败 {skill_dir.name}: {e}")
        
        return dependencies
    
    def _analyze_entry_point(self, skill_dir: Path) -> str:
        """分析技能入口点
        
        Args:
            skill_dir: 技能目录路径
            
        Returns:
            入口点路径
        """
        # 检查是否有Python模块
        python_files = list(skill_dir.rglob("*.py"))
        if python_files:
            # 查找主要的Python文件
            main_files = [f for f in python_files if f.stem in ['main', 'skill', skill_dir.name]]
            if main_files:
                # 返回相对路径
                relative_path = main_files[0].relative_to(skill_dir)
                return f"app.skills.skills.{skill_dir.name}.{relative_path.stem}"
        
        # 默认返回技能目录名
        return f"app.skills.skills.{skill_dir.name}"
    
    def build_skills_registry(self) -> Dict[str, SkillMetadata]:
        """构建技能注册表
        
        Returns:
            技能注册表字典
        """
        logger.info("开始构建技能注册表")
        
        skill_dirs = self.scan_skills_directory()
        
        for skill_path in skill_dirs:
            skill_metadata = self.parse_skill_metadata(skill_path)
            if skill_metadata:
                self.skills_registry[skill_metadata.skill_id] = skill_metadata
                logger.debug(f"注册技能: {skill_metadata.skill_id}")
        
        logger.info(f"技能注册表构建完成，共注册 {len(self.skills_registry)} 个技能")
        return self.skills_registry
    
    def get_skill(self, skill_id: str) -> Optional[SkillMetadata]:
        """获取指定技能元数据
        
        Args:
            skill_id: 技能ID
            
        Returns:
            技能元数据对象
        """
        return self.skills_registry.get(skill_id)
    
    def get_skills_by_category(self, category: SkillCategory) -> List[SkillMetadata]:
        """按分类获取技能列表
        
        Args:
            category: 技能分类
            
        Returns:
            技能元数据列表
        """
        return [skill for skill in self.skills_registry.values() if skill.category == category]
    
    def refresh_registry(self) -> Dict[str, SkillMetadata]:
        """刷新技能注册表
        
        Returns:
            更新后的技能注册表
        """
        self.skills_registry.clear()
        return self.build_skills_registry()


def discover_all_skills() -> Dict[str, SkillMetadata]:
    """发现所有技能的便捷函数
    
    Returns:
        技能注册表字典
    """
    discovery = SkillDiscovery()
    return discovery.build_skills_registry()


if __name__ == "__main__":
    # 测试技能发现功能
    import sys
    
    # 添加日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    discovery = SkillDiscovery()
    registry = discovery.build_skills_registry()
    
    print(f"发现 {len(registry)} 个技能:")
    for skill_id, skill in registry.items():
        print(f"- {skill_id}: {skill.name} ({skill.category.value})")