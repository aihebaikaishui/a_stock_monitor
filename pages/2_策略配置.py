"""策略配置页面"""
import streamlit as st

from lib.data_manager import DataManager

st.header("策略配置")

stocks = DataManager.load_stocks()

if not stocks:
    st.warning("⚠️ 请先添加标的，再进行策略配置")
    st.stop()

# 选择标的
stock_options = {f"{s['name']}({s['code']})": s['id'] for s in stocks}
selected_stock_name = st.selectbox("选择标的", list(stock_options.keys()))

if selected_stock_name:
    stock_id = stock_options[selected_stock_name]
    stock = None
    for s in stocks:
        if s['id'] == stock_id:
            stock = s
            break
    
    if stock:
        col1, col2 = st.columns(2)
        
        # 卖出策略配置
        with col1:
            st.subheader("📤 卖出策略")
            st.caption("触发时提醒高抛")
            
            sell_config = stock.get('sell_config') or {}
            is_technical_sell = sell_config.get('type') == 'technical'
            
            sell_type = st.selectbox(
                "条件类型",
                ["不设置", "固定价格", "涨幅百分比", "技术指标"],
                index=0 if not sell_config else 
                     (1 if sell_config.get('type') == 'fixed_price' else
                      2 if sell_config.get('type') == 'percent_up' else
                      3 if sell_config.get('type') == 'technical' else 0)
            )
            
            if sell_type == "固定价格":
                sell_value = st.number_input(
                    "目标价格(元)",
                    min_value=0.0,
                    step=0.01,
                    value=float(sell_config.get('value', 0))
                )
                new_sell_config = {'type': 'fixed_price', 'value': sell_value}
                
            elif sell_type == "涨幅百分比":
                sell_value = st.number_input(
                    "目标涨幅(%)",
                    min_value=0.0,
                    step=0.1,
                    value=float(sell_config.get('value', 5))
                )
                new_sell_config = {'type': 'percent_up', 'value': sell_value}
                
            elif sell_type == "技术指标":
                st.markdown("**MACD 设置**")
                macd_fast = st.number_input("快线周期", min_value=1, value=12, key="sell_macd_fast")
                macd_slow = st.number_input("慢线周期", min_value=1, value=26, key="sell_macd_slow")
                macd_signal = st.number_input("信号线周期", min_value=1, value=9, key="sell_macd_signal")
                
                macd_condition = st.selectbox(
                    "MACD 条件",
                    ["死叉", "金叉"],
                    index=0,
                    key="sell_macd_cond"
                )
                
                st.markdown("**MA 均线设置**")
                ma_short = st.number_input("短期均线周期", min_value=1, value=5, key="sell_ma_short")
                ma_long = st.number_input("长期均线周期", min_value=1, value=20, key="sell_ma_long")
                
                ma_condition = st.selectbox(
                    "MA 条件",
                    ["死叉", "上穿"],
                    index=0,
                    key="sell_ma_cond"
                )
                
                st.markdown("**组合逻辑**")
                tech_logic = st.radio(
                    "多指标组合方式",
                    ["AND (全部满足)", "OR (任一满足)"],
                    index=0 if sell_config.get('logic', 'AND') == 'AND' else 1,
                    horizontal=True,
                    key="sell_tech_logic"
                )
                logic_value = 'AND' if 'AND' in tech_logic else 'OR'
                
                # 检查是否启用各指标
                enable_macd = st.checkbox("启用 MACD", value=True, key="sell_enable_macd")
                enable_ma = st.checkbox("启用 MA 均线", value=True, key="sell_enable_ma")
                
                # 构建技术指标配置
                indicators = []
                if enable_macd:
                    indicators.append({
                        'name': 'MACD',
                        'params': {'fast': macd_fast, 'slow': macd_slow, 'signal': macd_signal},
                        'condition': macd_condition
                    })
                if enable_ma:
                    indicators.append({
                        'name': 'MA',
                        'params': {'period_short': ma_short, 'period_long': ma_long},
                        'condition': ma_condition
                    })
                
                new_sell_config = {
                    'type': 'technical',
                    'logic': logic_value,
                    'indicators': indicators
                }
            else:
                new_sell_config = {}
        
        # 买入策略配置
        with col2:
            st.subheader("📥 买入策略")
            st.caption("触发时提醒低吸")
            
            buy_config = stock.get('buy_config') or {}
            
            buy_type = st.selectbox(
                "条件类型",
                ["不设置", "固定价格", "跌幅百分比", "技术指标"],
                index=0 if not buy_config else 
                     (1 if buy_config.get('type') == 'fixed_price' else
                      2 if buy_config.get('type') == 'percent_down' else
                      3 if buy_config.get('type') == 'technical' else 0)
            )
            
            if buy_type == "固定价格":
                buy_value = st.number_input(
                    "目标价格(元)",
                    min_value=0.0,
                    step=0.01,
                    value=float(buy_config.get('value', 0))
                )
                new_buy_config = {'type': 'fixed_price', 'value': buy_value}
                
            elif buy_type == "跌幅百分比":
                buy_value = st.number_input(
                    "目标跌幅(%)",
                    min_value=0.0,
                    step=0.1,
                    value=float(buy_config.get('value', 5))
                )
                new_buy_config = {
                    'type': 'percent_down', 
                    'value': buy_value,
                    'base_price': stock.get('cost_price', 0)
                }
                
            elif buy_type == "技术指标":
                st.markdown("**MACD 设置**")
                macd_fast_b = st.number_input("快线周期", min_value=1, value=12, key="buy_macd_fast")
                macd_slow_b = st.number_input("慢线周期", min_value=1, value=26, key="buy_macd_slow")
                macd_signal_b = st.number_input("信号线周期", min_value=1, value=9, key="buy_macd_signal")
                
                macd_condition_b = st.selectbox(
                    "MACD 条件",
                    ["金叉", "死叉"],
                    index=0,
                    key="buy_macd_cond"
                )
                
                st.markdown("**MA 均线设置**")
                ma_short_b = st.number_input("短期均线周期", min_value=1, value=5, key="buy_ma_short")
                ma_long_b = st.number_input("长期均线周期", min_value=1, value=20, key="buy_ma_long")
                
                ma_condition_b = st.selectbox(
                    "MA 条件",
                    ["上穿", "下穿"],
                    index=0,
                    key="buy_ma_cond"
                )
                
                st.markdown("**组合逻辑**")
                tech_logic_b = st.radio(
                    "多指标组合方式",
                    ["AND (全部满足)", "OR (任一满足)"],
                    index=0 if buy_config.get('logic', 'AND') == 'AND' else 1,
                    horizontal=True,
                    key="buy_tech_logic"
                )
                logic_value_b = 'AND' if 'AND' in tech_logic_b else 'OR'
                
                enable_macd_b = st.checkbox("启用 MACD", value=True, key="buy_enable_macd")
                enable_ma_b = st.checkbox("启用 MA 均线", value=True, key="buy_enable_ma")
                
                indicators_b = []
                if enable_macd_b:
                    indicators_b.append({
                        'name': 'MACD',
                        'params': {'fast': macd_fast_b, 'slow': macd_slow_b, 'signal': macd_signal_b},
                        'condition': macd_condition_b
                    })
                if enable_ma_b:
                    indicators_b.append({
                        'name': 'MA',
                        'params': {'period_short': ma_short_b, 'period_long': ma_long_b},
                        'condition': ma_condition_b
                    })
                
                new_buy_config = {
                    'type': 'technical',
                    'logic': logic_value_b,
                    'indicators': indicators_b
                }
            else:
                new_buy_config = {}
        
        # 保存按钮
        st.markdown("---")
        
        if st.button("💾 保存策略配置", use_container_width=True, type="primary"):
            stock_data = {}
            if new_sell_config:
                stock_data['sell_config'] = new_sell_config
            if new_buy_config:
                stock_data['buy_config'] = new_buy_config
            
            if stock_data:
                success, msg = DataManager.update_stock(stock_id, stock_data)
                if success:
                    st.success("✅ 策略配置已保存")
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("请先配置至少一个策略")
        
        # 当前配置预览
        st.markdown("---")
        st.subheader("📋 当前配置预览")
        
        def format_tech_config(config, prefix):
            if not config or config.get('type') != 'technical':
                return '未设置'
            logic = config.get('logic', 'AND')
            indicators = config.get('indicators', [])
            parts = []
            for ind in indicators:
                name = ind.get('name', '')
                cond = ind.get('condition', '')
                params = ind.get('params', {})
                if name == 'MACD':
                    parts.append(f"MACD({params.get('fast')},{params.get('slow')},{params.get('signal')}){cond}")
                elif name == 'MA':
                    parts.append(f"MA{params.get('period_short')}/{params.get('period_long')}{cond}")
            return f"{logic.join(parts)}" if parts else '未设置'
        
        config_text = f"""
**标的**: {stock['name']}({stock['code']})
**成本价**: {stock.get('cost_price', 0):.2f} 元
**持仓数量**: {stock.get('quantity', 0)} 股

**卖出策略**: 
- 类型: {sell_type if sell_type != '不设置' else '未设置'}
- 配置: {new_sell_config.get('value', format_tech_config(new_sell_config, 'sell')) if 'value' in new_sell_config else format_tech_config(new_sell_config, 'sell')}

**买入策略**: 
- 类型: {buy_type if buy_type != '不设置' else '未设置'}
- 配置: {new_buy_config.get('value', format_tech_config(new_buy_config, 'buy')) if 'value' in new_buy_config else format_tech_config(new_buy_config, 'buy')}
"""
        st.markdown(config_text)
