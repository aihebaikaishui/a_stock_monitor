"""标的管理页面"""
import streamlit as st
import pandas as pd

from lib.stock import StockData
from lib.data_manager import DataManager

st.header("标的管理")

# 选项卡
tab1, tab2 = st.tabs(["添加标的", "标的列表"])

# 添加标的
with tab1:
    st.subheader("添加新标的")
    
    # 获取股票列表
    with st.spinner("加载股票列表..."):
        stock_list = StockData.get_a_stock_list()
    
    if stock_list.empty:
        st.error("⚠️ 无法获取股票列表，请检查网络连接")
    else:
        # 搜索框
        search = st.text_input("🔍 搜索股票名称或代码", key="stock_search")
        
        if search:
            filtered = stock_list[
                stock_list['name'].str.contains(search, case=False, na=False) |
                stock_list['code'].str.contains(search, case=False, na=False)
            ]
        else:
            filtered = stock_list.head(100)
        
        # 创建下拉选择
        stock_options = [f"{row['code']} - {row['name']}" for _, row in filtered.iterrows()]
        selected_label = st.selectbox("选择股票", options=stock_options, key="stock_select")
        
        # 解析选择
        stock_code = selected_label.split(" - ")[0] if selected_label else None
        stock_name = selected_label.split(" - ")[1] if selected_label else None
        
        # 其他信息
        col1, col2 = st.columns(2)
        with col1:
            cost_price = st.number_input("成本价(元)", min_value=0.0, step=0.01, value=0.0, key="cost_price")
        with col2:
            quantity = st.number_input("持仓数量", min_value=0, step=100, value=0, key="quantity")
        
        notes = st.text_area("备注", placeholder="可选：添加一些备注信息...", key="notes")
        
        # 添加按钮
        if st.button("✅ 添加标的", use_container_width=True, type="primary"):
            if not stock_code:
                st.error("请先选择股票")
            else:
                new_stock = {
                    'code': stock_code,
                    'name': stock_name,
                    'cost_price': cost_price,
                    'quantity': quantity,
                    'notes': notes,
                    'sell_config': {},
                    'buy_config': {}
                }
                
                if DataManager.add_stock(new_stock):
                    st.success(f"✅ 成功添加: {stock_name}({stock_code})")
                    st.rerun()
                else:
                    st.error("❌ 添加失败，该标的可能已存在")

# 标的列表
with tab2:
    st.subheader("已添加标的")
    
    stocks = DataManager.load_stocks()
    
    if not stocks:
        st.info("📌 暂无标的，请先添加")
    else:
        for stock in stocks:
            with st.expander(f"{stock['name']}({stock['code']})", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    new_cost_price = st.number_input(
                        "成本价",
                        min_value=0.0,
                        step=0.01,
                        value=float(stock.get('cost_price', 0)),
                        key=f"cost_{stock['id']}"
                    )
                    new_quantity = st.number_input(
                        "持仓数量",
                        min_value=0,
                        step=100,
                        value=int(stock.get('quantity', 0)),
                        key=f"qty_{stock['id']}"
                    )
                    new_notes = st.text_area(
                        "备注",
                        value=stock.get('notes', ''),
                        key=f"notes_{stock['id']}"
                    )
                
                with col2:
                    st.write("操作")
                    if st.button("💾 保存", key=f"save_{stock['id']}", use_container_width=True):
                        DataManager.update_stock(stock['id'], {
                            'cost_price': new_cost_price,
                            'quantity': new_quantity,
                            'notes': new_notes
                        })
                        st.success("✅ 已保存")
                        st.rerun()
                    
                    if st.button("🗑️ 删除", key=f"del_{stock['id']}", 
                               use_container_width=True, type="secondary"):
                        if DataManager.delete_stock(stock['id']):
                            st.success("✅ 已删除")
                            st.rerun()
