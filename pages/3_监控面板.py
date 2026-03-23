"""监控面板页面"""
import streamlit as st
import pandas as pd

from lib.stock import StockData
from lib.data_manager import DataManager
from lib.strategy import StrategyChecker

st.header("实时监控面板")

stocks = DataManager.load_stocks()

if not stocks:
    st.warning("⚠️ 请先添加标的")
    st.stop()

# 获取所有标的的实时数据
codes = [stock['code'] for stock in stocks]
realtime_data = StockData.get_realtime_data(codes)

if realtime_data.empty:
    st.error("❌ 无法获取实时数据，请检查网络连接")
    st.stop()

# 构建价格字典
price_dict = {}
for _, row in realtime_data.iterrows():
    code = f"{int(row['代码']):06d}"
    price_dict[code] = {
        'name': row['名称'],
        'price': row['最新价'],
        'change_percent': row['涨跌幅'],
        'volume': row['成交量'],
        'amount': row['成交额'],
        'high': row['最高'],
        'low': row['最低'],
        'open': row['今开']
    }

# 构造展示数据
display_data = []
for stock in stocks:
    code = stock['code']
    
    if code not in price_dict:
        continue
    
    info = price_dict[code]
    current_price = info['price']
    change_percent = info['change_percent']
    
    # 计算盈亏
    cost_price = stock.get('cost_price', 0)
    if cost_price > 0:
        profit = (current_price - cost_price) * stock.get('quantity', 0)
        profit_percent = (current_price - cost_price) / cost_price * 100
    else:
        profit = 0
        profit_percent = 0
    
    # 状态显示
    status_map = {
        'wait_sell': ('⏳ 等待卖出', 'blue'),
        'wait_buy': ('⏰ 等待买入', 'orange'),
        'completed': ('✅ 已完成', 'green')
    }
    status_text, status_color = status_map.get(stock['status'], (stock['status'], 'gray'))
    
    # 策略提示
    sell_config = stock.get('sell_config', {})
    buy_config = stock.get('buy_config', {})
    
    sell_tip = ""
    if sell_config:
        if sell_config.get('type') == 'fixed_price':
            sell_tip = f"卖出价≥{sell_config['value']:.2f}"
        elif sell_config.get('type') == 'percent_up':
            sell_tip = f"涨幅≥{sell_config['value']}%"
    
    buy_tip = ""
    if buy_config:
        if buy_config.get('type') == 'fixed_price':
            buy_tip = f"买入价≤{buy_config['value']:.2f}"
        elif buy_config.get('type') == 'percent_down':
            buy_tip = f"跌幅≥{buy_config['value']}%"
    
    display_data.append({
        '代码': code,
        '名称': info['name'],
        '当前价': f"{current_price:.2f}",
        '涨跌幅': f"{change_percent:+.2f}%",
        '成本价': f"{cost_price:.2f}",
        '盈亏': f"{profit:+.2f}",
        '盈亏%': f"{profit_percent:+.2f}%",
        '状态': status_text,
        '卖出策略': sell_tip if sell_tip else '-',
        '买入策略': buy_tip if buy_tip else '-'
    })

if display_data:
    df = pd.DataFrame(display_data)
    
    # 颜色函数
    def color_change(val):
        if isinstance(val, str) and '%' in val:
            num = float(val.replace('%', '').replace('+', ''))
            if num > 0:
                return 'color: red'
            elif num < 0:
                return 'color: green'
        return ''
    
    st.dataframe(
        df.style.applymap(color_change, subset=['涨跌幅', '盈亏%']),
        use_container_width=True,
        hide_index=True
    )
    
    # 统计信息
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_stocks = len(display_data)
    total_profit = sum(float(d['盈亏'].replace('+', '')) for d in display_data)
    profit_count = len([d for d in display_data if float(d['盈亏'].replace('+', '')) > 0])
    loss_count = len([d for d in display_data if float(d['盈亏'].replace('+', '')) < 0])
    
    with col1:
        st.metric("监控标的", total_stocks)
    with col2:
        st.metric("总盈亏", f"{total_profit:+.2f} 元")
    with col3:
        st.metric("盈利", profit_count, delta="盈利")
    with col4:
        st.metric("亏损", loss_count, delta="亏损", delta_color="inverse")

# 刷新按钮
st.markdown("---")
if st.button("🔄 刷新数据", use_container_width=True):
    st.rerun()
