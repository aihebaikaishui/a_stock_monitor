"""策略判断模块"""
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TechnicalIndicator:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线 (EMA)"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算 MACD
        返回: (DIF, DEA, MACD柱)
        """
        ema_fast = TechnicalIndicator.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicator.calculate_ema(prices, slow)
        dif = ema_fast - ema_slow
        dea = TechnicalIndicator.calculate_ema(dif, signal)
        macd_hist = (dif - dea) * 2  # MACD 柱状图
        return dif, dea, macd_hist
    
    @staticmethod
    def calculate_ma(prices: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均线 (MA)"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def get_macd_signal(dif: float, dea: float, prev_dif: float, prev_dea: float) -> str:
        """判断 MACD 信号
        返回: '金叉', '死叉', '红柱', '绿柱', '无信号'
        """
        # 金叉：DIF 从下穿上
        if prev_dif <= prev_dea and dif > dea:
            return '金叉'
        # 死叉：DIF 从上穿下
        if prev_dif >= prev_dea and dif < dea:
            return '死叉'
        return '无信号'
    
    @staticmethod
    def get_ma_signal(ma_short: float, ma_long: float, prev_ma_short: float, prev_ma_long: float) -> str:
        """判断 MA 均线信号
        返回: '金叉', '死叉', '无信号'
        """
        # 金叉：短期均线从下穿上
        if prev_ma_short <= prev_ma_long and ma_short > ma_long:
            return '金叉'
        # 死叉：短期均线从上穿下
        if prev_ma_short >= prev_ma_long and ma_short < ma_long:
            return '死叉'
        return '无信号'
    
    @staticmethod
    def check_macd_cross(dif: pd.Series, dea: pd.Series, index: int = -1) -> str:
        """检查 MACD 金叉/死叉（用于历史信号检测）
        index=-1 表示最新位置
        """
        if len(dif) < 2 or index >= 0:
            return '无信号'
        
        prev_idx = index - 1
        curr_dif = dif.iloc[index]
        curr_dea = dea.iloc[index]
        prev_dif = dif.iloc[prev_idx]
        prev_dea = dea.iloc[prev_idx]
        
        return TechnicalIndicator.get_macd_signal(curr_dif, curr_dea, prev_dif, prev_dea)
    
    @staticmethod
    def check_ma_cross(ma_short: pd.Series, ma_long: pd.Series, index: int = -1) -> str:
        """检查 MA 均线金叉/死叉
        index=-1 表示最新位置
        """
        if len(ma_short) < 2 or index >= 0:
            return '无信号'
        
        prev_idx = index - 1
        curr_short = ma_short.iloc[index]
        curr_long = ma_long.iloc[index]
        prev_short = ma_short.iloc[prev_idx]
        prev_long = ma_long.iloc[prev_idx]
        
        if pd.isna(curr_short) or pd.isna(curr_long) or pd.isna(prev_short) or pd.isna(prev_long):
            return '无信号'
        
        return TechnicalIndicator.get_ma_signal(curr_short, curr_long, prev_short, prev_long)


class StrategyChecker:
    """策略检查类"""
    
    @staticmethod
    def _get_kline_data(code: str, period: str = 'daily', adjust: str = 'qfq') -> pd.DataFrame:
        """获取K线数据（内部使用）"""
        try:
            from lib.stock import StockData
            df = StockData.get_kline_data(code, period, adjust)
            return df
        except Exception as e:
            logger.error(f"获取K线数据失败 {code}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def _check_technical_sell(config: Dict, kline_df: pd.DataFrame, current_price: float) -> Tuple[bool, str]:
        """检查技术指标卖出条件
        config: 技术指标配置
        kline_df: K线数据（需要包含收盘价close列）
        返回: (是否触发, 触发原因)
        """
        if kline_df.empty or 'close' not in kline_df.columns:
            return False, ""
        
        close_prices = kline_df['close']
        if len(close_prices) < 30:  # 需要足够的数据计算指标
            return False, ""
        
        # 获取最新收盘价（如果K线最新不是今天，用当前价）
        if len(close_prices) > 0:
            latest_close = close_prices.iloc[-1]
        else:
            latest_close = current_price
        
        logic = config.get('logic', 'AND')
        indicators = config.get('indicators', [])
        
        results = []
        reasons = []
        
        for ind in indicators:
            name = ind.get('name', '').upper()
            condition = ind.get('condition', '')
            params = ind.get('params', {})
            
            if name == 'MACD':
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal = params.get('signal', 9)
                
                dif, dea, macd_hist = TechnicalIndicator.calculate_macd(close_prices, fast, slow, signal)
                
                # 检查最新信号
                if len(dif) >= 2:
                    curr_signal = TechnicalIndicator.get_macd_signal(
                        dif.iloc[-1], dea.iloc[-1],
                        dif.iloc[-2], dea.iloc[-2]
                    )
                else:
                    curr_signal = '无信号'
                
                # 判断是否满足条件
                triggered = False
                if condition == '死叉' and curr_signal == '死叉':
                    triggered = True
                    reasons.append(f"MACD死叉")
                elif condition == '金叉' and curr_signal == '金叉':
                    triggered = True
                    reasons.append(f"MACD金叉")
                
                results.append(triggered)
                
            elif name == 'MA':
                period_short = params.get('period_short', 5)
                period_long = params.get('period_long', 20)
                
                ma_short = TechnicalIndicator.calculate_ma(close_prices, period_short)
                ma_long = TechnicalIndicator.calculate_ma(close_prices, period_long)
                
                if len(ma_short) >= 2 and len(ma_long) >= 2:
                    curr_signal = TechnicalIndicator.get_ma_signal(
                        ma_short.iloc[-1], ma_long.iloc[-1],
                        ma_short.iloc[-2], ma_long.iloc[-2]
                    )
                else:
                    curr_signal = '无信号'
                
                triggered = False
                if condition == '死叉' and curr_signal == '死叉':
                    triggered = True
                    reasons.append(f"MA{period_short}死叉MA{period_long}")
                elif condition == '上穿' and curr_signal == '金叉':
                    triggered = True
                    reasons.append(f"MA{period_short}上穿MA{period_long}")
                
                results.append(triggered)
        
        if not results:
            return False, ""
        
        # 根据逻辑判断
        if logic == 'AND':
            triggered = all(results)
        else:  # OR
            triggered = any(results)
        
        reason = ' + '.join(reasons) if reasons else ''
        return triggered, reason
    
    @staticmethod
    def _check_technical_buy(config: Dict, kline_df: pd.DataFrame, current_price: float) -> Tuple[bool, str]:
        """检查技术指标买入条件
        config: 技术指标配置
        kline_df: K线数据
        返回: (是否触发, 触发原因)
        """
        if kline_df.empty or 'close' not in kline_df.columns:
            return False, ""
        
        close_prices = kline_df['close']
        if len(close_prices) < 30:
            return False, ""
        
        logic = config.get('logic', 'AND')
        indicators = config.get('indicators', [])
        
        results = []
        reasons = []
        
        for ind in indicators:
            name = ind.get('name', '').upper()
            condition = ind.get('condition', '')
            params = ind.get('params', {})
            
            if name == 'MACD':
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal = params.get('signal', 9)
                
                dif, dea, macd_hist = TechnicalIndicator.calculate_macd(close_prices, fast, slow, signal)
                
                if len(dif) >= 2:
                    curr_signal = TechnicalIndicator.get_macd_signal(
                        dif.iloc[-1], dea.iloc[-1],
                        dif.iloc[-2], dea.iloc[-2]
                    )
                else:
                    curr_signal = '无信号'
                
                triggered = False
                if condition == '金叉' and curr_signal == '金叉':
                    triggered = True
                    reasons.append(f"MACD金叉")
                elif condition == '死叉' and curr_signal == '死叉':
                    triggered = True
                    reasons.append(f"MACD死叉")
                
                results.append(triggered)
                
            elif name == 'MA':
                period_short = params.get('period_short', 5)
                period_long = params.get('period_long', 20)
                
                ma_short = TechnicalIndicator.calculate_ma(close_prices, period_short)
                ma_long = TechnicalIndicator.calculate_ma(close_prices, period_long)
                
                if len(ma_short) >= 2 and len(ma_long) >= 2:
                    curr_signal = TechnicalIndicator.get_ma_signal(
                        ma_short.iloc[-1], ma_long.iloc[-1],
                        ma_short.iloc[-2], ma_long.iloc[-2]
                    )
                else:
                    curr_signal = '无信号'
                
                triggered = False
                if condition == '上穿' and curr_signal == '金叉':
                    triggered = True
                    reasons.append(f"MA{period_short}上穿MA{period_long}")
                elif condition == '下穿' and curr_signal == '死叉':
                    triggered = True
                    reasons.append(f"MA{period_short}下穿MA{period_long}")
                
                results.append(triggered)
        
        if not results:
            return False, ""
        
        if logic == 'AND':
            triggered = all(results)
        else:
            triggered = any(results)
        
        reason = ' + '.join(reasons) if reasons else ''
        return triggered, reason
    
    @staticmethod
    def check_sell_condition(stock: Dict, current_price: float, kline_df: pd.DataFrame = None) -> Tuple[bool, str]:
        """检查卖出条件
        返回: (是否触发, 触发原因)
        """
        sell_config = stock.get('sell_config') or {}
        
        # 固定价格卖出
        if sell_config.get('type') == 'fixed_price':
            target_price = sell_config.get('value', 0)
            if current_price >= target_price:
                return True, f"当前价 {current_price:.2f} >= 目标价 {target_price:.2f}"
        
        # 涨幅百分比卖出
        elif sell_config.get('type') == 'percent_up':
            cost_price = stock.get('cost_price', 0)
            target_percent = sell_config.get('value', 0)
            if cost_price > 0:
                current_percent = (current_price - cost_price) / cost_price * 100
                if current_percent >= target_percent:
                    return True, f"涨幅 {current_percent:.2f}% >= 目标涨幅 {target_percent}%"
        
        # 技术指标卖出
        elif sell_config.get('type') == 'technical':
            if kline_df is not None:
                return StrategyChecker._check_technical_sell(sell_config, kline_df, current_price)
        
        return False, ""
    
    @staticmethod
    def check_buy_condition(stock: Dict, current_price: float, kline_df: pd.DataFrame = None) -> Tuple[bool, str]:
        """检查买入条件
        返回: (是否触发, 触发原因)
        """
        buy_config = stock.get('buy_config') or {}
        
        # 固定价格买入
        if buy_config.get('type') == 'fixed_price':
            target_price = buy_config.get('value', 0)
            if current_price <= target_price:
                return True, f"当前价 {current_price:.2f} <= 目标价 {target_price:.2f}"
        
        # 跌幅百分比买入
        elif buy_config.get('type') == 'percent_down':
            base_price = buy_config.get('base_price')
            if base_price:
                target_percent = buy_config.get('value', 0)
                current_percent = (current_price - base_price) / base_price * 100
                if current_percent <= -target_percent:
                    return True, f"跌幅 {current_percent:.2f}% <= 目标跌幅 -{target_percent}%"
        
        # 技术指标买入
        elif buy_config.get('type') == 'technical':
            if kline_df is not None:
                return StrategyChecker._check_technical_buy(buy_config, kline_df, current_price)
        
        return False, ""
    
    @staticmethod
    def check_all_strategies(stocks: List[Dict], realtime_data) -> List[Dict]:
        """检查所有标的的策略
        返回触发列表
        """
        triggers = []
        
        if realtime_data.empty:
            return triggers
        
        # 构建价格字典
        price_dict = {}
        for _, row in realtime_data.iterrows():
            code = f"{int(row['代码']):06d}"
            price_dict[code] = {
                'name': row['名称'],
                'price': row['最新价'],
                'change_percent': row['涨跌幅']
            }
        
        # 预获取所有标的的K线数据（用于技术指标判断）
        kline_cache = {}
        for stock in stocks:
            code = stock['code']
            sell_config = stock.get('sell_config') or {}
            buy_config = stock.get('buy_config') or {}
            
            # 如果有技术指标配置，提前获取K线数据
            if sell_config.get('type') == 'technical' or buy_config.get('type') == 'technical':
                kline_cache[code] = StrategyChecker._get_kline_data(code)
        
        for stock in stocks:
            code = stock['code']
            
            if code not in price_dict:
                continue
            
            stock_info = price_dict[code]
            current_price = stock_info['price']
            kline_df = kline_cache.get(code, None)
            
            # 根据状态检查对应策略
            if stock['status'] == 'wait_sell':
                triggered, reason = StrategyChecker.check_sell_condition(stock, current_price, kline_df)
                if triggered:
                    triggers.append({
                        'stock_id': stock['id'],
                        'code': code,
                        'name': stock['name'],
                        'price': current_price,
                        'type': 'sell',
                        'reason': reason
                    })
            
            elif stock['status'] == 'wait_buy':
                triggered, reason = StrategyChecker.check_buy_condition(stock, current_price, kline_df)
                if triggered:
                    triggers.append({
                        'stock_id': stock['id'],
                        'code': code,
                        'name': stock['name'],
                        'price': current_price,
                        'type': 'buy',
                        'reason': reason
                    })
        
        return triggers
