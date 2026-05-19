"""提醒记录页面"""
import streamlit as st
import pandas as pd

from lib.data_manager import DataManager

st.header("提醒记录")

triggers = DataManager.load_triggers()

if not triggers:
    st.info("📌 暂无提醒记录")
else:
    # 构造展示数据
    display_data = []
    for trigger in triggers:
        display_data.append({
            '时间': trigger.get('created_at', ''),
            '标的': f"{trigger.get('name', '')}({trigger.get('code', '')})",
            '类型': '📤 卖出提醒' if trigger.get('type') == 'sell' else '📥 买入提醒',
            '价格': f"{trigger.get('price', 0):.2f}",
            '原因': trigger.get('reason', '')
        })
    
    df = pd.DataFrame(display_data)
    
    # 颜色函数
    def color_type(val):
        if '卖出' in str(val):
            return 'color: red'
        elif '买入' in str(val):
            return 'color: green'
        return ''
    
    st.dataframe(
        df.style.applymap(color_type, subset=['类型']),
        use_container_width=True,
        hide_index=True
    )
    
    # 统计
    st.markdown("---")
    
    sell_count = len([t for t in triggers if t.get('type') == 'sell'])
    buy_count = len([t for t in triggers if t.get('type') == 'buy'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总提醒数", len(triggers))
    with col2:
        st.metric("卖出提醒", sell_count)
    with col3:
        st.metric("买入提醒", buy_count)
    
    # 清空记录
    st.markdown("---")
    if st.button("🗑️ 清空所有记录", use_container_width=True):
        DataManager.save_triggers([])
        st.success("✅ 记录已清空")
        st.rerun()
