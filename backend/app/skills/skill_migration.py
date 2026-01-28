"""
技能迁移工具

负责将现有技能迁移到新的元数据标准，包括元数据标准化、依赖分析、结构验证等
"""
import os
import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 修复导入路径问题
import sys
from pathlib import Path

# 添加父目录到Python路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.skills.skill_parser import SkillParser
from app.schemas.skill_metadata import SkillMetadata, SkillCategory, SkillStatus, SkillDependency

logger = logging.getLogger(__name__)


class SkillMigration:
    """技能迁移器类"""
    
    def __init__(self, skills_base_path: str = None):
        """初始化技能迁移器
        
        Args:
            skills_base_path: 技能基础路径
        """
        if skills_base_path is None:
            self.skills_base_path = Path(__file__).parent / "skills"
        else:
            self.skills_base_path = Path(skills_base_path)
        
        self.parser = SkillParser()
        self.migration_report = {
            'total_skills': 0,
            'migrated_skills': 0,
            'failed_skills': 0,
            'warnings': [],
            'errors': [],
            'details': {}
        }
    
    def migrate_all_skills(self) -> Dict[str, Any]:
        """迁移所有技能
        
        Returns:
            迁移报告
        """
        logger.info("开始技能迁移过程")
        
        # 扫描技能目录
        skill_dirs = self._scan_skill_directories()
        self.migration_report['total_skills'] = len(skill_dirs)
        
        for skill_dir in skill_dirs:
            self._migrate_single_skill(skill_dir)
        
        # 生成总结报告
        self._generate_summary_report()
        
        logger.info(f"技能迁移完成: {self.migration_report['migrated_skills']} 成功, "
                   f"{self.migration_report['failed_skills']} 失败")
        
        return self.migration_report
    
    def _scan_skill_directories(self) -> List[Path]:
        """扫描技能目录
        
        Returns:
            技能目录路径列表
        """
        skill_dirs = []
        
        if not self.skills_base_path.exists():
            logger.error(f"技能目录不存在: {self.skills_base_path}")
            return []
        
        for item in self.skills_base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 检查是否包含SKILL.md文件
                skill_md_path = item / "SKILL.md"
                if skill_md_path.exists():
                    skill_dirs.append(item)
        
        logger.info(f"发现 {len(skill_dirs)} 个技能目录")
        return skill_dirs
    
    def _migrate_single_skill(self, skill_dir: Path):
        """迁移单个技能
        
        Args:
            skill_dir: 技能目录路径
        """
        skill_name = skill_dir.name
        
        try:
            logger.info(f"开始迁移技能: {skill_name}")
            
            # 解析现有技能元数据
            skill_metadata = self.parser.parse_skill(str(skill_dir))
            if not skill_metadata:
                self.migration_report['failed_skills'] += 1
                self.migration_report['errors'].append(f"技能 {skill_name} 元数据解析失败")
                self.migration_report['details'][skill_name] = {
                    'status': 'failed',
                    'error': '元数据解析失败'
                }
                return
            
            # 验证技能结构
            structure_validation = self.parser.validate_skill_structure(str(skill_dir))
            
            # 标准化元数据
            standardized_metadata = self._standardize_metadata(skill_metadata, skill_dir)
            
            # 生成标准化元数据文件
            self._generate_standardized_files(skill_dir, standardized_metadata)
            
            # 记录迁移结果
            self.migration_report['migrated_skills'] += 1
            self.migration_report['details'][skill_name] = {
                'status': 'success',
                'metadata': standardized_metadata.dict(),
                'structure_validation': structure_validation,
                'migration_time': datetime.now().isoformat()
            }
            
            # 记录警告
            if structure_validation['warnings']:
                for warning in structure_validation['warnings']:
                    self.migration_report['warnings'].append(f"{skill_name}: {warning}")
            
            logger.info(f"技能 {skill_name} 迁移成功")
            
        except Exception as e:
            logger.error(f"技能 {skill_name} 迁移失败: {e}")
            self.migration_report['failed_skills'] += 1
            self.migration_report['errors'].append(f"技能 {skill_name} 迁移失败: {str(e)}")
            self.migration_report['details'][skill_name] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def _standardize_metadata(self, skill_metadata: SkillMetadata, skill_dir: Path) -> SkillMetadata:
        """标准化技能元数据
        
        Args:
            skill_metadata: 原始技能元数据
            skill_dir: 技能目录路径
            
        Returns:
            标准化后的技能元数据
        """
        # 确保技能ID格式正确
        skill_id = skill_metadata.skill_id.lower().replace(' ', '-')
        
        # 更新分类信息
        category = self._determine_category(skill_id, skill_metadata.category)
        
        # 标准化标签
        tags = self._standardize_tags(skill_metadata.tags, skill_id, category)
        
        # 更新入口点
        entry_point = self._determine_entry_point(skill_dir, skill_metadata.entry_point)
        
        # 分析依赖关系
        dependencies = self._analyze_dependencies(skill_dir, skill_metadata.dependencies)
        
        # 创建标准化元数据
        standardized_metadata = SkillMetadata(
            skill_id=skill_id,
            name=skill_metadata.name,
            description=skill_metadata.description,
            version=skill_metadata.version,
            category=category,
            tags=tags,
            author=skill_metadata.author,
            author_email=skill_metadata.author_email,
            license=skill_metadata.license,
            status=skill_metadata.status,
            created_at=skill_metadata.created_at,
            updated_at=datetime.now(),
            entry_point=entry_point,
            dependencies=dependencies,
            usage_count=skill_metadata.usage_count,
            avg_rating=skill_metadata.avg_rating
        )
        
        return standardized_metadata
    
    def _determine_category(self, skill_id: str, current_category: SkillCategory) -> SkillCategory:
        """确定技能分类
        
        Args:
            skill_id: 技能ID
            current_category: 当前分类
            
        Returns:
            确定的分类
        """
        # 分类映射表
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
            'brand-guidelines': SkillCategory.UTILITY,
            'skill-creator': SkillCategory.DEVELOPMENT,
            'slack-gif-creator': SkillCategory.COMMUNICATION,
            'theme-factory': SkillCategory.DESIGN,
            'web-artifacts-builder': SkillCategory.DEVELOPMENT,
            'webapp-testing': SkillCategory.DEVELOPMENT,
            'xlsx': SkillCategory.DOCUMENT
        }
        
        return category_mapping.get(skill_id, current_category)
    
    def _standardize_tags(self, current_tags: List[str], skill_id: str, category: SkillCategory) -> List[str]:
        """标准化标签
        
        Args:
            current_tags: 当前标签
            skill_id: 技能ID
            category: 技能分类
            
        Returns:
            标准化后的标签列表
        """
        tags = set(current_tags)
        
        # 添加分类标签
        tags.add(category.value)
        
        # 根据技能ID添加特定标签
        if 'doc' in skill_id:
            tags.add('document-processing')
        if 'design' in skill_id:
            tags.add('creative')
        if 'analysis' in skill_id:
            tags.add('data-processing')
        if 'comms' in skill_id or 'communication' in skill_id:
            tags.add('collaboration')
        
        # 添加通用标签
        tags.add('migrated')
        tags.add('standardized')
        
        return list(tags)
    
    def _determine_entry_point(self, skill_dir: Path, current_entry_point: str) -> str:
        """确定技能入口点
        
        Args:
            skill_dir: 技能目录路径
            current_entry_point: 当前入口点
            
        Returns:
            确定的入口点
        """
        # 检查是否有主要的Python文件
        python_files = list(skill_dir.rglob("*.py"))
        if python_files:
            # 查找主要的Python文件
            main_files = [f for f in python_files if f.stem in ['main', 'skill', skill_dir.name]]
            if main_files:
                # 返回相对路径
                relative_path = main_files[0].relative_to(skill_dir)
                return f"app.skills.skills.{skill_dir.name}.{relative_path.stem}"
        
        # 使用当前入口点或默认值
        return current_entry_point if current_entry_point else f"app.skills.skills.{skill_dir.name}"
    
    def _analyze_dependencies(self, skill_dir: Path, current_dependencies: List[SkillDependency]) -> List[SkillDependency]:
        """分析依赖关系
        
        Args:
            skill_dir: 技能目录路径
            current_dependencies: 当前依赖列表
            
        Returns:
            分析后的依赖列表
        """
        dependencies = list(current_dependencies)
        
        # 检查requirements.txt文件
        requirements_path = skill_dir / "requirements.txt"
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 检查是否已存在该依赖
                            parts = line.split('==')
                            package_name = parts[0].strip()
                            
                            # 如果依赖不存在，则添加
                            if not any(dep.package_name == package_name for dep in dependencies):
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
        
        return dependencies
    
    def _generate_standardized_files(self, skill_dir: Path, skill_metadata: SkillMetadata):
        """生成标准化文件
        
        Args:
            skill_dir: 技能目录路径
            skill_metadata: 标准化后的技能元数据
        """
        # 生成skill.yaml文件（标准化元数据）
        yaml_path = skill_dir / "skill.yaml"
        self._generate_yaml_file(yaml_path, skill_metadata)
        
        # 生成skill.json文件（JSON格式元数据）
        json_path = skill_dir / "skill.json"
        self._generate_json_file(json_path, skill_metadata)
        
        # 更新SKILL.md文件（添加标准化元数据）
        md_path = skill_dir / "SKILL.md"
        self._update_markdown_file(md_path, skill_metadata)
    
    def _generate_yaml_file(self, file_path: Path, skill_metadata: SkillMetadata):
        """生成YAML格式的元数据文件
        
        Args:
            file_path: 文件路径
            skill_metadata: 技能元数据
        """
        metadata_dict = skill_metadata.dict()
        
        # 转换datetime对象为字符串
        for key in ['created_at', 'updated_at']:
            if key in metadata_dict and metadata_dict[key]:
                metadata_dict[key] = metadata_dict[key].isoformat()
        
        # 转换依赖对象为字典
        if 'dependencies' in metadata_dict:
            metadata_dict['dependencies'] = [dep.dict() for dep in metadata_dict['dependencies']]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata_dict, f, allow_unicode=True, indent=2)
    
    def _generate_json_file(self, file_path: Path, skill_metadata: SkillMetadata):
        """生成JSON格式的元数据文件
        
        Args:
            file_path: 文件路径
            skill_metadata: 技能元数据
        """
        metadata_dict = skill_metadata.dict()
        
        # 转换datetime对象为字符串
        for key in ['created_at', 'updated_at']:
            if key in metadata_dict and metadata_dict[key]:
                metadata_dict[key] = metadata_dict[key].isoformat()
        
        # 转换依赖对象为字典
        if 'dependencies' in metadata_dict:
            metadata_dict['dependencies'] = [dep.dict() for dep in metadata_dict['dependencies']]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, ensure_ascii=False, indent=2)
    
    def _update_markdown_file(self, file_path: Path, skill_metadata: SkillMetadata):
        """更新Markdown文件，添加标准化元数据
        
        Args:
            file_path: 文件路径
            skill_metadata: 技能元数据
        """
        if not file_path.exists():
            return
        
        # 读取现有内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有YAML frontmatter
        lines = content.split('\n')
        has_frontmatter = len(lines) >= 2 and lines[0] == '---' and '---' in lines[1:]
        
        if has_frontmatter:
            # 更新现有的frontmatter
            updated_content = self._update_existing_frontmatter(content, skill_metadata)
        else:
            # 添加新的frontmatter
            updated_content = self._add_new_frontmatter(content, skill_metadata)
        
        # 写入更新后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    def _update_existing_frontmatter(self, content: str, skill_metadata: SkillMetadata) -> str:
        """更新现有的YAML frontmatter
        
        Args:
            content: 文件内容
            skill_metadata: 技能元数据
            
        Returns:
            更新后的内容
        """
        lines = content.split('\n')
        
        # 找到frontmatter的结束位置
        end_index = -1
        for i, line in enumerate(lines[1:], 1):
            if line == '---':
                end_index = i
                break
        
        if end_index == -1:
            return content
        
        # 提取frontmatter内容
        frontmatter_lines = lines[1:end_index]
        
        try:
            # 解析现有frontmatter
            existing_metadata = yaml.safe_load('\n'.join(frontmatter_lines))
            
            # 更新关键字段
            if existing_metadata:
                existing_metadata['name'] = skill_metadata.name
                existing_metadata['description'] = skill_metadata.description
                existing_metadata['version'] = skill_metadata.version
                existing_metadata['category'] = skill_metadata.category.value
                existing_metadata['tags'] = skill_metadata.tags
                existing_metadata['author'] = skill_metadata.author
                existing_metadata['license'] = skill_metadata.license
            
            # 生成新的frontmatter
            new_frontmatter = yaml.dump(existing_metadata, allow_unicode=True)
            
            # 构建新的内容
            new_lines = ['---'] + new_frontmatter.split('\n') + ['---'] + lines[end_index+1:]
            return '\n'.join(new_lines)
            
        except yaml.YAMLError:
            return content
    
    def _add_new_frontmatter(self, content: str, skill_metadata: SkillMetadata) -> str:
        """添加新的YAML frontmatter
        
        Args:
            content: 文件内容
            skill_metadata: 技能元数据
            
        Returns:
            添加frontmatter后的内容
        """
        # 构建frontmatter
        frontmatter_data = {
            'name': skill_metadata.name,
            'description': skill_metadata.description,
            'version': skill_metadata.version,
            'category': skill_metadata.category.value,
            'tags': skill_metadata.tags,
            'author': skill_metadata.author,
            'license': skill_metadata.license
        }
        
        frontmatter = yaml.dump(frontmatter_data, allow_unicode=True)
        
        return f"---\n{frontmatter}---\n\n{content}"
    
    def _generate_summary_report(self):
        """生成迁移总结报告"""
        success_rate = (self.migration_report['migrated_skills'] / 
                       self.migration_report['total_skills'] * 100) if self.migration_report['total_skills'] > 0 else 0
        
        self.migration_report['summary'] = {
            'success_rate': round(success_rate, 2),
            'migration_time': datetime.now().isoformat(),
            'total_warnings': len(self.migration_report['warnings']),
            'total_errors': len(self.migration_report['errors'])
        }
    
    def export_migration_report(self, file_path: str):
        """导出迁移报告
        
        Args:
            file_path: 导出文件路径
        """
        # 转换datetime对象为字符串
        def datetime_converter(o):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.migration_report, f, ensure_ascii=False, indent=2, default=datetime_converter)
        
        logger.info(f"迁移报告已导出到: {file_path}")


def migrate_skills() -> Dict[str, Any]:
    """迁移技能的便捷函数
    
    Returns:
        迁移报告
    """
    migration = SkillMigration()
    return migration.migrate_all_skills()


if __name__ == "__main__":
    # 测试技能迁移功能
    import sys
    
    # 添加日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== 技能迁移工具测试 ===")
    
    migration = SkillMigration()
    report = migration.migrate_all_skills()
    
    print(f"迁移总结:")
    print(f"总技能数: {report['total_skills']}")
    print(f"成功迁移: {report['migrated_skills']}")
    print(f"迁移失败: {report['failed_skills']}")
    print(f"成功率: {report['summary']['success_rate']}%")
    
    # 导出报告
    migration.export_migration_report("skill_migration_report.json")
    print("迁移报告已导出到: skill_migration_report.json")