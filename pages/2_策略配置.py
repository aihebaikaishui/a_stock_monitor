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
    stock = next((s for s in stocks if s['id'] == stock_id), None)
    
    if stock:
        col1, col2 = st.columns(2)
        
        # 卖出策略配置
        with col1:
            st.subheader("📤 卖出策略")
            st.caption("当满足以下任一条件时，提醒高抛")
            
            sell_config = stock.get('sell_config', {})
            
            sell_type = st.selectbox(
                "卖出条件类型",
                ["不设置", "固定价格", "涨幅百分比", "技术指标"],
                index=0 if not sell_config else 
                     (1 if sell_config.get('type') == 'fixed_price' else
                      2 if sell_config.get('type') == 'percent_up' else 0)
            )
            
            if sell_type == "固定价格":
                sell_value = st.number_input(
                    "目标价格(元)",
                    min_value=0.0,
                    step=0.01,
                    value=float(sell_config.get('value', 0))
                )
            elif sell_type == "涨幅百分比":
                sell_value = st.number_input(
                    "目标涨幅(%)",
                    min_value=0.0,
                    step=0.1,
                    value=float(sell_config.get('value', 5))
                )
            elif sell_type == "技术指标":
                st.info("技术指标功能开发中...")
                sell_value = 0
            else:
                sell_value = 0
        
        # 买入策略配置
        with col2:
            st.subheader("📥 买入策略")
            st.caption("当满足以下任一条件时，提醒低吸")
            
            buy_config = stock.get('buy_config', {})
            
            buy_type = st.selectbox(
                "买入条件类型",
                ["不设置", "固定价格", "跌幅百分比", "技术指标"],
                index=0 if not buy_config else 
                     (1 if buy_config.get('type') == 'fixed_price' else
                      2 if buy_config.get('type') == 'percent_down' else 0)
            )
            
            if buy_type == "固定价格":
                buy_value = st.number_input(
                    "目标价格(元)",
                    min_value=0.0,
                    step=0.01,
                    value=float(buy_config.get('value', 0))
                )
            elif buy_type == "跌幅百分比":
                buy_value = st.number_input(
                    "目标跌幅(%)",
                    min_value=0.0,
                    step=0.1,
                    value=float(buy_config.get('value', 5))
                )
            elif buy_type == "技术指标":
                st.info("技术指标功能开发中...")
                buy_value = 0
            else:
                buy_value = 0
        
        # 保存按钮
        st.markdown("---")
        
        if st.button("💾 保存策略配置", use_container_width=True, type="primary"):
            # 构建配置
            new_sell_config = {}
            if sell_type == "固定价格":
                new_sell_config = {'type': 'fixed_price', 'value': sell_value}
            elif sell_type == "涨幅百分比":
                new_sell_config = {'type': 'percent_up', 'value': sell_value}
            
            new_buy_config = {}
            if buy_type == "固定价格":
                new_buy_config = {'type': 'fixed_price', 'value': buy_value}
            elif buy_type == "跌幅百分比":
                new_buy_config = {
                    'type': 'percent_down', 
                    'value': buy_value,
                    'base_price': stock.get('cost_price', 0)
                }
            
            # 更新
            stock_data = {
                'sell_config': new_sell_config,
                'buy_config': new_buy_config
            }
            
            if DataManager.update_stock(stock_id, stock_data):
                st.success("✅ 策略配置已保存")
            else:
                st.error("❌ 保存失败")
        
        # 当前配置预览
        st.markdown("---")
        st.subheader("📋 当前配置预览")
        
        config_text = f"""
**标的**: {stock['name']}({stock['code']})
**成本价**: {stock.get('cost_price', 0):.2f} 元
**持仓数量**: {stock.get('quantity', 0)} 股

**卖出策略**: 
- 类型: {sell_type if sell_type != '不设置' else '未设置'}
- 状态: {'✅ 已配置' if sell_type != '不设置' else '❌ 未配置'}

**买入策略**: 
- 类型: {buy_type if buy_type != '不设置' else '未设置'}
- 状态: {'✅ 已配置' if buy_type != '不设置' else '❌ 未配置'}
"""
        st.markdown(config_text)
