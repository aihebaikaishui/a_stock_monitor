"""认证模块"""
import streamlit as st
from supabase import Client
from lib.supabase_client import get_supabase_client


class AuthManager:
    """认证管理类"""
    
    @staticmethod
    def sign_up(email: str, password: str) -> tuple[bool, str]:
        """用户注册"""
        try:
            supabase: Client = get_supabase_client()
            result = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            if result.user:
                return True, "注册成功！请查收验证邮件。"
            return False, "注册失败"
        except Exception as e:
            return False, f"注册失败: {str(e)}"
    
    @staticmethod
    def sign_in(email: str, password: str) -> tuple[bool, str]:
        """用户登录"""
        try:
            supabase: Client = get_supabase_client()
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if result.user:
                return True, "登录成功"
            return False, "登录失败"
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                return False, "登录超时，请检查网络连接"
            return False, f"登录失败: {error_msg}"
    
    @staticmethod
    def sign_out() -> bool:
        """用户登出"""
        try:
            supabase: Client = get_supabase_client()
            supabase.auth.sign_out()
            return True
        except Exception:
            return False
    
    @staticmethod
    def reset_password(email: str) -> tuple[bool, str]:
        """发送密码重置邮件"""
        try:
            supabase: Client = get_supabase_client()
            supabase.auth.reset_password_email(email)
            return True, "密码重置邮件已发送，请查收"
        except Exception as e:
            return False, f"发送失败: {str(e)}"
    
    @staticmethod
    def get_current_user():
        """获取当前登录用户"""
        try:
            supabase: Client = get_supabase_client()
            session = supabase.auth.get_session()
            if session and session.user:
                return session.user
            return None
        except Exception:
            return None
    
    @staticmethod
    def is_authenticated() -> bool:
        """检查是否已登录"""
        return AuthManager.get_current_user() is not None


def init_auth_state():
    """初始化认证状态"""
    user = AuthManager.get_current_user()
    st.session_state.user = user
    st.session_state.is_authenticated = user is not None


def require_auth():
    """要求用户已登录，否则显示登录页面"""
    init_auth_state()
    
    if not st.session_state.is_authenticated:
        show_login_page()
        st.stop()
    
    return st.session_state.user


def show_login_page():
    """显示登录/注册页面"""
    st.title("🎯 A股盯盘助手")
    
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("🔐 登录账号")
            email = st.text_input("邮箱", placeholder="your@email.com")
            password = st.text_input("密码", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("登录", use_container_width=True, type="primary")
            with col2:
                reset_clicked = st.form_submit_button("找回密码", use_container_width=True)
            
            if reset_clicked and email:
                with st.spinner("发送中..."):
                    success, message = AuthManager.reset_password(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            elif reset_clicked and not email:
                st.warning("请输入邮箱")
            
            if submitted and email and password:
                st.info("正在连接服务器...")
                success, message = AuthManager.sign_in(email, password)
                if success:
                    st.success(message)
                    st.session_state.is_authenticated = True
                    st.session_state.user = AuthManager.get_current_user()
                    st.rerun()
                else:
                    st.error(message)
    
    with tab2:
        with st.form("register_form"):
            st.subheader("📝 注册账号")
            email = st.text_input("邮箱", placeholder="your@email.com", key="register_email")
            password = st.text_input("密码", type="password", key="register_password")
            confirm_password = st.text_input("确认密码", type="password")
            
            submitted = st.form_submit_button("注册", use_container_width=True, type="primary")
            
            if submitted:
                if not email or not password:
                    st.error("请填写所有字段")
                elif password != confirm_password:
                    st.error("两次密码输入不一致")
                elif len(password) < 6:
                    st.error("密码长度至少6位")
                else:
                    with st.spinner("注册中..."):
                        success, message = AuthManager.sign_up(email, password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
    
    st.markdown("---")
    st.caption("💡 登录后即可开始使用 A股盯盘助手")


def show_user_info(user):
    """显示用户信息"""
    if user:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.info(f"👤 {user.email}")
        with col2:
            if st.button("退出登录", use_container_width=True):
                AuthManager.sign_out()
                st.session_state.user = None
                st.session_state.is_authenticated = False
                st.rerun()
