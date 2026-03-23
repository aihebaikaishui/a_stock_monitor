"""通知推送模块"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)


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
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 连接SMTP服务器
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
    def send_trigger_notification(trigger: Dict, email_config: Optional[Dict] = None):
        """发送触发通知
        trigger: 触发信息字典
        email_config: 邮件配置
        """
        # 确定操作类型
        action = "卖出" if trigger['type'] == 'sell' else "买入"
        
        # 构造消息
        message = f"【{action}提醒】{trigger['name']}({trigger['code']})\n"
        message += f"当前价格: {trigger['price']:.2f} 元\n"
        message += f"触发原因: {trigger['reason']}\n"
        message += f"建议操作: {'高抛' if trigger['type'] == 'sell' else '低吸'}"
        
        # 显示页面通知
        NotifyManager.show_toast(message, icon="📢")
        NotifyManager.show_page_notification(message, notification_type='warning')
        
        # 发送邮件
        if email_config and email_config.get('enabled'):
            NotifyManager.send_email(
                subject=f"【A股盯盘助手】{action}提醒 - {trigger['name']}",
                content=message,
                smtp_host=email_config.get('smtp_host'),
                smtp_port=email_config.get('smtp_port', 587),
                smtp_user=email_config.get('smtp_user'),
                smtp_password=email_config.get('smtp_password'),
                to_email=email_config.get('to_email')
            )
