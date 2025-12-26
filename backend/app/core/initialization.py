"""系统参数初始化脚本"""
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.parameter_template import ParameterTemplate


SYSTEM_PARAMETERS = {
    "generation": {
        "name": "生成参数",
        "description": "控制文本生成的质量和风格",
        "order": 1,
        "parameters": {
            "temperature": {
                "type": "number",
                "value": 0.7,
                "description": "控制输出的随机性，值越高越有创意，值越低越确定性",
                "min": 0.0,
                "max": 2.0,
                "step": 0.1
            },
            "top_p": {
                "type": "number",
                "value": 1.0,
                "description": "核采样概率阈值，越低越保守",
                "min": 0.0,
                "max": 1.0,
                "step": 0.01
            },
            "max_tokens": {
                "type": "integer",
                "value": 1000,
                "description": "单次生成的最大token数量，影响回复长度",
                "min": 1,
                "max": 4096,
                "step": 1
            },
            "presence_penalty": {
                "type": "number",
                "value": 0.0,
                "description": "惩罚重复词汇，正值鼓励新词汇",
                "min": -2.0,
                "max": 2.0,
                "step": 0.1
            },
            "frequency_penalty": {
                "type": "number",
                "value": 0.0,
                "description": "惩罚频繁词汇，正值降低重复率",
                "min": -2.0,
                "max": 2.0,
                "step": 0.1
            }
        }
    },
    "safety": {
        "name": "安全参数",
        "description": "控制内容过滤和安全级别",
        "order": 2,
        "parameters": {
            "response_mime_type": {
                "type": "enum",
                "value": "text",
                "options": ["text", "json_object"],
                "description": "响应格式，json_object强制输出JSON"
            }
        }
    },
    "advanced": {
        "name": "高级参数",
        "description": "专家级参数调整",
        "order": 3,
        "parameters": {
            "logprobs": {
                "type": "boolean",
                "value": False,
                "description": "是否返回对数概率信息"
            },
            "top_logprobs": {
                "type": "integer",
                "value": 0,
                "description": "每个位置返回的最可能token数量",
                "min": 0,
                "max": 20,
                "step": 1
            }
        }
    }
}


def get_system_parameters_dict() -> Dict[str, Any]:
    """获取系统级默认参数字典"""
    params = {}
    
    for group_name, group_config in SYSTEM_PARAMETERS.items():
        group_params = group_config.get("parameters", {})
        for param_name, param_config in group_params.items():
            params[param_name] = param_config.get("value")
    
    return params


def create_system_parameter_template(
    db: Session,
    name: str = "系统默认参数模板",
    description: str = "系统级默认参数配置，包含所有LLM调用所需的默认参数",
    is_active: bool = True
) -> ParameterTemplate:
    """创建系统参数模板"""
    
    params = get_system_parameters_dict()
    
    template = ParameterTemplate(
        name=name,
        description=description,
        level="system",
        parent_id=None,
        level_id=None,
        parameters=params,
        version="1.0.0",
        is_active=is_active
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


def get_or_create_system_template(db: Session) -> ParameterTemplate:
    """获取或创建系统参数模板"""
    
    existing = db.query(ParameterTemplate).filter(
        ParameterTemplate.level == "system",
        ParameterTemplate.is_active == True
    ).first()
    
    if existing:
        return existing
    
    return create_system_parameter_template(db)


def update_system_parameters(
    db: Session,
    parameters: Dict[str, Any],
    description: str = None
) -> ParameterTemplate:
    """更新系统参数模板"""
    
    template = get_or_create_system_template(db)
    
    existing_params = template.parameters or {}
    existing_params.update(parameters)
    
    template.parameters = existing_params
    
    if description:
        template.description = description
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


def initialize_system_parameters(db: Session) -> Dict[str, Any]:
    """初始化系统参数"""
    
    template = get_or_create_system_template(db)
    
    return template.parameters or {}


def reset_system_parameters(db: Session) -> ParameterTemplate:
    """重置系统参数为默认值"""
    
    existing = db.query(ParameterTemplate).filter(
        ParameterTemplate.level == "system"
    ).all()
    
    for template in existing:
        db.delete(template)
    
    db.commit()
    
    return create_system_parameter_template(db)


def seed_all_system_parameters(db: Session) -> Dict[str, Any]:
    """播种所有系统参数（包含分组信息）"""
    
    template = get_or_create_system_template(db)
    
    template.parameters = SYSTEM_PARAMETERS
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template.parameters


def init_db():
    """初始化数据库（命令行入口）"""
    print("正在初始化系统参数...")
    
    db = SessionLocal()
    try:
        params = initialize_system_parameters(db)
        print(f"系统参数初始化完成，共 {len(params)} 个参数")
        print(f"参数列表: {list(params.keys())}")
        return True
    except Exception as e:
        print(f"系统参数初始化失败: {e}")
        return False
    finally:
        db.close()


def seed_db():
    """播种数据库（命令行入口，包含完整分组信息）"""
    print("正在播种系统参数（包含分组信息）...")
    
    db = SessionLocal()
    try:
        params = seed_all_system_parameters(db)
        print("系统参数播种完成")
        print(f"参数分组: {list(params.keys())}")
        return True
    except Exception as e:
        print(f"系统参数播种失败: {e}")
        return False
    finally:
        db.close()


def reset_db():
    """重置数据库（命令行入口）"""
    print("正在重置系统参数...")
    
    db = SessionLocal()
    try:
        template = reset_system_parameters(db)
        print(f"系统参数重置完成，模板ID: {template.id}")
        return True
    except Exception as e:
        print(f"系统参数重置失败: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    
    if command == "init":
        success = init_db()
    elif command == "seed":
        success = seed_db()
    elif command == "reset":
        success = reset_db()
    else:
        print(f"未知命令: {command}")
        print("可用命令: init, seed, reset")
        success = False
    
    sys.exit(0 if success else 1)
