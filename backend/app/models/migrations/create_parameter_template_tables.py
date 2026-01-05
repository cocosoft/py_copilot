"""
参数模板表创建迁移脚本

此脚本创建参数模板相关的数据库表，并更新默认模型表以包含参数模板关联。
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy import (
    create_engine, 
    Column, 
    Integer, 
    String, 
    Text, 
    JSON, 
    Boolean, 
    DateTime, 
    ForeignKey, 
    UniqueConstraint,
    inspect,
    text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy import func

# 创建基类
Base = declarative_base()

class ParameterTemplate(Base):
    """参数模板"""
    __tablename__ = "parameter_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    scene = Column(String(100), nullable=False)  # 适用场景
    is_default = Column(Boolean, nullable=False, default=False)  # 是否为该场景的默认模板
    parameters = Column(JSON, nullable=False)  # 参数配置，JSON格式存储
    is_active = Column(Boolean, nullable=False, default=True)  # 是否激活
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    default_models = relationship("DefaultModel", back_populates="parameter_template")
    versions = relationship("ParameterTemplateVersion", back_populates="template", cascade="all, delete-orphan")
    
    # 唯一约束
    __table_args__ = (
        # 确保每个场景只有一个默认模板
        # 注意：如果使用SQLite，需要特殊处理唯一约束
    )


class ParameterTemplateVersion(Base):
    """参数模板版本"""
    __tablename__ = "parameter_template_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("parameter_templates.id", ondelete="CASCADE"), nullable=False)  # 关联模板ID
    version = Column(Integer, nullable=False)  # 版本号
    parameters = Column(JSON, nullable=False)  # 参数配置，JSON格式存储
    changelog = Column(Text, nullable=True)  # 版本变更说明
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    template = relationship("ParameterTemplate", back_populates="versions")
    
    # 唯一约束
    __table_args__ = (
        # 确保每个模板的版本号唯一
    )

class DefaultModel(Base):
    """默认模型配置 - 简化的模型用于迁移"""
    __tablename__ = "default_models"
    
    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(50), nullable=False, default="global")  # 默认作用域：global（全局）、scene（场景）
    scene = Column(String(100), nullable=True)  # 场景名称，当scope为scene时使用
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)  # 默认模型ID
    priority = Column(Integer, nullable=False, default=1)  # 模型优先级，数字越小优先级越高
    fallback_model_id = Column(Integer, ForeignKey("models.id", ondelete="SET NULL"), nullable=True)  # 备选模型ID
    parameter_template_id = Column(Integer, ForeignKey("parameter_templates.id", ondelete="SET NULL"), nullable=True)  # 参数模板ID
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    parameter_template = relationship("ParameterTemplate", back_populates="default_models")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('scope', 'scene', name='uq_scope_scene'),
    )


def create_parameter_template_tables():
    """创建参数模板相关表"""
    # 使用项目中的数据库连接
    from app.core.dependencies import SQLALCHEMY_DATABASE_URL
    
    # 创建数据库引擎
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # 检查表是否存在
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 创建 parameter_templates 表（如果不存在）
    if "parameter_templates" not in existing_tables:
        print("创建 parameter_templates 表...")
        ParameterTemplate.__table__.create(engine)
    else:
        print("parameter_templates 表已存在，跳过创建")
    
    # 创建 parameter_template_versions 表（如果不存在）
    if "parameter_template_versions" not in existing_tables:
        print("创建 parameter_template_versions 表...")
        ParameterTemplateVersion.__table__.create(engine)
    else:
        print("parameter_template_versions 表已存在，跳过创建")
    
    # 检查 default_models 表中是否有 parameter_template_id 字段
    default_models_columns = [col['name'] for col in inspector.get_columns("default_models")]
    
    if "parameter_template_id" not in default_models_columns:
        print("添加 parameter_template_id 字段到 default_models 表...")
        try:
            # 使用原生 SQL 添加字段
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE default_models ADD COLUMN parameter_template_id INTEGER"))
                conn.execute(text("ALTER TABLE default_models ADD FOREIGN KEY (parameter_template_id) REFERENCES parameter_templates(id) ON DELETE SET NULL"))
                conn.commit()
                print("成功添加 parameter_template_id 字段")
        except Exception as e:
            print(f"添加字段时出错: {str(e)}")
    else:
        print("default_models 表已有 parameter_template_id 字段")
    
    # 创建索引
    try:
        with engine.connect() as conn:
            # 为 parameter_templates 表创建索引
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_parameter_templates_scene ON parameter_templates(scene)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_parameter_templates_is_default ON parameter_templates(is_default)"))
            
            # 为 parameter_template_versions 表创建索引
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_parameter_template_versions_template_id ON parameter_template_versions(template_id)"))
            
            # 为 default_models 表的 parameter_template_id 创建索引
            if "parameter_template_id" in default_models_columns:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_default_models_parameter_template_id ON default_models(parameter_template_id)"))
            
            conn.commit()
            print("成功创建索引")
    except Exception as e:
        print(f"创建索引时出错: {str(e)}")
    
    print("参数模板表迁移完成")


if __name__ == "__main__":
    create_parameter_template_tables()