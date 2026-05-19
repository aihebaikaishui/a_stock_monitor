"""A股盯盘助手 - 主程序"""
import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from streamlit_autorefresh import st_autorefresh

from lib.stock import StockData
from lib.data_manager import DataManager
from lib.strategy import StrategyChecker
from lib.notify import NotifyManager
from lib.auth import require_auth, show_user_info, init_auth_state
from lib.supabase_client import get_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="A股盯盘助手",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'notifications' not in st.session_state:
    st.session_state.notifications = []


def display_stock_list():
    stocks = DataManager.load_stocks()
    
    if not stocks:
        st.info("📌 暂无监控标的，请先添加股票")
        return
    
    codes = [stock['code'] for stock in stocks]
    realtime_data = StockData.get_realtime_data(codes)
    
    price_dict = {}
    for _, row in realtime_data.iterrows():
        code = f"{int(row['代码']):06d}"
        price_dict[code] = {
            'name': row['名称'],
            'price': row['最新价'],
            'change_percent': row['涨跌幅']
        }
    
    display_data = []
    for stock in stocks:
        code = stock['code']
        
        if code in price_dict:
            info = price_dict[code]
            current_price = info['price']
            change_percent = info['change_percent']
            
            cost_price = stock.get('cost_price', 0)
            if cost_price > 0:
                profit = (current_price - cost_price) * stock.get('quantity', 0)
                profit_percent = (current_price - cost_price) / cost_price * 100
            else:
                profit = 0
                profit_percent = 0
            
            status_map = {
                'wait_sell': '⏳ 等待卖出',
                'wait_buy': '⏰ 等待买入'
            }
            
            display_data.append({
                'ID': stock['id'],
                '代码': code,
                '名称': info['name'],
                '成本价': f"{cost_price:.2f}",
                '当前价': f"{current_price:.2f}",
                '涨跌幅': f"{change_percent:+.2f}%",
                '盈亏': f"{profit:+.2f}",
                '盈亏%': f"{profit_percent:+.2f}%",
                '状态': status_map.get(stock['status'], stock['status'])
            })
    
    if display_data:
        df = pd.DataFrame(display_data)
        
        def color_change(val):
            if isinstance(val, str):
                num = float(val.replace('%', '').replace('+', ''))
                if num > 0:
                    return 'color: red'
                elif num < 0:
                    return 'color: green'
            return ''
        
        st.dataframe(
            df.style.applymap(color_change, subset=['涨跌幅']),
            use_container_width=True,
            hide_index=True
        )
        
        total_profit = sum(float(d['盈亏'].replace('+', '')) for d in display_data)
        st.metric("总盈亏", f"{total_profit:+.2f} 元", 
                 delta=f"{'盈利' if total_profit >= 0 else '亏损'} {abs(total_profit):.2f} 元")


def check_triggers():
    stocks = DataManager.load_stocks()
    codes = [stock['code'] for stock in stocks]
    
    if not codes:
        return
    
    realtime_data = StockData.get_realtime_data(codes)
    triggers = StrategyChecker.check_all_strategies(stocks, realtime_data)
    
    for trigger in triggers:
        NotifyManager.send_trigger_notification(trigger)
        DataManager.add_trigger(trigger)
        DataManager.update_stock_status(trigger['stock_id'], 'completed')


def handle_auth_callback():
    """处理 Supabase 邮件验证等回调"""
    try:
        supabase = get_supabase_client()
        current_url = getattr(st.context, 'url', None)
        if current_url and '#' in current_url:
            supabase.auth.initialize_from_url(current_url)
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        logger.debug(f"Auth callback处理: {e}")


def main():
    current_url = getattr(st.context, 'url', None)
    if current_url and ('#' in current_url or (st.query_params and any(k in st.query_params for k in ['access_token', 'error_description']))):
        handle_auth_callback()
        return
    
    init_auth_state()
    user = require_auth()
    
    st.title("📈 A股盯盘助手")
    
    with st.sidebar:
        st.header("导航")
        
        page = st.radio(
            "选择功能",
            ["监控面板", "标的管理", "策略配置", "提醒记录"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        show_user_info(user)
        st.markdown("---")
        st.caption(f"最后刷新: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
        
        if st.button("🔄 刷新数据", use_container_width=True):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    if page == "监控面板":
        st.header("监控面板")
        st.subheader("持仓标的")
        display_stock_list()
        
        st.markdown("---")
        
        with st.expander("⚙️ 自动刷新设置", expanded=False):
            auto_refresh = st.checkbox("启用自动刷新", value=False)
            if auto_refresh:
                refresh_interval = st.slider("刷新间隔(秒)", 10, 300, 60)
                st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh")
        
        check_triggers()
    
    elif page == "标的管理":
        exec(open('pages/1_标的管理.py', encoding='utf-8').read())
    
    elif page == "策略配置":
        exec(open('pages/2_策略配置.py', encoding='utf-8').read())
    
    elif page == "提醒记录":
        exec(open('pages/4_提醒记录.py', encoding='utf-8').read())


if __name__ == "__main__":
    main()
