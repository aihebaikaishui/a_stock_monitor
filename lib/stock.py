"""股票数据获取模块"""
import akshare as ak
import pandas as pd
import requests
from datetime import datetime
import logging
import streamlit as st

logger = logging.getLogger(__name__)

SINA_HEADERS = {
    'Referer': 'https://finance.sina.com.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


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
    def _get_sina_realtime(codes):
        """使用新浪接口获取实时行情"""
        if not codes:
            return pd.DataFrame()
        
        symbols = ','.join([f'sh{c}' if c.startswith(('6', '5')) else f'sz{c}' for c in codes])
        url = f'https://hq.sinajs.cn/list={symbols}'
        
        try:
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.encoding = 'gb18030'
            lines = resp.text.strip().split('\n')
            
            data = []
            for line in lines:
                if '=' not in line:
                    continue
                match = line.split('"')
                if len(match) < 2:
                    continue
                parts = match[1].split(',')
                if len(parts) < 10:
                    continue
                code_raw = match[0].split('_')[-1].strip('=')
                prefix = code_raw[:2]
                code = code_raw[2:]
                data.append({
                    '代码': code,
                    '名称': parts[0],
                    '最新价': float(parts[3]) if parts[3] else 0,
                    '涨跌幅': (float(parts[3]) - float(parts[2])) / float(parts[2]) * 100 if parts[2] and float(parts[2]) > 0 else 0,
                    '今开': float(parts[1]) if parts[1] else 0,
                    '最高': float(parts[4]) if parts[4] else 0,
                    '最低': float(parts[5]) if parts[5] else 0,
                    '成交量': float(parts[8]) if parts[8] else 0,
                    '成交额': float(parts[9]) if parts[9] else 0,
                    '昨收': float(parts[2]) if parts[2] else 0,
                })
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"新浪接口失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=10)
    def get_realtime_data(codes=None):
        """获取实时行情数据
        codes: 股票代码列表，如 ['600519', '000001']
        """
        df = pd.DataFrame()
        
        try:
            df = ak.stock_zh_a_spot_em()
        except Exception as e:
            logger.warning(f"东方财富接口失败: {e}")
        
        if df.empty and codes:
            logger.info("使用新浪接口获取数据")
            df = StockData._get_sina_realtime(codes)
        
        if codes and not df.empty:
            df = df[df['代码'].apply(lambda x: f"{int(x):06d}").isin(codes)]
        
        return df
    
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
        def process_df(df):
            if df is None or df.empty:
                return df
            rename_map = {
                '日期': 'date', '股票代码': 'code', '开盘': 'open',
                '收盘': 'close', '最高': 'high', '最低': 'low',
                '成交量': 'volume', '成交额': 'amount', '振幅': 'amplitude',
                '涨跌幅': 'change_pct', '涨跌额': 'change', '换手率': 'turnover'
            }
            existing_rename = {k: v for k, v in rename_map.items() if k in df.columns}
            if existing_rename:
                df = df.rename(columns=existing_rename)
            return df
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                adjust=adjust,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            return process_df(df)
        except Exception as e:
            logger.warning(f"stock_zh_a_hist 失败，尝试备用接口: {e}")
        
        try:
            df = ak.stock_zh_a_hist_em(
                symbol=code,
                period=period,
                adjust=adjust,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            return process_df(df)
        except Exception as e:
            logger.warning(f"stock_zh_a_hist_em 失败: {e}")
        
        try:
            import requests
            if code.startswith('6'):
                symbol = f'sh{code}'
            else:
                symbol = f'sz{code}'
            url = f'https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&datalen=60'
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={
                        'day': 'date', 'open': 'open', 'close': 'close',
                        'high': 'high', 'low': 'low', 'volume': 'volume'
                    })
                    for col in ['open', 'close', 'high', 'low', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    return df
        except Exception as e:
            logger.warning(f"新浪备用接口也失败: {e}")
        
        logger.error(f"所有K线数据接口都无法获取 {code}")
        return pd.DataFrame()
    
    @staticmethod
    def get_fund_name(code: str) -> str:
        """根据基金代码获取基金名称"""
        try:
            import requests
            url = f"https://fund.eastmoney.com/pingzhongdata/{code}.js"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            import re
            match = re.search(r'fS_name = "(.*?)"', resp.text)
            if match:
                return match.group(1)
        except Exception as e:
            logger.warning(f"获取基金名称失败 {code}: {e}")
        return f"基金{code}"
