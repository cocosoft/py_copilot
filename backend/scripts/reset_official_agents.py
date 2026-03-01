#!/usr/bin/env python3
"""
重置官方智能体脚本
此脚本用于删除所有非官方智能体，并重新初始化官方智能体数据
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.agent import Agent
from app.models.agent_category import AgentCategory


def delete_non_official_agents(db: Session):
    """删除所有非官方智能体
    
    Args:
        db: 数据库会话
    """
    print("开始删除非官方智能体...")
    
    # 查询所有非官方智能体（is_official != True 或 is_official is None）
    non_official_agents = db.query(Agent).filter(
        (Agent.is_official == False) | (Agent.is_official == None)
    ).all()
    
    deleted_count = 0
    for agent in non_official_agents:
        try:
            agent_name = agent.name
            agent_id = agent.id
            
            # 软删除
            from datetime import datetime
            agent.is_deleted = True
            agent.deleted_at = datetime.now()
            
            db.commit()
            print(f"✓ 删除智能体: {agent_name} (ID: {agent_id})")
            deleted_count += 1
            
        except Exception as e:
            db.rollback()
            print(f"✗ 删除智能体 {agent.name} 失败: {e}")
    
    print(f"共删除 {deleted_count} 个非官方智能体\n")
    return deleted_count


def delete_official_agents(db: Session):
    """删除所有官方智能体（用于重新创建）
    
    Args:
        db: 数据库会话
    """
    print("开始删除现有官方智能体...")
    
    # 查询所有官方智能体
    official_agents = db.query(Agent).filter(
        Agent.is_official == True
    ).all()
    
    deleted_count = 0
    for agent in official_agents:
        try:
            agent_name = agent.name
            agent_id = agent.id
            
            # 软删除
            from datetime import datetime
            agent.is_deleted = True
            agent.deleted_at = datetime.now()
            
            db.commit()
            print(f"✓ 删除官方智能体: {agent_name} (ID: {agent_id})")
            deleted_count += 1
            
        except Exception as e:
            db.rollback()
            print(f"✗ 删除官方智能体 {agent.name} 失败: {e}")
    
    print(f"共删除 {deleted_count} 个官方智能体\n")
    return deleted_count


def get_or_create_official_category(db: Session) -> AgentCategory:
    """获取或创建官方智能体分类
    
    Args:
        db: 数据库会话
        
    Returns:
        官方智能体分类对象
    """
    category = db.query(AgentCategory).filter(
        AgentCategory.name == "官方智能体"
    ).first()
    
    if not category:
        category = AgentCategory(
            name="官方智能体",
            logo="official_agents.svg",
            is_system=True
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        print(f"✓ 创建分类: {category.name} (ID: {category.id})")
    
    return category


def create_official_agents(db: Session):
    """初始化官方智能体数据
    
    Args:
        db: 数据库会话
    """
    print("开始创建官方智能体...")
    
    # 获取或创建官方智能体分类
    category = get_or_create_official_category(db)
    
    # 定义官方智能体数据
    official_agents = [
        {
            "name": "聊天助手",
            "description": "通用对话智能体，可以进行日常聊天、回答问题、提供建议等",
            "avatar": "chat_agent.svg",
            "prompt": "你是一个友好、专业的AI助手。请用简洁、清晰的语言回答用户的问题。如果用户的问题不够明确，请主动询问以获取更多信息。",
            "agent_type": "single",
            "template_category": "chat"
        },
        {
            "name": "翻译专家",
            "description": "专业的多语言翻译智能体，支持各种语言之间的互译",
            "avatar": "translate_agent.svg",
            "prompt": "你是一位专业的翻译专家。请将用户提供的文本准确翻译成目标语言，保持原文的语气和风格。对于专业术语，请提供适当的翻译。如果用户没有指定目标语言，请询问用户需要翻译成哪种语言。",
            "agent_type": "single",
            "template_category": "translation"
        },
        {
            "name": "语音识别助手",
            "description": "将语音转换为文本的智能体，支持多种语言和方言",
            "avatar": "speech_recognition_agent.svg",
            "prompt": "你是一个语音识别助手。当用户上传音频文件时，你需要将语音内容转换为文本。请尽可能准确地识别语音内容，并标注说话人的情绪和语气。如果音频质量不佳，请提示用户。",
            "agent_type": "single",
            "template_category": "speech"
        },
        {
            "name": "知识库搜索",
            "description": "在知识库中搜索和检索信息的智能体",
            "avatar": "knowledge_search_agent.svg",
            "prompt": "你是一个知识库搜索专家。当用户提出问题时，请在知识库中搜索相关信息，并基于搜索结果提供准确的答案。如果知识库中没有相关信息，请明确告知用户。请引用信息来源，并确保答案的准确性。",
            "agent_type": "single",
            "template_category": "search"
        },
        {
            "name": "Web搜索助手",
            "description": "使用网络搜索获取最新信息的智能体",
            "avatar": "web_search_agent.svg",
            "prompt": "你是一个Web搜索专家。当用户需要获取最新信息或知识库中没有的信息时，请使用网络搜索工具查找相关内容。请综合多个来源的信息，提供全面、准确的答案。请标注信息来源和时间。",
            "agent_type": "single",
            "template_category": "web_search"
        },
        {
            "name": "图片生成器",
            "description": "根据描述生成图片的AI智能体",
            "avatar": "image_generation_agent.svg",
            "prompt": "你是一个图片生成专家。当用户描述他们想要的图片时，请将描述转换为详细的提示词，用于生成高质量的图片。请确保提示词包含风格、光线、构图等细节，以获得最佳效果。",
            "agent_type": "single",
            "template_category": "image_generation"
        },
        {
            "name": "图像识别专家",
            "description": "识别和分析图片内容的智能体",
            "avatar": "image_recognition_agent.svg",
            "prompt": "你是一个图像识别专家。当用户上传图片时，请详细描述图片内容，包括物体、场景、人物、文字等信息。如果用户有特定问题关于图片，请针对性回答。请保持客观和准确。",
            "agent_type": "single",
            "template_category": "image_recognition"
        },
        {
            "name": "视频生成器",
            "description": "根据描述生成视频的AI智能体",
            "avatar": "video_generation_agent.svg",
            "prompt": "你是一个视频生成专家。当用户描述他们想要的视频时，请将描述转换为详细的提示词，包括场景、动作、镜头运动、时长等要素，用于生成高质量的视频内容。",
            "agent_type": "single",
            "template_category": "video_generation"
        },
        {
            "name": "视频分析专家",
            "description": "分析视频内容和提取信息的智能体",
            "avatar": "video_analysis_agent.svg",
            "prompt": "你是一个视频分析专家。当用户上传视频时，请分析视频内容，包括场景、人物、动作、对话等。可以生成视频摘要、提取关键帧、识别视频中的物体和事件。如果用户有特定分析需求，请针对性处理。",
            "agent_type": "single",
            "template_category": "video_analysis"
        },
        {
            "name": "文字转语音",
            "description": "将文本转换为自然语音的智能体",
            "avatar": "tts_agent.svg",
            "prompt": "你是一个文字转语音专家。当用户提供文本时，请将其转换为自然流畅的语音。支持多种语言和声音风格选择。请确保语音清晰、语调自然，适合用户的场景需求。",
            "agent_type": "single",
            "template_category": "tts"
        },
        {
            "name": "语音转文字",
            "description": "将语音准确转换为文本的智能体",
            "avatar": "stt_agent.svg",
            "prompt": "你是一个语音转文字专家。当用户上传音频时，请准确地将语音内容转换为文本。支持多种语言和方言识别。请尽可能准确地识别内容，并适当添加标点符号和分段。",
            "agent_type": "single",
            "template_category": "stt"
        }
    ]
    
    # 获取系统用户ID（使用ID为1的用户作为官方智能体创建者）
    system_user_id = 1
    
    created_count = 0
    
    for agent_data in official_agents:
        try:
            # 创建官方智能体
            agent = Agent(
                name=agent_data["name"],
                description=agent_data["description"],
                avatar=agent_data["avatar"],
                prompt=agent_data["prompt"],
                user_id=system_user_id,
                category_id=category.id,
                is_public=True,
                is_recommended=True,
                is_official=True,
                is_template=True,
                agent_type=agent_data["agent_type"],
                template_category=agent_data["template_category"],
                is_deleted=False
            )
            
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            print(f"✓ 创建官方智能体: {agent.name} (ID: {agent.id})")
            created_count += 1
            
        except Exception as e:
            db.rollback()
            print(f"✗ 创建官方智能体 {agent_data['name']} 失败: {e}")
    
    print(f"\n共创建 {created_count} 个官方智能体")


def main():
    """主函数"""
    db = SessionLocal()
    try:
        print("=" * 60)
        print("开始重置智能体数据")
        print("=" * 60 + "\n")
        
        # 第一步：删除所有非官方智能体
        delete_non_official_agents(db)
        
        # 第二步：删除现有官方智能体
        delete_official_agents(db)
        
        # 第三步：重新创建官方智能体
        create_official_agents(db)
        
        print("\n" + "=" * 60)
        print("智能体数据重置完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n重置失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
