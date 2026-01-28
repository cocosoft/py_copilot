"""
技能元数据解析器模块

负责解析和验证技能元数据，支持多种格式的元数据文件
"""
import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
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
from app.schemas.skill_metadata import SkillMetadata, SkillCategory, SkillStatus, SkillDependency

logger = logging.getLogger(__name__)


class SkillParser:
    """技能元数据解析器类"""
    
    def __init__(self):
        """初始化技能解析器"""
        self.supported_formats = ['.md', '.yaml', '.yml', '.json']
        
    def parse_skill(self, skill_path: str) -> Optional[SkillMetadata]:
        """解析技能目录，提取元数据
        
        Args:
            skill_path: 技能目录路径
            
        Returns:
            技能元数据对象
        """
        skill_dir = Path(skill_path)
        
        # 查找元数据文件
        metadata_file = self._find_metadata_file(skill_dir)
        if not metadata_file:
            logger.warning(f"技能目录 {skill_dir.name} 未找到元数据文件")
            return None
        
        # 解析元数据文件
        metadata = self._parse_metadata_file(metadata_file)
        if not metadata:
            logger.warning(f"解析元数据文件失败: {metadata_file}")
            return None
        
        # 验证和补充元数据
        validated_metadata = self._validate_and_complete_metadata(metadata, skill_dir)
        if not validated_metadata:
            logger.warning(f"元数据验证失败: {skill_dir.name}")
            return None
        
        # 构建技能元数据对象
        skill_metadata = self._build_skill_metadata(validated_metadata, skill_dir)
        
        logger.info(f"成功解析技能: {skill_dir.name}")
        return skill_metadata
    
    def _find_metadata_file(self, skill_dir: Path) -> Optional[Path]:
        """查找技能元数据文件
        
        Args:
            skill_dir: 技能目录路径
            
        Returns:
            元数据文件路径
        """
        # 优先查找SKILL.md文件
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            return skill_md_path
        
        # 查找其他元数据文件
        for ext in self.supported_formats:
            metadata_file = skill_dir / f"skill{ext}"
            if metadata_file.exists():
                return metadata_file
        
        # 查找skill.yaml/skill.yml等
        for filename in ['skill.yaml', 'skill.yml', 'skill.json', 'metadata.yaml', 'metadata.json']:
            metadata_file = skill_dir / filename
            if metadata_file.exists():
                return metadata_file
        
        return None
    
    def _parse_metadata_file(self, metadata_file: Path) -> Optional[Dict[str, Any]]:
        """解析元数据文件
        
        Args:
            metadata_file: 元数据文件路径
            
        Returns:
            解析出的元数据字典
        """
        try:
            if metadata_file.suffix == '.md':
                return self._parse_markdown_metadata(metadata_file)
            elif metadata_file.suffix in ['.yaml', '.yml']:
                return self._parse_yaml_metadata(metadata_file)
            elif metadata_file.suffix == '.json':
                return self._parse_json_metadata(metadata_file)
            else:
                logger.warning(f"不支持的元数据文件格式: {metadata_file}")
                return None
        except Exception as e:
            logger.error(f"解析元数据文件失败 {metadata_file}: {e}")
            return None
    
    def _parse_markdown_metadata(self, metadata_file: Path) -> Optional[Dict[str, Any]]:
        """解析Markdown格式的元数据文件
        
        Args:
            metadata_file: Markdown文件路径
            
        Returns:
            解析出的元数据字典
        """
        with open(metadata_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
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
    
    def _parse_yaml_metadata(self, metadata_file: Path) -> Optional[Dict[str, Any]]:
        """解析YAML格式的元数据文件
        
        Args:
            metadata_file: YAML文件路径
            
        Returns:
            解析出的元数据字典
        """
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = yaml.safe_load(f)
        
        return metadata if isinstance(metadata, dict) else None
    
    def _parse_json_metadata(self, metadata_file: Path) -> Optional[Dict[str, Any]]:
        """解析JSON格式的元数据文件
        
        Args:
            metadata_file: JSON文件路径
            
        Returns:
            解析出的元数据字典
        """
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return metadata if isinstance(metadata, dict) else None
    
    def _validate_and_complete_metadata(self, metadata: Dict[str, Any], skill_dir: Path) -> Optional[Dict[str, Any]]:
        """验证和补充元数据
        
        Args:
            metadata: 原始元数据
            skill_dir: 技能目录路径
            
        Returns:
            验证和补充后的元数据
        """
        # 必需字段检查
        required_fields = ['name', 'description']
        for field in required_fields:
            if field not in metadata:
                logger.warning(f"技能 {skill_dir.name} 缺少必需字段: {field}")
                return None
        
        # 补充默认值
        if 'skill_id' not in metadata:
            metadata['skill_id'] = metadata.get('name', skill_dir.name)
        
        if 'version' not in metadata:
            metadata['version'] = '1.0.0'
        
        if 'author' not in metadata:
            metadata['author'] = 'Unknown'
        
        if 'license' not in metadata:
            metadata['license'] = 'MIT'
        
        # 分类映射
        if 'category' not in metadata:
            metadata['category'] = self._infer_category(metadata['skill_id'])
        
        # 标签处理
        if 'tags' not in metadata:
            metadata['tags'] = []
        elif isinstance(metadata['tags'], str):
            metadata['tags'] = [tag.strip() for tag in metadata['tags'].split(',')]
        
        return metadata
    
    def _infer_category(self, skill_id: str) -> str:
        """根据技能ID推断分类
        
        Args:
            skill_id: 技能ID
            
        Returns:
            分类名称
        """
        category_mapping = {
            'algorithmic-art': 'design',
            'canvas-design': 'design', 
            'frontend-design': 'design',
            'docx': 'document',
            'pdf': 'document',
            'pptx': 'document',
            'doc-coauthoring': 'document',
            'data-analysis': 'data',
            'internal-comms': 'communication',
            'mcp-builder': 'development',
            'brand-guidelines': 'utility'
        }
        
        return category_mapping.get(skill_id, 'utility')
    
    def _build_skill_metadata(self, metadata: Dict[str, Any], skill_dir: Path) -> SkillMetadata:
        """构建技能元数据对象
        
        Args:
            metadata: 验证后的元数据
            skill_dir: 技能目录路径
            
        Returns:
            技能元数据对象
        """
        # 分类枚举转换
        category_mapping = {
            'design': SkillCategory.DESIGN,
            'document': SkillCategory.DOCUMENT,
            'data': SkillCategory.DATA,
            'communication': SkillCategory.COMMUNICATION,
            'development': SkillCategory.DEVELOPMENT,
            'utility': SkillCategory.UTILITY
        }
        
        category = category_mapping.get(metadata['category'], SkillCategory.UTILITY)
        
        # 依赖分析
        dependencies = self._analyze_dependencies(skill_dir)
        
        # 入口点分析
        entry_point = self._analyze_entry_point(skill_dir)
        
        # 构建技能元数据
        skill_metadata = SkillMetadata(
            skill_id=metadata['skill_id'],
            name=metadata['name'],
            description=metadata['description'],
            version=metadata['version'],
            category=category,
            tags=metadata['tags'],
            author=metadata['author'],
            author_email=metadata.get('author_email'),
            license=metadata['license'],
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
    
    def validate_skill_structure(self, skill_path: str) -> Dict[str, Any]:
        """验证技能目录结构
        
        Args:
            skill_path: 技能目录路径
            
        Returns:
            验证结果字典
        """
        skill_dir = Path(skill_path)
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'files_found': []
        }
        
        # 检查元数据文件
        metadata_file = self._find_metadata_file(skill_dir)
        if not metadata_file:
            result['valid'] = False
            result['errors'].append("未找到元数据文件")
        else:
            result['files_found'].append(f"元数据文件: {metadata_file.name}")
        
        # 检查README文件
        readme_files = list(skill_dir.glob("README*"))
        if not readme_files:
            result['warnings'].append("建议添加README文件")
        else:
            result['files_found'].extend([f"README文件: {f.name}" for f in readme_files])
        
        # 检查许可证文件
        license_files = list(skill_dir.glob("LICENSE*"))
        if not license_files:
            result['warnings'].append("建议添加许可证文件")
        else:
            result['files_found'].extend([f"许可证文件: {f.name}" for f in license_files])
        
        # 检查实现文件
        implementation_files = list(skill_dir.rglob("*.py")) + list(skill_dir.rglob("*.js"))
        if not implementation_files:
            result['warnings'].append("未找到实现文件")
        else:
            result['files_found'].extend([f"实现文件: {f.name}" for f in implementation_files[:5]])  # 只显示前5个
        
        return result


def parse_skill_metadata(skill_path: str) -> Optional[SkillMetadata]:
    """解析技能元数据的便捷函数
    
    Args:
        skill_path: 技能目录路径
        
    Returns:
        技能元数据对象
    """
    parser = SkillParser()
    return parser.parse_skill(skill_path)


if __name__ == "__main__":
    # 测试技能解析功能
    import sys
    
    # 添加日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        skill_path = sys.argv[1]
    else:
        # 默认测试路径
        skill_path = "E:\\PY\\CODES\\py copilot IV\\backend\\app\\skills\\skills\\algorithmic-art"
    
    parser = SkillParser()
    
    # 验证技能结构
    validation_result = parser.validate_skill_structure(skill_path)
    print("技能结构验证结果:")
    print(f"有效: {validation_result['valid']}")
    print(f"错误: {validation_result['errors']}")
    print(f"警告: {validation_result['warnings']}")
    print(f"发现文件: {validation_result['files_found']}")
    
    # 解析技能元数据
    skill_metadata = parser.parse_skill(skill_path)
    if skill_metadata:
        print(f"\n解析成功: {skill_metadata.name}")
        print(f"技能ID: {skill_metadata.skill_id}")
        print(f"分类: {skill_metadata.category.value}")
        print(f"描述: {skill_metadata.description[:100]}...")
    else:
        print("\n解析失败")