#!/usr/bin/env python3
"""
知识图谱配置API

提供前端配置界面的完整API支持，包括：
1. 实体类型配置管理
2. 关系类型配置管理
3. 提取规则管理
4. 质量规则管理
5. 配置版本管理
6. 配置导入导出
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import json
import re
import logging

from app.database import get_db
from app.services.knowledge.entity_config_manager import EntityConfigManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kg-config", tags=["knowledge-graph-config"])


# ============== 请求/响应模型 ==============

class EntityTypeCreate(BaseModel):
    """实体类型创建请求"""
    key: str = Field(..., min_length=1, max_length=50, description="实体类型标识")
    name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    description: str = Field(default="", max_length=500, description="描述")
    color: str = Field(default="#4A90E2", description="显示颜色")
    enabled: bool = Field(default=True, description="是否启用")

    @validator('key')
    def validate_key(cls, v):
        if not re.match(r'^[A-Z][A-Z0-9_]*$', v):
            raise ValueError('实体类型标识必须为大写字母开头，只能包含大写字母、数字和下划线')
        return v

    @validator('color')
    def validate_color(cls, v):
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('颜色必须是有效的十六进制格式，如 #4A90E2')
        return v


class EntityTypeUpdate(BaseModel):
    """实体类型更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = None
    enabled: Optional[bool] = None

    @validator('color')
    def validate_color(cls, v):
        if v is not None and not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('颜色必须是有效的十六进制格式')
        return v


class RelationshipTypeCreate(BaseModel):
    """关系类型创建请求"""
    key: str = Field(..., min_length=1, max_length=50, description="关系类型标识")
    name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    description: str = Field(default="", max_length=500, description="描述")
    color: str = Field(default="#7ED321", description="显示颜色")
    enabled: bool = Field(default=True, description="是否启用")
    source_types: List[str] = Field(default=[], description="允许的源实体类型")
    target_types: List[str] = Field(default=[], description="允许的目标实体类型")
    symmetric: bool = Field(default=False, description="是否对称关系")
    transitive: bool = Field(default=False, description="是否传递关系")

    @validator('key')
    def validate_key(cls, v):
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError('关系类型标识必须为小写字母开头，只能包含小写字母、数字和下划线')
        return v


class ExtractionRuleCreate(BaseModel):
    """提取规则创建请求"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    pattern: str = Field(..., min_length=1, max_length=1000, description="正则表达式模式")
    description: str = Field(default="", max_length=500, description="描述")
    entity_type: str = Field(..., description="适用的实体类型")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=0, ge=0, le=100, description="优先级(0-100)")

    @validator('pattern')
    def validate_pattern(cls, v):
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f'无效的正则表达式: {e}')
        return v


class QualityRuleCreate(BaseModel):
    """质量规则创建请求"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    rule_type: str = Field(..., description="规则类型: completeness, consistency, accuracy")
    description: str = Field(default="", max_length=500, description="描述")
    parameters: Dict[str, Any] = Field(default={}, description="规则参数")
    enabled: bool = Field(default=True, description="是否启用")
    severity: str = Field(default="warning", description="严重程度: error, warning, info")

    @validator('rule_type')
    def validate_rule_type(cls, v):
        allowed = ['completeness', 'consistency', 'accuracy', 'uniqueness', 'timeliness']
        if v not in allowed:
            raise ValueError(f'规则类型必须是以下之一: {allowed}')
        return v

    @validator('severity')
    def validate_severity(cls, v):
        allowed = ['error', 'warning', 'info']
        if v not in allowed:
            raise ValueError(f'严重程度必须是以下之一: {allowed}')
        return v


class ConfigVersionCreate(BaseModel):
    """配置版本创建请求"""
    name: str = Field(..., min_length=1, max_length=100, description="版本名称")
    description: str = Field(default="", max_length=500, description="版本描述")


class APIResponse(BaseModel):
    """统一API响应"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============== 依赖注入 ==============

def get_config_manager(knowledge_base_id: Optional[int] = None) -> EntityConfigManager:
    """获取配置管理器"""
    return EntityConfigManager(knowledge_base_id)


# ============== 实体类型管理API ==============

@router.get("/entity-types", response_model=APIResponse)
async def get_entity_types(
    knowledge_base_id: Optional[int] = None,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """获取所有实体类型配置"""
    try:
        entity_types = config_manager.get_entity_types()

        # 格式化响应
        formatted_types = []
        for key, config in entity_types.items():
            formatted_types.append({
                'key': key,
                'name': config.get('name', key),
                'description': config.get('description', ''),
                'color': config.get('color', '#4A90E2'),
                'enabled': config.get('enabled', True),
                'created_at': config.get('created_at'),
                'updated_at': config.get('updated_at')
            })

        return APIResponse(
            success=True,
            message="获取实体类型成功",
            data={
                'total': len(formatted_types),
                'entity_types': formatted_types
            }
        )
    except Exception as e:
        logger.error(f"获取实体类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实体类型失败: {str(e)}")


@router.post("/entity-types", response_model=APIResponse)
async def create_entity_type(
    request: EntityTypeCreate,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """创建新的实体类型"""
    try:
        config_manager = EntityConfigManager(knowledge_base_id)

        config_dict = {
            'name': request.name,
            'description': request.description,
            'color': request.color,
            'enabled': request.enabled,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        success = config_manager.add_entity_type(request.key, config_dict)

        if success:
            return APIResponse(
                success=True,
                message=f"成功创建实体类型: {request.name}",
                data={'key': request.key}
            )
        else:
            raise HTTPException(status_code=400, detail="创建实体类型失败，可能已存在")

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"创建实体类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建实体类型失败: {str(e)}")


@router.put("/entity-types/{entity_type_key}", response_model=APIResponse)
async def update_entity_type(
    entity_type_key: str,
    request: EntityTypeUpdate,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """更新实体类型配置"""
    try:
        config_manager = EntityConfigManager(knowledge_base_id)

        # 只更新非空字段
        update_dict = {k: v for k, v in request.dict().items() if v is not None}
        update_dict['updated_at'] = datetime.now().isoformat()

        success = config_manager.update_entity_type(entity_type_key, update_dict)

        if success:
            return APIResponse(
                success=True,
                message=f"成功更新实体类型: {entity_type_key}"
            )
        else:
            raise HTTPException(status_code=404, detail=f"实体类型不存在: {entity_type_key}")

    except Exception as e:
        logger.error(f"更新实体类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新实体类型失败: {str(e)}")


@router.delete("/entity-types/{entity_type_key}", response_model=APIResponse)
async def delete_entity_type(
    entity_type_key: str,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """删除实体类型"""
    try:
        config_manager = EntityConfigManager(knowledge_base_id)

        success = config_manager.remove_entity_type(entity_type_key)

        if success:
            return APIResponse(
                success=True,
                message=f"成功删除实体类型: {entity_type_key}"
            )
        else:
            raise HTTPException(status_code=404, detail=f"实体类型不存在: {entity_type_key}")

    except Exception as e:
        logger.error(f"删除实体类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除实体类型失败: {str(e)}")


# ============== 关系类型管理API ==============

@router.get("/relationship-types", response_model=APIResponse)
async def get_relationship_types(
    knowledge_base_id: Optional[int] = None,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """获取所有关系类型配置"""
    try:
        # 从配置中获取关系类型
        config = config_manager.config
        relationship_types = config.get('relationship_types', {})

        formatted_types = []
        for key, rel_config in relationship_types.items():
            formatted_types.append({
                'key': key,
                'name': rel_config.get('name', key),
                'description': rel_config.get('description', ''),
                'color': rel_config.get('color', '#7ED321'),
                'enabled': rel_config.get('enabled', True),
                'source_types': rel_config.get('source_types', []),
                'target_types': rel_config.get('target_types', []),
                'symmetric': rel_config.get('symmetric', False),
                'transitive': rel_config.get('transitive', False)
            })

        return APIResponse(
            success=True,
            message="获取关系类型成功",
            data={
                'total': len(formatted_types),
                'relationship_types': formatted_types
            }
        )
    except Exception as e:
        logger.error(f"获取关系类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取关系类型失败: {str(e)}")


@router.post("/relationship-types", response_model=APIResponse)
async def create_relationship_type(
    request: RelationshipTypeCreate,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """创建新的关系类型"""
    try:
        config_manager = EntityConfigManager(knowledge_base_id)

        config_dict = {
            'name': request.name,
            'description': request.description,
            'color': request.color,
            'enabled': request.enabled,
            'source_types': request.source_types,
            'target_types': request.target_types,
            'symmetric': request.symmetric,
            'transitive': request.transitive,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # 添加到配置
        if 'relationship_types' not in config_manager.config:
            config_manager.config['relationship_types'] = {}

        config_manager.config['relationship_types'][request.key] = config_dict
        config_manager._save_config()

        return APIResponse(
            success=True,
            message=f"成功创建关系类型: {request.name}",
            data={'key': request.key}
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"创建关系类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建关系类型失败: {str(e)}")


# ============== 提取规则管理API ==============

@router.get("/extraction-rules", response_model=APIResponse)
async def get_extraction_rules(
    entity_type: Optional[str] = None,
    knowledge_base_id: Optional[int] = None,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """获取提取规则"""
    try:
        rules = config_manager.get_extraction_rules(entity_type)

        formatted_rules = []
        if isinstance(rules, dict):
            for etype, type_rules in rules.items():
                for rule in type_rules:
                    formatted_rules.append({
                        'id': rule.get('id', ''),
                        'name': rule.get('name', ''),
                        'pattern': rule.get('pattern', ''),
                        'description': rule.get('description', ''),
                        'entity_type': etype,
                        'enabled': rule.get('enabled', True),
                        'priority': rule.get('priority', 0)
                    })
        elif isinstance(rules, list):
            for rule in rules:
                formatted_rules.append({
                    'id': rule.get('id', ''),
                    'name': rule.get('name', ''),
                    'pattern': rule.get('pattern', ''),
                    'description': rule.get('description', ''),
                    'entity_type': entity_type or rule.get('entity_type', ''),
                    'enabled': rule.get('enabled', True),
                    'priority': rule.get('priority', 0)
                })

        return APIResponse(
            success=True,
            message="获取提取规则成功",
            data={
                'total': len(formatted_rules),
                'rules': formatted_rules
            }
        )
    except Exception as e:
        logger.error(f"获取提取规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取提取规则失败: {str(e)}")


@router.post("/extraction-rules", response_model=APIResponse)
async def create_extraction_rule(
    request: ExtractionRuleCreate,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """创建提取规则"""
    try:
        config_manager = EntityConfigManager(knowledge_base_id)

        rule_dict = {
            'id': f"rule_{datetime.now().timestamp()}",
            'name': request.name,
            'pattern': request.pattern,
            'description': request.description,
            'enabled': request.enabled,
            'priority': request.priority,
            'created_at': datetime.now().isoformat()
        }

        success = config_manager.add_extraction_rule(request.entity_type, rule_dict)

        if success:
            return APIResponse(
                success=True,
                message=f"成功创建提取规则: {request.name}",
                data={'id': rule_dict['id']}
            )
        else:
            raise HTTPException(status_code=400, detail="创建提取规则失败")

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"创建提取规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建提取规则失败: {str(e)}")


# ============== 质量规则管理API ==============

@router.get("/quality-rules", response_model=APIResponse)
async def get_quality_rules(
    knowledge_base_id: Optional[int] = None,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """获取质量规则"""
    try:
        # 从配置中获取质量规则
        config = config_manager.config
        quality_rules = config.get('quality_rules', [])

        return APIResponse(
            success=True,
            message="获取质量规则成功",
            data={
                'total': len(quality_rules),
                'rules': quality_rules
            }
        )
    except Exception as e:
        logger.error(f"获取质量规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取质量规则失败: {str(e)}")


@router.post("/quality-rules", response_model=APIResponse)
async def create_quality_rule(
    request: QualityRuleCreate,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """创建质量规则"""
    try:
        config_manager = EntityConfigManager(knowledge_base_id)

        rule_dict = {
            'id': f"quality_rule_{datetime.now().timestamp()}",
            'name': request.name,
            'rule_type': request.rule_type,
            'description': request.description,
            'parameters': request.parameters,
            'enabled': request.enabled,
            'severity': request.severity,
            'created_at': datetime.now().isoformat()
        }

        # 添加到配置
        if 'quality_rules' not in config_manager.config:
            config_manager.config['quality_rules'] = []

        config_manager.config['quality_rules'].append(rule_dict)
        config_manager._save_config()

        return APIResponse(
            success=True,
            message=f"成功创建质量规则: {request.name}",
            data={'id': rule_dict['id']}
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"创建质量规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建质量规则失败: {str(e)}")


# ============== 配置导入导出API ==============

@router.get("/export", response_model=APIResponse)
async def export_config(
    knowledge_base_id: Optional[int] = None,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """导出完整配置"""
    try:
        config = config_manager.config

        export_data = {
            'version': '1.0',
            'export_time': datetime.now().isoformat(),
            'knowledge_base_id': knowledge_base_id,
            'config': config
        }

        return APIResponse(
            success=True,
            message="配置导出成功",
            data=export_data
        )
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")


@router.post("/import", response_model=APIResponse)
async def import_config(
    file: UploadFile = File(...),
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """导入配置"""
    try:
        # 读取文件内容
        content = await file.read()
        import_data = json.loads(content)

        # 验证配置格式
        if 'config' not in import_data:
            raise HTTPException(status_code=400, detail="无效的配置文件格式")

        config_manager = EntityConfigManager(knowledge_base_id)

        # 备份当前配置
        backup_config = config_manager.config.copy()

        try:
            # 导入新配置
            config_manager.config = import_data['config']
            config_manager._save_config()

            return APIResponse(
                success=True,
                message="配置导入成功",
                data={
                    'imported_at': datetime.now().isoformat(),
                    'source_version': import_data.get('version', 'unknown')
                }
            )
        except Exception as e:
            # 恢复备份
            config_manager.config = backup_config
            config_manager._save_config()
            raise e

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON格式")
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")


# ============== 配置验证API ==============

@router.post("/validate", response_model=APIResponse)
async def validate_config(
    knowledge_base_id: Optional[int] = None,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """验证配置有效性"""
    try:
        config = config_manager.config
        errors = []
        warnings = []

        # 验证实体类型
        entity_types = config.get('entity_types', {})
        if not entity_types:
            warnings.append("未配置任何实体类型")

        # 验证提取规则
        extraction_rules = config.get('extraction_rules', {})
        for entity_type, rules in extraction_rules.items():
            if entity_type not in entity_types:
                warnings.append(f"提取规则引用了未定义的实体类型: {entity_type}")

            for rule in rules:
                pattern = rule.get('pattern', '')
                try:
                    re.compile(pattern)
                except re.error:
                    errors.append(f"无效的正则表达式: {rule.get('name', 'unknown')}")

        # 验证关系类型
        relationship_types = config.get('relationship_types', {})
        for rel_key, rel_config in relationship_types.items():
            source_types = rel_config.get('source_types', [])
            target_types = rel_config.get('target_types', [])

            for st in source_types:
                if st not in entity_types:
                    warnings.append(f"关系 {rel_key} 引用了未定义的源实体类型: {st}")

            for tt in target_types:
                if tt not in entity_types:
                    warnings.append(f"关系 {rel_key} 引用了未定义的目标实体类型: {tt}")

        return APIResponse(
            success=True,
            message="配置验证完成",
            data={
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'error_count': len(errors),
                'warning_count': len(warnings)
            }
        )
    except Exception as e:
        logger.error(f"验证配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证配置失败: {str(e)}")


# ============== 配置预览API ==============

@router.post("/preview-extraction", response_model=APIResponse)
async def preview_extraction(
    text: str,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """预览实体提取效果"""
    try:
        from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor

        processor = AdvancedTextProcessor(db, knowledge_base_id)
        entities, relationships = processor.extract_entities_relationships(text)

        # 统计信息
        entity_types = {}
        for entity in entities:
            etype = entity.get('type', 'UNKNOWN')
            entity_types[etype] = entity_types.get(etype, 0) + 1

        return APIResponse(
            success=True,
            message="提取预览成功",
            data={
                'entities': entities,
                'relationships': relationships,
                'statistics': {
                    'total_entities': len(entities),
                    'total_relationships': len(relationships),
                    'entity_types': entity_types
                }
            }
        )
    except Exception as e:
        logger.error(f"提取预览失败: {e}")
        raise HTTPException(status_code=500, detail=f"提取预览失败: {str(e)}")
