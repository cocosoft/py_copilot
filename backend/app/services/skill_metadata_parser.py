"""
技能元数据解析器

负责解析技能文件的元数据，验证完整性，并生成标准化的技能元数据对象。
支持多种文件格式（SKILL.md、skill.yaml、skill.json）的解析。
"""

import os
import re
import yaml
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
import hashlib

from app.core.logging_config import logger
from app.schemas.skill_metadata import SkillMetadata, SkillCategory


class SkillMetadataParser:
    """技能元数据解析器"""
    
    # 必填字段
    REQUIRED_FIELDS = [
        "name",
        "description", 
        "version",
        "author",
    ]
    
    # 字段验证器
    FIELD_VALIDATORS = {
        "name": lambda x: isinstance(x, str) and len(x.strip()) > 0 and len(x) <= 100,
        "description": lambda x: isinstance(x, str) and len(x.strip()) > 0 and len(x) <= 500,
        "version": lambda x: isinstance(x, str) and re.match(r'^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9.]+)?$', x),
        "author": lambda x: isinstance(x, str) and len(x.strip()) > 0 and len(x) <= 100,
        "category": lambda x: x in [cat.value for cat in SkillCategory],
        "tags": lambda x: isinstance(x, list) and all(isinstance(t, str) for t in x) and len(x) <= 20,
        "dependencies": lambda x: isinstance(x, list) and all(isinstance(d, str) for d in x),
        "enabled": lambda x: isinstance(x, bool),
    }
    
    # 默认值
    DEFAULT_VALUES = {
        "version": "1.0.0",
        "enabled": True,
        "tags": [],
        "dependencies": [],
    }
    
    def __init__(self):
        """初始化技能元数据解析器"""
        self.frontmatter_pattern = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
    
    def parse_skill_file(self, file_path: str) -> Optional[SkillMetadata]:
        """
        解析技能文件，返回技能元数据
        
        Args:
            file_path: 技能文件路径
            
        Returns:
            技能元数据对象，解析失败返回None
        """
        try:
            # 验证文件存在性和可读性
            if not self._validate_file_access(file_path):
                return None
            
            # 根据文件类型选择解析方法
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.md', '.markdown']:
                return self._parse_markdown_file(file_path)
            elif file_extension in ['.yaml', '.yml']:
                return self._parse_yaml_file(file_path)
            elif file_extension == '.json':
                return self._parse_json_file(file_path)
            else:
                logger.warning(f"不支持的文件格式: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"解析技能文件 {file_path} 时出错: {e}")
            return None
    
    def _parse_markdown_file(self, file_path: str) -> Optional[SkillMetadata]:
        """解析Markdown格式的技能文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取frontmatter
            frontmatter_match = self.frontmatter_pattern.match(content)
            if not frontmatter_match:
                logger.warning(f"SKILL.md文件缺少frontmatter: {file_path}")
                return None
            
            frontmatter_yaml = frontmatter_match.group(1)
            metadata = yaml.safe_load(frontmatter_yaml)
            
            if not metadata:
                logger.warning(f"frontmatter解析失败: {file_path}")
                return None
            
            # 提取技能内容
            skill_content = content[frontmatter_match.end():]
            
            # 验证和补全元数据
            validated_metadata = self._validate_and_complete_metadata(metadata, file_path)
            if not validated_metadata:
                return None
            
            # 生成技能ID
            skill_id = self._generate_skill_id(validated_metadata['name'], file_path)
            
            # 创建技能元数据对象
            return SkillMetadata(
                skill_id=skill_id,
                name=validated_metadata['name'],
                display_name=validated_metadata.get('display_name', validated_metadata['name']),
                description=validated_metadata['description'],
                category=validated_metadata.get('category', SkillCategory.UTILITY.value),
                version=validated_metadata['version'],
                author=validated_metadata['author'],
                tags=validated_metadata.get('tags', []),
                dependencies=validated_metadata.get('dependencies', []),
                enabled=validated_metadata.get('enabled', True),
                file_path=file_path,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                config_schema=validated_metadata.get('config_schema'),
                content=skill_content,
                parameters_schema=self._extract_parameters_schema(skill_content)
            )
            
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误 {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"解析Markdown文件 {file_path} 时出错: {e}")
            return None
    
    def _parse_yaml_file(self, file_path: str) -> Optional[SkillMetadata]:
        """解析YAML格式的技能文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f)
            
            if not metadata:
                logger.warning(f"YAML文件内容为空: {file_path}")
                return None
            
            # 验证和补全元数据
            validated_metadata = self._validate_and_complete_metadata(metadata, file_path)
            if not validated_metadata:
                return None
            
            # 生成技能ID
            skill_id = self._generate_skill_id(validated_metadata['name'], file_path)
            
            # 创建技能元数据对象
            return SkillMetadata(
                skill_id=skill_id,
                name=validated_metadata['name'],
                display_name=validated_metadata.get('display_name', validated_metadata['name']),
                description=validated_metadata['description'],
                category=validated_metadata.get('category', SkillCategory.UTILITY.value),
                version=validated_metadata['version'],
                author=validated_metadata['author'],
                tags=validated_metadata.get('tags', []),
                dependencies=validated_metadata.get('dependencies', []),
                enabled=validated_metadata.get('enabled', True),
                file_path=file_path,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                config_schema=validated_metadata.get('config_schema'),
                content=validated_metadata.get('content', ''),
                parameters_schema=validated_metadata.get('parameters_schema')
            )
            
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误 {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"解析YAML文件 {file_path} 时出错: {e}")
            return None
    
    def _parse_json_file(self, file_path: str) -> Optional[SkillMetadata]:
        """解析JSON格式的技能文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            if not metadata:
                logger.warning(f"JSON文件内容为空: {file_path}")
                return None
            
            # 验证和补全元数据
            validated_metadata = self._validate_and_complete_metadata(metadata, file_path)
            if not validated_metadata:
                return None
            
            # 生成技能ID
            skill_id = self._generate_skill_id(validated_metadata['name'], file_path)
            
            # 创建技能元数据对象
            return SkillMetadata(
                skill_id=skill_id,
                name=validated_metadata['name'],
                display_name=validated_metadata.get('display_name', validated_metadata['name']),
                description=validated_metadata['description'],
                category=validated_metadata.get('category', SkillCategory.UTILITY.value),
                version=validated_metadata['version'],
                author=validated_metadata['author'],
                tags=validated_metadata.get('tags', []),
                dependencies=validated_metadata.get('dependencies', []),
                enabled=validated_metadata.get('enabled', True),
                file_path=file_path,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                config_schema=validated_metadata.get('config_schema'),
                content=validated_metadata.get('content', ''),
                parameters_schema=validated_metadata.get('parameters_schema')
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误 {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"解析JSON文件 {file_path} 时出错: {e}")
            return None
    
    def _validate_file_access(self, file_path: str) -> bool:
        """验证文件可访问性"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"技能文件不存在: {file_path}")
                return False
            
            if not os.path.isfile(file_path):
                logger.warning(f"路径不是文件: {file_path}")
                return False
            
            # 检查文件大小（不超过10MB）
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"技能文件过大: {file_path} ({file_size} bytes)")
                return False
            
            # 检查文件可读性
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # 尝试读取前1KB
            
            return True
            
        except PermissionError:
            logger.warning(f"没有权限读取文件: {file_path}")
            return False
        except Exception as e:
            logger.error(f"验证文件访问 {file_path} 时出错: {e}")
            return False
    
    def _validate_and_complete_metadata(self, metadata: Dict[str, Any], file_path: str) -> Optional[Dict[str, Any]]:
        """验证和补全元数据"""
        try:
            # 检查必填字段
            missing_fields = []
            for field in self.REQUIRED_FIELDS:
                if field not in metadata or not metadata[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.warning(f"技能文件缺少必填字段 {missing_fields}: {file_path}")
                return None
            
            # 应用默认值
            validated_metadata = metadata.copy()
            for field, default_value in self.DEFAULT_VALUES.items():
                if field not in validated_metadata:
                    validated_metadata[field] = default_value
            
            # 验证字段格式
            validation_errors = []
            for field, validator in self.FIELD_VALIDATORS.items():
                if field in validated_metadata:
                    try:
                        if not validator(validated_metadata[field]):
                            validation_errors.append(field)
                    except Exception as e:
                        logger.warning(f"验证字段 {field} 时出错: {e}")
                        validation_errors.append(field)
            
            if validation_errors:
                logger.warning(f"技能文件字段验证失败 {validation_errors}: {file_path}")
                return None
            
            # 清理和标准化数据
            validated_metadata['name'] = validated_metadata['name'].strip()
            validated_metadata['description'] = validated_metadata['description'].strip()
            validated_metadata['author'] = validated_metadata['author'].strip()
            
            # 标准化标签
            if 'tags' in validated_metadata:
                validated_metadata['tags'] = [tag.strip().lower() for tag in validated_metadata['tags'] if tag.strip()]
            
            return validated_metadata
            
        except Exception as e:
            logger.error(f"验证元数据时出错: {e}")
            return None
    
    def _generate_skill_id(self, name: str, file_path: str) -> str:
        """生成技能ID"""
        # 使用名称和文件路径生成唯一ID
        base_string = f"{name}:{file_path}"
        return hashlib.md5(base_string.encode('utf-8')).hexdigest()[:16]
    
    def _extract_parameters_schema(self, content: str) -> Optional[Dict[str, Any]]:
        """从技能内容中提取参数模式"""
        try:
            # 查找参数模式块
            param_block_pattern = re.compile(
                r'```(?:yaml|json)?\s*parameters?\s*:?\s*\n(.*?)\n```',
                re.DOTALL | re.IGNORECASE
            )
            
            match = param_block_pattern.search(content)
            if match:
                param_content = match.group(1)
                try:
                    return yaml.safe_load(param_content)
                except yaml.YAMLError:
                    # 尝试JSON格式
                    try:
                        return json.loads(param_content)
                    except json.JSONDecodeError:
                        logger.warning("参数模式解析失败")
                        return None
            
            return None
            
        except Exception as e:
            logger.warning(f"提取参数模式时出错: {e}")
            return None
    
    def validate_metadata(self, metadata: SkillMetadata) -> Tuple[bool, List[str]]:
        """
        验证技能元数据完整性
        
        Args:
            metadata: 技能元数据对象
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        # 检查必填字段
        if not metadata.name or not metadata.name.strip():
            errors.append("技能名称不能为空")
        
        if not metadata.description or not metadata.description.strip():
            errors.append("技能描述不能为空")
        
        if not metadata.version:
            errors.append("技能版本不能为空")
        
        if not metadata.author or not metadata.author.strip():
            errors.append("技能作者不能为空")
        
        # 检查版本格式
        if not re.match(r'^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9.]+)?$', metadata.version):
            errors.append("技能版本格式不正确")
        
        # 检查分类有效性
        if metadata.category not in [cat.value for cat in SkillCategory]:
            errors.append(f"技能分类无效: {metadata.category}")
        
        # 检查标签数量
        if metadata.tags and len(metadata.tags) > 20:
            errors.append("技能标签数量不能超过20个")
        
        # 检查文件路径
        if not os.path.exists(metadata.file_path):
            errors.append(f"技能文件不存在: {metadata.file_path}")
        
        return len(errors) == 0, errors


def create_parser() -> SkillMetadataParser:
    """
    创建技能元数据解析器实例
    
    Returns:
        技能元数据解析器实例
    """
    return SkillMetadataParser()


# 测试函数
def test_parser():
    """测试解析器功能"""
    parser = SkillMetadataParser()
    
    # 测试解析现有技能文件
    test_files = [
        "backend/app/skills/skills/algorithmic-art/SKILL.md",
        "backend/app/skills/skills/data-analysis/SKILL.md",
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            metadata = parser.parse_skill_file(file_path)
            if metadata:
                print(f"成功解析技能文件: {file_path}")
                print(f"技能名称: {metadata.name}")
                print(f"技能描述: {metadata.description[:100]}...")
                print(f"技能分类: {metadata.category}")
                print()
            else:
                print(f"解析失败: {file_path}")
        else:
            print(f"文件不存在: {file_path}")


if __name__ == "__main__":
    test_parser()