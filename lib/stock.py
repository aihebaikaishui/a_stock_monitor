"""股票数据获取模块"""
import akshare as ak
import pandas as pd
from datetime import datetime
import logging
import streamlit as st

logger = logging.getLogger(__name__)


class StockData:
    """股票数据操作类"""
    
    @staticmethod
    @st.cache_data(ttl=60)
    def get_a_stock_list():
        """获取A股股票列表"""
        try:
            df = ak.stock_info_a_code_name()
            df['code'] = df['code'].apply(lambda x: f"{int(x):06d}")
            return df[['code', 'name']]
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=10)
    def get_realtime_data(codes=None):
        """获取实时行情数据
        codes: 股票代码列表，如 ['600519', '000001']
        """
        try:
            df = ak.stock_zh_a_spot_em()
            if codes:
                df = df[df['代码'].apply(lambda x: f"{int(x):06d}").isin(codes)]
            return df
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_info(code):
        """获取股票基本信息"""
        try:
            df = ak.stock_individual_info_em(symbol=code)
            return df
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None
    
    @staticmethod
    @st.cache_data(ttl=300)
    def get_kline_data(code, period='daily', adjust=''):
        """获取K线数据
        period: daily, weekly, monthly
        adjust: '', 'qfq'前复权, 'hfq'后复权
        """
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                adjust=adjust,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            return df
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return pd.DataFrame()
