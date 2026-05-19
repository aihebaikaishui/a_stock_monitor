"""通知推送模块"""
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)

FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/d7ef5fc7-3013-45d2-b5ec-747b5208afc8"


class NotifyManager:
    """通知管理类"""
    
    @staticmethod
    def show_page_notification(message: str, notification_type: str = 'info'):
        """显示页面内通知
        notification_type: info, success, warning, error
        """
        if notification_type == 'success':
            st.success(message)
        elif notification_type == 'warning':
            st.warning(message)
        elif notification_type == 'error':
            st.error(message)
        else:
            st.info(message)
    
    @staticmethod
    def show_toast(message: str, icon: str = "ℹ️"):
        """显示Toast通知"""
        st.toast(message, icon=icon)
    
    @staticmethod
    def send_email(subject: str, content: str, 
                   smtp_host: str, smtp_port: int, 
                   smtp_user: str, smtp_password: str, 
                   to_email: str) -> bool:
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    @staticmethod
    def send_feishu_notification(title: str, content: str, action: str = "买入") -> bool:
        """发送飞书机器人加急通知"""
        try:
            icon = "🚨" if action == "卖出" else "🎯"
            
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": f"{icon} {title}"
                        },
                        "template": "red" if action == "卖出" else "orange"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": content
                            }
                        },
                        {
                            "tag": "hr"
                        },
                        {
                            "tag": "note",
                            "elements": [
                                {
                                    "tag": "plain_text",
                                    "content": "A股盯盘助手"
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"飞书通知发送成功: {title}")
                return True
            else:
                logger.error(f"飞书通知发送失败: {result}")
                return False
        
        except Exception as e:
            logger.error(f"飞书通知发送异常: {e}")
            return False
    
    @staticmethod
    def send_trigger_notification(trigger: Dict, email_config: Optional[Dict] = None):
        """发送触发通知
        trigger: 触发信息字典
        email_config: 邮件配置
        """
        action = "卖出" if trigger['type'] == 'sell' else "买入"
        
        message = f"**{trigger['name']}**({trigger['code']})\n\n"
        message += f"📊 当前价格: **{trigger['price']:.2f} 元**\n"
        message += f"⚡ 触发原因: {trigger['reason']}\n"
        message += f"💡 建议操作: **{'高抛' if trigger['type'] == 'sell' else '低吸'}**"
        
        title = f"【{action}提醒】{trigger['name']}"
        
        NotifyManager.show_toast(f"{title} {trigger['price']:.2f}元", icon="📢")
        NotifyManager.show_page_notification(message, notification_type='warning')
        
        NotifyManager.send_feishu_notification(title, message, action)
        
        if email_config and email_config.get('enabled'):
            NotifyManager.send_email(
                subject=f"【A股盯盘助手】{action}提醒 - {trigger['name']}",
                content=message.replace('**', '').replace('*', ''),
                smtp_host=email_config.get('smtp_host'),
                smtp_port=email_config.get('smtp_port', 587),
                smtp_user=email_config.get('smtp_user'),
                smtp_password=email_config.get('smtp_password'),
                to_email=email_config.get('to_email')
            )
