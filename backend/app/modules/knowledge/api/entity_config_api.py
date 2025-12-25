"""
实体配置API - 支持用户通过API管理实体类型和提取规则
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from ....services.knowledge.advanced_text_processor import AdvancedTextProcessor
from ....services.knowledge.entity_config_manager import EntityConfigManager

router = APIRouter(prefix="/entity-config", tags=["实体配置管理"])

# 请求和响应模型
class EntityTypeConfig(BaseModel):
    name: str
    description: str
    color: str = "#000000"
    enabled: bool = True

class ExtractionRule(BaseModel):
    name: str
    pattern: str
    description: str
    entity_type: Optional[str] = None
    enabled: bool = True

class DictionaryUpdate(BaseModel):
    terms: List[str]

class ConfigResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# 依赖注入
def get_config_manager() -> EntityConfigManager:
    return EntityConfigManager()

def get_text_processor() -> AdvancedTextProcessor:
    return AdvancedTextProcessor()

@router.get("/entity-types", response_model=ConfigResponse)
async def get_entity_types(
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """获取所有实体类型配置"""
    try:
        entity_types = config_manager.get_entity_types()
        return ConfigResponse(
            success=True,
            message="获取实体类型成功",
            data={"entity_types": entity_types}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体类型失败: {str(e)}")

@router.post("/entity-types/{entity_type}", response_model=ConfigResponse)
async def add_entity_type(
    entity_type: str,
    config: EntityTypeConfig,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """添加新的实体类型"""
    try:
        config_dict = config.dict()
        success = config_manager.add_entity_type(entity_type, config_dict)
        
        if success:
            return ConfigResponse(
                success=True,
                message=f"成功添加实体类型: {entity_type}"
            )
        else:
            raise HTTPException(status_code=400, detail=f"添加实体类型失败: {entity_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加实体类型失败: {str(e)}")

@router.put("/entity-types/{entity_type}", response_model=ConfigResponse)
async def update_entity_type(
    entity_type: str,
    config: EntityTypeConfig,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """更新实体类型配置"""
    try:
        config_dict = config.dict()
        success = config_manager.update_entity_type(entity_type, config_dict)
        
        if success:
            return ConfigResponse(
                success=True,
                message=f"成功更新实体类型: {entity_type}"
            )
        else:
            raise HTTPException(status_code=400, detail=f"更新实体类型失败: {entity_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新实体类型失败: {str(e)}")

@router.get("/extraction-rules", response_model=ConfigResponse)
async def get_extraction_rules(
    entity_type: Optional[str] = None,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """获取提取规则"""
    try:
        rules = config_manager.get_extraction_rules(entity_type)
        return ConfigResponse(
            success=True,
            message="获取提取规则成功",
            data={"rules": rules}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提取规则失败: {str(e)}")

@router.post("/extraction-rules/{entity_type}", response_model=ConfigResponse)
async def add_extraction_rule(
    entity_type: str,
    rule: ExtractionRule,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """添加提取规则"""
    try:
        rule_dict = rule.dict()
        rule_dict['entity_type'] = entity_type
        success = config_manager.add_extraction_rule(entity_type, rule_dict)
        
        if success:
            return ConfigResponse(
                success=True,
                message=f"成功为 {entity_type} 添加提取规则"
            )
        else:
            raise HTTPException(status_code=400, detail=f"添加提取规则失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加提取规则失败: {str(e)}")

@router.get("/dictionaries/{entity_type}", response_model=ConfigResponse)
async def get_dictionary(
    entity_type: str,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """获取指定实体类型的词典"""
    try:
        dictionary = config_manager.get_dictionary(entity_type)
        return ConfigResponse(
            success=True,
            message="获取词典成功",
            data={"dictionary": dictionary}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取词典失败: {str(e)}")

@router.post("/dictionaries/{entity_type}", response_model=ConfigResponse)
async def add_to_dictionary(
    entity_type: str,
    update: DictionaryUpdate,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """向词典添加术语"""
    try:
        success = config_manager.add_to_dictionary(entity_type, update.terms)
        
        if success:
            return ConfigResponse(
                success=True,
                message=f"成功向 {entity_type} 词典添加 {len(update.terms)} 个术语"
            )
        else:
            raise HTTPException(status_code=400, detail=f"添加词典术语失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加词典术语失败: {str(e)}")

@router.post("/test-extraction", response_model=ConfigResponse)
async def test_entity_extraction(
    text: str,
    processor: AdvancedTextProcessor = Depends(get_text_processor)
):
    """测试实体提取效果"""
    try:
        entities, relationships = processor.extract_entities_relationships(text)
        
        return ConfigResponse(
            success=True,
            message="实体提取测试成功",
            data={
                "entities": entities,
                "relationships": relationships,
                "summary": {
                    "total_entities": len(entities),
                    "total_relationships": len(relationships),
                    "entity_types": {}
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实体提取测试失败: {str(e)}")

@router.post("/export-config", response_model=ConfigResponse)
async def export_config(
    export_path: str,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """导出配置到文件"""
    try:
        success = config_manager.export_config(export_path)
        
        if success:
            return ConfigResponse(
                success=True,
                message=f"配置已导出到: {export_path}"
            )
        else:
            raise HTTPException(status_code=400, detail="导出配置失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")

@router.post("/import-config", response_model=ConfigResponse)
async def import_config(
    import_path: str,
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """从文件导入配置"""
    try:
        success = config_manager.import_config(import_path)
        
        if success:
            return ConfigResponse(
                success=True,
                message=f"配置已从 {import_path} 导入"
            )
        else:
            raise HTTPException(status_code=400, detail="导入配置失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")

@router.post("/reset-config", response_model=ConfigResponse)
async def reset_config(
    config_manager: EntityConfigManager = Depends(get_config_manager)
):
    """重置为默认配置"""
    try:
        success = config_manager.reset_to_default()
        
        if success:
            return ConfigResponse(
                success=True,
                message="配置已重置为默认值"
            )
        else:
            raise HTTPException(status_code=400, detail="重置配置失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置配置失败: {str(e)}")