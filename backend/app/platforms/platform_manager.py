"""
平台管理器

管理多个平台适配器，处理平台注册、初始化和消息分发
"""
from typing import Dict, Any, List, Optional
import logging
import asyncio
from sqlalchemy.orm import Session

from app.platforms.base import PlatformAdapter, Message
from app.models.platform_config import PlatformConfig

logger = logging.getLogger(__name__)


class PlatformManager:
    """平台管理器"""
    
    def __init__(self, db_session: Session):
        """初始化平台管理器
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.adapters: Dict[str, PlatformAdapter] = {}
        self.platform_configs: Dict[str, Dict[str, Any]] = {}
        logger.info("平台管理器已初始化")
    
    def register_platform(self, platform_name: str, adapter_class, config: Dict[str, Any]):
        """注册平台
        
        Args:
            platform_name: 平台名称
            adapter_class: 适配器类
            config: 平台配置
            
        Returns:
            是否成功
        """
        try:
            # 创建适配器实例
            adapter = adapter_class(platform_name, config)
            
            # 验证配置
            if not adapter.validate_config():
                logger.error(f"平台配置无效: {platform_name}")
                return False
            
            # 注册适配器
            self.adapters[platform_name] = adapter
            self.platform_configs[platform_name] = config
            
            # 保存配置到数据库
            self._save_platform_config(platform_name, config)
            
            logger.info(f"平台已注册: {platform_name}")
            return True
        except Exception as e:
            logger.error(f"注册平台失败: {platform_name}, 错误: {str(e)}")
            return False
    
    def connect_platform(self, platform_name: str) -> bool:
        """连接平台
        
        Args:
            platform_name: 平台名称
            
        Returns:
            是否成功
        """
        if platform_name not in self.adapters:
            logger.error(f"平台未注册: {platform_name}")
            return False
        
        try:
            adapter = self.adapters[platform_name]
            success = adapter.connect()
            if success:
                logger.info(f"平台已连接: {platform_name}")
            else:
                logger.error(f"平台连接失败: {platform_name}")
            return success
        except Exception as e:
            logger.error(f"连接平台失败: {platform_name}, 错误: {str(e)}")
            return False
    
    def connect_all_platforms(self) -> Dict[str, bool]:
        """连接所有平台
        
        Returns:
            平台连接状态字典
        """
        results = {}
        for platform_name in self.adapters:
            results[platform_name] = self.connect_platform(platform_name)
        return results
    
    def disconnect_platform(self, platform_name: str) -> bool:
        """断开平台连接
        
        Args:
            platform_name: 平台名称
            
        Returns:
            是否成功
        """
        if platform_name not in self.adapters:
            logger.error(f"平台未注册: {platform_name}")
            return False
        
        try:
            adapter = self.adapters[platform_name]
            success = adapter.disconnect()
            if success:
                logger.info(f"平台已断开: {platform_name}")
            else:
                logger.error(f"平台断开失败: {platform_name}")
            return success
        except Exception as e:
            logger.error(f"断开平台失败: {platform_name}, 错误: {str(e)}")
            return False
    
    def disconnect_all_platforms(self) -> Dict[str, bool]:
        """断开所有平台连接
        
        Returns:
            平台断开状态字典
        """
        results = {}
        for platform_name in self.adapters:
            results[platform_name] = self.disconnect_platform(platform_name)
        return results
    
    def send_message(self, platform_name: str, user_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """发送消息
        
        Args:
            platform_name: 平台名称
            user_id: 用户ID
            content: 消息内容
            metadata: 元数据
            
        Returns:
            是否成功
        """
        if platform_name not in self.adapters:
            logger.error(f"平台未注册: {platform_name}")
            return False
        
        try:
            adapter = self.adapters[platform_name]
            if not adapter.get_connection_status():
                # 尝试重新连接
                if not adapter.connect():
                    logger.error(f"平台未连接: {platform_name}")
                    return False
            
            success = adapter.send_message(user_id, content, metadata)
            if success:
                logger.info(f"消息已发送到平台 {platform_name}, 用户 {user_id}")
            else:
                logger.error(f"消息发送失败: {platform_name}, 用户 {user_id}")
            return success
        except Exception as e:
            logger.error(f"发送消息失败: {platform_name}, 用户 {user_id}, 错误: {str(e)}")
            return False
    
    def broadcast_message(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, bool]:
        """广播消息到所有平台
        
        Args:
            content: 消息内容
            metadata: 元数据
            
        Returns:
            平台发送状态字典
        """
        results = {}
        for platform_name, adapter in self.adapters.items():
            if adapter.get_connection_status():
                # 这里简化处理，实际应该为每个平台指定用户ID
                # 或者根据平台类型获取默认用户
                user_id = metadata.get(f"{platform_name}_user_id") or "default"
                results[platform_name] = adapter.send_message(user_id, content, metadata)
            else:
                results[platform_name] = False
        return results
    
    def receive_messages(self, platform_name: str = None) -> List[Message]:
        """接收消息
        
        Args:
            platform_name: 平台名称，None表示所有平台
            
        Returns:
            消息列表
        """
        messages = []
        
        if platform_name:
            # 接收指定平台的消息
            if platform_name in self.adapters:
                adapter = self.adapters[platform_name]
                if adapter.get_connection_status():
                    try:
                        platform_messages = adapter.receive_messages()
                        messages.extend(platform_messages)
                    except Exception as e:
                        logger.error(f"接收消息失败: {platform_name}, 错误: {str(e)}")
        else:
            # 接收所有平台的消息
            for platform_name, adapter in self.adapters.items():
                if adapter.get_connection_status():
                    try:
                        platform_messages = adapter.receive_messages()
                        messages.extend(platform_messages)
                    except Exception as e:
                        logger.error(f"接收消息失败: {platform_name}, 错误: {str(e)}")
        
        logger.info(f"接收到 {len(messages)} 条消息")
        return messages
    
    async def start_message_listener(self, interval: int = 5):
        """启动消息监听器
        
        Args:
            interval: 监听间隔（秒）
        """
        logger.info(f"启动消息监听器，间隔: {interval}秒")
        
        while True:
            try:
                # 接收消息
                messages = self.receive_messages()
                
                # 处理消息
                for message in messages:
                    await self._process_message(message)
                
                # 等待下一次轮询
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"消息监听器错误: {str(e)}")
                await asyncio.sleep(interval)
    
    async def _process_message(self, message: Message):
        """处理消息
        
        Args:
            message: 消息
        """
        # 这里可以实现消息处理逻辑
        # 例如，将消息路由到对应的智能体
        logger.info(f"处理消息: 平台={message.platform}, 用户={message.user_id}, 内容={message.content[:50]}...")
        
        # 示例：回复消息
        response = f"收到您的消息: {message.content[:100]}"
        self.send_message(message.platform, message.user_id, response)
    
    def get_platforms(self) -> List[str]:
        """获取已注册的平台
        
        Returns:
            平台名称列表
        """
        return list(self.adapters.keys())
    
    def get_platform_status(self) -> Dict[str, bool]:
        """获取平台状态
        
        Returns:
            平台状态字典
        """
        status = {}
        for platform_name, adapter in self.adapters.items():
            status[platform_name] = adapter.get_connection_status()
        return status
    
    def get_platform_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """获取平台配置
        
        Args:
            platform_name: 平台名称
            
        Returns:
            平台配置
        """
        return self.platform_configs.get(platform_name)
    
    def update_platform_config(self, platform_name: str, config: Dict[str, Any]) -> bool:
        """更新平台配置
        
        Args:
            platform_name: 平台名称
            config: 新配置
            
        Returns:
            是否成功
        """
        if platform_name not in self.adapters:
            logger.error(f"平台未注册: {platform_name}")
            return False
        
        try:
            adapter = self.adapters[platform_name]
            adapter.update_config(config)
            
            # 验证新配置
            if not adapter.validate_config():
                logger.error(f"新配置无效: {platform_name}")
                return False
            
            # 更新配置
            self.platform_configs[platform_name] = config
            
            # 保存配置到数据库
            self._save_platform_config(platform_name, config)
            
            logger.info(f"平台配置已更新: {platform_name}")
            return True
        except Exception as e:
            logger.error(f"更新平台配置失败: {platform_name}, 错误: {str(e)}")
            return False
    
    def load_platforms_from_config(self):
        """从数据库加载平台"""
        # 从数据库加载平台配置
        logger.info("从数据库加载平台")
        
        # 查询所有激活的平台配置
        platform_configs = self.db.query(PlatformConfig).filter(
            PlatformConfig.is_active == True
        ).all()
        
        for platform_config in platform_configs:
            platform_name = platform_config.platform_name
            config_data = platform_config.config_data
            
            # 这里应该导入具体的平台适配器类
            # 示例：加载飞书平台
            if platform_name == "feishu":
                # from app.platforms.feishu import FeishuAdapter
                # self.register_platform("feishu", FeishuAdapter, config_data)
                pass
            # 示例：加载微信平台
            elif platform_name == "wechat":
                # from app.platforms.wechat import WechatAdapter
                # self.register_platform("wechat", WechatAdapter, config_data)
                pass
            # 示例：加载Telegram平台
            elif platform_name == "telegram":
                # from app.platforms.telegram import TelegramAdapter
                # self.register_platform("telegram", TelegramAdapter, config_data)
                pass
            
            logger.info(f"已加载平台配置: {platform_name}")
    
    def _save_platform_config(self, platform_name: str, config: Dict[str, Any]):
        """保存平台配置到数据库
        
        Args:
            platform_name: 平台名称
            config: 配置数据
        """
        try:
            # 查找现有配置
            existing_config = self.db.query(PlatformConfig).filter(
                PlatformConfig.platform_name == platform_name
            ).first()
            
            if existing_config:
                # 更新现有配置
                existing_config.config_data = config
                existing_config.is_active = True
            else:
                # 创建新配置
                new_config = PlatformConfig(
                    platform_name=platform_name,
                    config_data=config,
                    is_active=True
                )
                self.db.add(new_config)
            
            self.db.commit()
            logger.info(f"平台配置已保存: {platform_name}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存平台配置失败: {platform_name}, 错误: {str(e)}")
    
    def _load_platform_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """从数据库加载平台配置
        
        Args:
            platform_name: 平台名称
            
        Returns:
            配置数据
        """
        try:
            config = self.db.query(PlatformConfig).filter(
                PlatformConfig.platform_name == platform_name,
                PlatformConfig.is_active == True
            ).first()
            
            if config:
                return config.config_data
            return None
        except Exception as e:
            logger.error(f"加载平台配置失败: {platform_name}, 错误: {str(e)}")
            return None
