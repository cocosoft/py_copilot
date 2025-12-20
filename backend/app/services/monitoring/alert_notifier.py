"""告警通知器模块"""
import smtplib
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from app.core.config import settings
from app.services.monitoring.monitoring_service import Alert

logger = logging.getLogger(__name__)

class AlertNotifier:
    """告警通知器"""
    
    def __init__(self):
        self.email_config = self._get_email_config()
        self.dingtalk_config = self._get_dingtalk_config()
        self.webhook_config = self._get_webhook_config()
    
    def _get_email_config(self) -> Optional[Dict[str, str]]:
        """获取邮件配置"""
        if (hasattr(settings, 'SMTP_SERVER') and 
            hasattr(settings, 'SMTP_PORT') and
            hasattr(settings, 'SMTP_USERNAME') and
            hasattr(settings, 'SMTP_PASSWORD') and
            hasattr(settings, 'ALERT_EMAIL_RECIPIENTS')):
            
            return {
                'server': settings.SMTP_SERVER,
                'port': settings.SMTP_PORT,
                'username': settings.SMTP_USERNAME,
                'password': settings.SMTP_PASSWORD,
                'recipients': settings.ALERT_EMAIL_RECIPIENTS.split(',')
            }
        return None
    
    def _get_dingtalk_config(self) -> Optional[Dict[str, str]]:
        """获取钉钉配置"""
        if hasattr(settings, 'DINGTALK_WEBHOOK_URL'):
            return {
                'webhook_url': settings.DINGTALK_WEBHOOK_URL
            }
        return None
    
    def _get_webhook_config(self) -> Optional[Dict[str, str]]:
        """获取Webhook配置"""
        if hasattr(settings, 'ALERT_WEBHOOK_URL'):
            return {
                'url': settings.ALERT_WEBHOOK_URL
            }
        return None
    
    def notify(self, alert: Alert, channels: List[str] = None):
        """发送告警通知"""
        if channels is None:
            channels = ['log']  # 默认只记录日志
        
        for channel in channels:
            try:
                if channel == 'email' and self.email_config:
                    self._send_email(alert)
                elif channel == 'dingtalk' and self.dingtalk_config:
                    self._send_dingtalk(alert)
                elif channel == 'webhook' and self.webhook_config:
                    self._send_webhook(alert)
                elif channel == 'log':
                    self._log_alert(alert)
            except Exception as e:
                logger.error(f"发送告警通知失败 (渠道: {channel}): {str(e)}")
    
    def _send_email(self, alert: Alert):
        """发送邮件告警"""
        if not self.email_config:
            return
        
        # 创建邮件内容
        subject = f"[{alert.level.value.upper()}] 系统告警 - {alert.rule_name}"
        
        body = f"""
        <h2>系统告警通知</h2>
        
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr><td style="padding: 8px; background-color: #f5f5f5;"><strong>告警级别</strong></td><td style="padding: 8px;">{alert.level.value.upper()}</td></tr>
            <tr><td style="padding: 8px; background-color: #f5f5f5;"><strong>告警类型</strong></td><td style="padding: 8px;">{alert.type.value}</td></tr>
            <tr><td style="padding: 8px; background-color: #f5f5f5;"><strong>规则名称</strong></td><td style="padding: 8px;">{alert.rule_name}</td></tr>
            <tr><td style="padding: 8px; background-color: #f5f5f5;"><strong>触发时间</strong></td><td style="padding: 8px;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            <tr><td style="padding: 8px; background-color: #f5f5f5;"><strong>指标值</strong></td><td style="padding: 8px;">{alert.metric_value}</td></tr>
            <tr><td style="padding: 8px; background-color: #f5f5f5;"><strong>阈值</strong></td><td style="padding: 8px;">{alert.threshold}</td></tr>
            <tr><td style="padding: 8px; background-color: #f5f5f5;"><strong>告警信息</strong></td><td style="padding: 8px;">{alert.message}</td></tr>
        </table>
        
        <p><em>此邮件由系统自动发送，请勿回复。</em></p>
        """
        
        # 创建邮件消息
        msg = MIMEMultipart()
        msg['From'] = self.email_config['username']
        msg['To'] = ', '.join(self.email_config['recipients'])
        msg['Subject'] = subject
        
        # 添加HTML内容
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # 发送邮件
        with smtplib.SMTP(self.email_config['server'], self.email_config['port']) as server:
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
        
        logger.info(f"邮件告警发送成功: {alert.rule_name}")
    
    def _send_dingtalk(self, alert: Alert):
        """发送钉钉告警"""
        if not self.dingtalk_config:
            return
        
        # 根据告警级别设置颜色
        color_map = {
            'info': '#1890FF',
            'warning': '#FAAD14',
            'error': '#FF4D4F',
            'critical': '#CF1322'
        }
        
        # 创建钉钉消息
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"系统告警 - {alert.level.value.upper()}",
                "text": f"""
## 🚨 系统告警通知

**告警级别**: {alert.level.value.upper()}  
**告警类型**: {alert.type.value}  
**规则名称**: {alert.rule_name}  
**触发时间**: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**指标值**: {alert.metric_value}  
**阈值**: {alert.threshold}  

**告警信息**: {alert.message}

---
*此消息由系统自动发送*
                """
            },
            "at": {
                "isAtAll": alert.level.value in ['error', 'critical']
            }
        }
        
        # 发送钉钉消息
        response = requests.post(
            self.dingtalk_config['webhook_url'],
            json=message,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"钉钉告警发送成功: {alert.rule_name}")
        else:
            logger.error(f"钉钉告警发送失败: {response.status_code} - {response.text}")
    
    def _send_webhook(self, alert: Alert):
        """发送Webhook告警"""
        if not self.webhook_config:
            return
        
        # 创建Webhook数据
        webhook_data = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "level": alert.level.value,
            "type": alert.type.value,
            "message": alert.message,
            "metric_value": alert.metric_value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp.isoformat(),
            "resolved": alert.resolved
        }
        
        # 发送Webhook请求
        response = requests.post(
            self.webhook_config['url'],
            json=webhook_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Webhook告警发送成功: {alert.rule_name}")
        else:
            logger.error(f"Webhook告警发送失败: {response.status_code} - {response.text}")
    
    def _log_alert(self, alert: Alert):
        """记录告警日志"""
        log_level = {
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error,
            'critical': logger.critical
        }
        
        log_func = log_level.get(alert.level.value, logger.warning)
        log_func(f"告警通知 - {alert.level.value.upper()}: {alert.message}")

class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notifier = AlertNotifier()
        self.notification_rules = self._setup_notification_rules()
    
    def _setup_notification_rules(self) -> Dict[str, List[str]]:
        """设置通知规则"""
        return {
            'info': ['log'],
            'warning': ['log', 'email'],
            'error': ['log', 'email', 'dingtalk'],
            'critical': ['log', 'email', 'dingtalk', 'webhook']
        }
    
    def send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        channels = self.notification_rules.get(alert.level.value, ['log'])
        self.notifier.notify(alert, channels)
    
    def send_resolution_notification(self, alert: Alert):
        """发送告警解决通知"""
        if not alert.resolved_at:
            return
        
        # 创建解决通知消息
        resolution_alert = Alert(
            id=f"resolved_{alert.id}",
            rule_name=alert.rule_name,
            level=AlertLevel.INFO,
            type=alert.type,
            message=f"告警已解决: {alert.message}",
            metric_value=alert.metric_value,
            threshold=alert.threshold,
            timestamp=alert.resolved_at,
            resolved=True
        )
        
        # 发送解决通知
        self.notifier.notify(resolution_alert, ['log', 'email'])