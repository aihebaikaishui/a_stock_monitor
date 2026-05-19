"""监控面板页面"""
import streamlit as st
import pandas as pd
import logging

from lib.stock import StockData
from lib.data_manager import DataManager
from lib.strategy import StrategyChecker, TechnicalIndicator
from lib.notify import NotifyManager

logger = logging.getLogger(__name__)

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

# 预获取K线数据用于技术指标计算
kline_cache = {}
for stock in stocks:
    code = stock['code']
    try:
        kline_cache[code] = StrategyChecker._get_kline_data(code)
    except Exception as e:
        logger.warning(f"获取K线数据失败 {code}: {e}")

def get_tech_signal_info(code):
    """获取技术指标信号详情"""
    kline_df = kline_cache.get(code)
    if kline_df is None or kline_df.empty:
        return None, None, None, None, None, None
    
    close_prices = kline_df.get('close')
    if close_prices is None or len(close_prices) < 30:
        return None, None, None, None, None, None
    
    # 计算 MACD
    dif, dea, macd_hist = TechnicalIndicator.calculate_macd(close_prices, 12, 26, 9)
    macd_signal = None
    dif_val = dif.iloc[-1] if len(dif) >= 1 else None
    dea_val = dea.iloc[-1] if len(dea) >= 1 else None
    if len(dif) >= 2 and dif_val is not None and dea_val is not None and not pd.isna(dif_val) and not pd.isna(dea_val):
        macd_signal = TechnicalIndicator.get_macd_signal(
            dif.iloc[-1], dea.iloc[-1],
            dif.iloc[-2], dea.iloc[-2]
        )
    
    # 计算 MA
    ma5 = TechnicalIndicator.calculate_ma(close_prices, 5)
    ma20 = TechnicalIndicator.calculate_ma(close_prices, 20)
    ma_signal = None
    ma5_val = ma5.iloc[-1] if len(ma5) >= 1 else None
    ma20_val = ma20.iloc[-1] if len(ma20) >= 1 else None
    if len(ma5) >= 2 and len(ma20) >= 2 and ma5_val is not None and ma20_val is not None and not pd.isna(ma5_val) and not pd.isna(ma20_val):
        ma_signal = TechnicalIndicator.get_ma_signal(
            ma5.iloc[-1], ma20.iloc[-1],
            ma5.iloc[-2], ma20.iloc[-2]
        )
    
    return macd_signal, ma_signal, dif_val, dea_val, ma5_val, ma20_val

def check_signal_match(stock, macd_signal, ma_signal):
    """检查信号是否匹配配置的策略"""
    status = stock.get('status', '')
    sell_config = stock.get('sell_config', {})
    buy_config = stock.get('buy_config', {})
    
    # 卖出信号检查（当状态是 wait_sell 时）
    if status == 'wait_sell' and macd_signal in ['死叉', '金叉']:
        if sell_config.get('type') == 'technical':
            indicators = sell_config.get('indicators', [])
            for ind in indicators:
                if ind.get('name') == 'MACD' and ind.get('condition') == macd_signal:
                    return True, 'sell', f"MACD{ind.get('condition')}"
    
    if status == 'wait_sell' and ma_signal in ['死叉', '上穿']:
        if sell_config.get('type') == 'technical':
            indicators = sell_config.get('indicators', [])
            for ind in indicators:
                if ind.get('name') == 'MA' and ind.get('condition') == ma_signal:
                    return True, 'sell', f"MA{ind.get('params', {}).get('period_short')}/{ind.get('params', {}).get('period_long')}{ind.get('condition')}"
    
    # 买入信号检查（当状态是 wait_buy 时）
    if status == 'wait_buy' and macd_signal in ['金叉', '死叉']:
        if buy_config.get('type') == 'technical':
            indicators = buy_config.get('indicators', [])
            for ind in indicators:
                if ind.get('name') == 'MACD' and ind.get('condition') == macd_signal:
                    return True, 'buy', f"MACD{ind.get('condition')}"
    
    if status == 'wait_buy' and ma_signal in ['上穿', '死叉']:
        if buy_config.get('type') == 'technical':
            indicators = buy_config.get('indicators', [])
            for ind in indicators:
                if ind.get('name') == 'MA' and ind.get('condition') == ma_signal:
                    return True, 'buy', f"MA{ind.get('params', {}).get('period_short')}/{ind.get('params', {}).get('period_long')}{ind.get('condition')}"
    
    return False, None, None

# 收集所有触发的信号用于提醒
signal_alerts = []

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
        elif sell_config.get('type') == 'technical':
            indicators = sell_config.get('indicators', [])
            logic = sell_config.get('logic', 'AND')
            parts = []
            for ind in indicators:
                name = ind.get('name', '')
                cond = ind.get('condition', '')
                if name == 'MACD':
                    params = ind.get('params', {})
                    parts.append(f"MACD{cond}")
                elif name == 'MA':
                    params = ind.get('params', {})
                    parts.append(f"MA{params.get('period_short')}/{params.get('period_long')}{cond}")
            sell_tip = f"技术指标({logic})" + " ".join(parts)
    
    buy_tip = ""
    if buy_config:
        if buy_config.get('type') == 'fixed_price':
            buy_tip = f"买入价≤{buy_config['value']:.2f}"
        elif buy_config.get('type') == 'percent_down':
            buy_tip = f"跌幅≥{buy_config['value']}%"
        elif buy_config.get('type') == 'technical':
            indicators = buy_config.get('indicators', [])
            logic = buy_config.get('logic', 'AND')
            parts = []
            for ind in indicators:
                name = ind.get('name', '')
                cond = ind.get('condition', '')
                if name == 'MACD':
                    parts.append(f"MACD{cond}")
                elif name == 'MA':
                    params = ind.get('params', {})
                    parts.append(f"MA{params.get('period_short')}/{params.get('period_long')}{cond}")
            buy_tip = f"技术指标({logic})" + " ".join(parts)
    
    # 获取技术指标信号
    macd_signal, ma_signal, dif_val, dea_val, ma5_val, ma20_val = get_tech_signal_info(code)
    
    # 检查信号是否匹配策略
    is_match, match_type, match_reason = check_signal_match(stock, macd_signal, ma_signal)
    if is_match:
        signal_alerts.append({
            'code': code,
            'name': stock['name'],
            'price': current_price,
            'type': match_type,
            'reason': match_reason,
            'status': stock['status']
        })
    
    # 格式化信号显示
    def format_macd(dif, dea, signal):
        if dif is None or dea is None:
            return '-'
        dif_str = f"{dif:.3f}" if not pd.isna(dif) else 'N/A'
        dea_str = f"{dea:.3f}" if not pd.isna(dea) else 'N/A'
        sig_str = f"({signal})" if signal else ""
        return f"DIF:{dif_str} DEA:{dea_str}{sig_str}"
    
    def format_ma(ma5, ma20, signal):
        if ma5 is None or ma20 is None:
            return '-'
        ma5_str = f"{ma5:.2f}" if not pd.isna(ma5) else 'N/A'
        ma20_str = f"{ma20:.2f}" if not pd.isna(ma20) else 'N/A'
        sig_str = f"({signal})" if signal else ""
        return f"MA5:{ma5_str} MA20:{ma20_str}{sig_str}"
    
    macd_display = format_macd(dif_val, dea_val, macd_signal)
    ma_display = format_ma(ma5_val, ma20_val, ma_signal)
    
    display_data.append({
        '代码': code,
        '名称': info['name'],
        '当前价': f"{current_price:.2f}",
        '涨跌幅': f"{change_percent:+.2f}%",
        '成本价': f"{cost_price:.2f}",
        '盈亏': f"{profit:+.2f}",
        '盈亏%': f"{profit_percent:+.2f}%",
        '状态': status_text,
        'MACD': macd_display,
        'MA': ma_display,
        '卖出策略': sell_tip if sell_tip else '-',
        '买入策略': buy_tip if buy_tip else '-'
    })

# 显示信号提醒
if signal_alerts:
    for alert in signal_alerts:
        action = "卖出" if alert['type'] == 'sell' else "买入"
        icon = "🚨" if alert['type'] == 'sell' else "🎯"
        message = f"{icon}【{action}信号】{alert['name']}({alert['code']}) 当前价: {alert['price']:.2f}元 触发: {alert['reason']}"
        NotifyManager.show_toast(message, icon=icon)
    st.warning(f"⚠️ 检测到 {len(signal_alerts)} 个交易信号！")

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
    
    def color_signal(val):
        if isinstance(val, str):
            if '金叉' in val or '上穿' in val:
                return 'color: red'
            elif '死叉' in val or '下穿' in val:
                return 'color: green'
        return ''
    
    st.dataframe(
        df.style.applymap(color_change, subset=['涨跌幅', '盈亏%'])
               .applymap(color_signal, subset=['MACD', 'MA']),
        use_container_width=True,
        hide_index=True
    )
    
    # 图例说明
    st.caption("📌 MACD/MA 颜色说明：红色=金叉/上穿(买入信号)，绿色=死叉/下穿(卖出信号)")
    
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
