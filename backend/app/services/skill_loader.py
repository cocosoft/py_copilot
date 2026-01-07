"""技能加载器服务"""
import re
import os
import yaml
from typing import Optional, Dict, Any
from app.core.logging_config import logger


class SkillLoader:
    """技能加载器，用于解析技能文件"""
    
    SKILL_FILE_NAME = "SKILL.md"
    FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
    
    @classmethod
    def parse_skill_file(cls, file_path: str) -> Optional[Dict[str, Any]]:
        """解析技能文件，提取元数据和内容"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"技能文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter_match = cls.FRONTMATTER_PATTERN.match(content)
            if not frontmatter_match:
                logger.warning(f"技能文件缺少frontmatter: {file_path}")
                return None
            
            frontmatter_yaml = frontmatter_match.group(1)
            metadata = yaml.safe_load(frontmatter_yaml)
            if not metadata:
                logger.warning(f"技能文件frontmatter解析失败: {file_path}")
                return None
            
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"技能文件缺少必填字段 '{field}': {file_path}")
                    return None
            
            skill_content = content[frontmatter_match.end():]
            parameters_schema = metadata.get('parameters_schema', {})
            
            return {
                'metadata': metadata,
                'content': skill_content,
                'parameters_schema': parameters_schema
            }
        except Exception as e:
            logger.error(f"解析技能文件失败 {file_path}: {e}")
            return None
    
    @classmethod
    def extract_parameters_schema(cls, content: str) -> Optional[Dict[str, Any]]:
        """从技能内容中提取参数模式"""
        param_block_pattern = re.compile(
            r'```(?:yaml|json)?\s*parameters?\s*:?\s*\n(.*?)\n```',
            re.DOTALL
        )
        match = param_block_pattern.search(content)
        if match:
            try:
                return yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                pass
        return None
