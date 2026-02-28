"""将MCP客户端工具映射迁移到工具表"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.mcp.models import MCPClientConfigModel, MCPToolMappingModel
from app.models.tool import Tool


def migrate_mcp_to_tools():
    """将MCP工具映射迁移到统一工具表"""
    db = SessionLocal()
    
    try:
        # 获取所有启用的MCP客户端配置
        clients = db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.enabled == True
        ).all()
        
        migrated_count = 0
        skipped_count = 0
        
        for client in clients:
            print(f"处理MCP客户端: {client.name} (ID: {client.id})")
            
            # 获取该客户端的工具映射
            mappings = db.query(MCPToolMappingModel).filter(
                MCPToolMappingModel.client_config_id == client.id
            ).all()
            
            for mapping in mappings:
                # 检查是否已存在
                existing = db.query(Tool).filter(
                    Tool.mcp_client_config_id == client.id,
                    Tool.mcp_tool_name == mapping.original_name
                ).first()
                
                if existing:
                    print(f"  跳过已存在: {mapping.local_name}")
                    skipped_count += 1
                    continue
                
                # 创建工具记录
                tool = Tool(
                    name=mapping.local_name,
                    display_name=mapping.local_name.replace('_', ' ').title(),
                    description=mapping.description or f"MCP工具: {mapping.original_name}",
                    category='mcp',
                    tool_type='mcp',
                    mcp_client_config_id=client.id,
                    mcp_tool_name=mapping.original_name,
                    parameters_schema=mapping.input_schema,
                    source='mcp',
                    is_official=False,
                    is_builtin=False,
                    status='active' if mapping.enabled else 'disabled',
                    is_active=mapping.enabled,
                    author=f"MCP:{client.name}",
                    version='1.0.0',
                    icon='🔗',
                    tags=['mcp', 'external']
                )
                
                db.add(tool)
                migrated_count += 1
                print(f"  迁移: {mapping.original_name} -> {mapping.local_name}")
        
        db.commit()
        print(f"\n✅ 迁移完成")
        print(f"   成功迁移: {migrated_count} 个MCP工具")
        print(f"   跳过已存在: {skipped_count} 个")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("开始迁移MCP工具到统一工具表...")
    migrate_mcp_to_tools()
