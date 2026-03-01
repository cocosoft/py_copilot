"""
Agent系统初始化脚本

本脚本用于初始化新的Agent系统，将11个官方智能体注册到注册中心
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.agents.registry import agent_registry
from app.agents.official import OFFICIAL_AGENTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_agent_system(db: Session = None):
    """
    初始化Agent系统

    Args:
        db: 数据库会话（可选，用于后续扩展）
    """
    logger.info("开始初始化Agent系统...")

    # 清空现有注册
    agent_registry.clear()
    logger.info("已清空Agent注册表")

    # 注册所有官方智能体
    registered_count = 0
    failed_count = 0

    for agent_class in OFFICIAL_AGENTS:
        try:
            config = agent_class.DEFAULT_CONFIG

            # 注册Agent（延迟实例化）
            success = agent_registry.register(
                agent_class=agent_class,
                config=config,
                create_instance=False
            )

            if success:
                logger.info(f"✓ 注册Agent: {config.name}")
                registered_count += 1
            else:
                logger.error(f"✗ 注册Agent失败: {config.name}")
                failed_count += 1

        except Exception as e:
            logger.error(f"✗ 注册Agent异常: {agent_class.__name__}, 错误: {e}")
            failed_count += 1

    # 打印统计
    logger.info("\nAgent系统初始化完成!")
    logger.info(f"  - 成功注册: {registered_count} 个")
    logger.info(f"  - 注册失败: {failed_count} 个")

    # 打印注册中心统计
    stats = agent_registry.get_registry_stats()
    logger.info(f"\n注册中心统计:")
    logger.info(f"  - 总Agent数: {stats['total_agents']}")
    logger.info(f"  - 激活Agent: {stats['active_agents']}")

    return registered_count, failed_count


def verify_agent_system():
    """验证Agent系统"""
    logger.info("\n验证Agent系统...")

    # 列出所有Agent
    agents = agent_registry.list_agents()
    logger.info(f"已注册Agent列表 ({len(agents)} 个):")

    for agent_name in agents:
        config = agent_registry.get_agent_config(agent_name)
        if config:
            logger.info(f"  - {agent_name}: {config.description[:50]}...")

    # 验证所有官方Agent
    expected_agents = [
        "聊天助手", "翻译专家", "语音识别助手",
        "知识库搜索", "Web搜索助手", "图片生成器",
        "图像识别专家", "视频生成器", "视频分析专家",
        "文字转语音", "语音转文字"
    ]

    missing = set(expected_agents) - set(agents)
    if missing:
        logger.warning(f"缺失的Agent: {missing}")
        return False

    logger.info("✓ 所有官方Agent已正确注册")
    return True


def test_agent_execution():
    """测试Agent执行"""
    logger.info("\n测试Agent执行...")

    import asyncio

    async def run_test():
        # 测试聊天助手
        chat_agent = agent_registry.get_agent("聊天助手")
        if chat_agent:
            result = await chat_agent.run("你好")
            logger.info(f"聊天助手测试: {'成功' if result.success else '失败'}")

        # 测试翻译专家
        translate_agent = agent_registry.get_agent("翻译专家")
        if translate_agent:
            result = await translate_agent.run({"text": "Hello", "target_lang": "zh"})
            logger.info(f"翻译专家测试: {'成功' if result.success else '失败'}")

    try:
        asyncio.run(run_test())
        logger.info("✓ Agent执行测试完成")
        return True
    except Exception as e:
        logger.error(f"✗ Agent执行测试失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Agent系统初始化")
    logger.info("=" * 50)

    db = SessionLocal()
    try:
        # 初始化Agent系统
        registered, failed = init_agent_system(db)

        # 验证系统
        verified = verify_agent_system()

        # 测试执行
        tested = test_agent_execution()

        # 总结
        logger.info("\n" + "=" * 50)
        logger.info("初始化总结")
        logger.info("=" * 50)
        logger.info(f"注册: {registered} 成功, {failed} 失败")
        logger.info(f"验证: {'通过' if verified else '未通过'}")
        logger.info(f"测试: {'通过' if tested else '未通过'}")

        if registered == 11 and verified and tested:
            logger.info("\n✓ Agent系统初始化成功!")
            return 0
        else:
            logger.warning("\n⚠ Agent系统初始化存在问题")
            return 1

    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
