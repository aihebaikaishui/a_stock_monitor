"""策略判断模块"""
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class StrategyChecker:
    """策略检查类"""
    
    @staticmethod
    def check_sell_condition(stock: Dict, current_price: float) -> Tuple[bool, str]:
        """检查卖出条件
        返回: (是否触发, 触发原因)
        """
        sell_config = stock.get('sell_config', {})
        
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
        
        # 技术指标卖出（暂不支持）
        elif sell_config.get('type') == 'technical':
            # TODO: 实现技术指标判断
            pass
        
        return False, ""
    
    @staticmethod
    def check_buy_condition(stock: Dict, current_price: float) -> Tuple[bool, str]:
        """检查买入条件
        返回: (是否触发, 触发原因)
        """
        buy_config = stock.get('buy_config', {})
        
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
        
        # 技术指标买入（暂不支持）
        elif buy_config.get('type') == 'technical':
            # TODO: 实现技术指标判断
            pass
        
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
        
        for stock in stocks:
            code = stock['code']
            
            if code not in price_dict:
                continue
            
            stock_info = price_dict[code]
            current_price = stock_info['price']
            
            # 根据状态检查对应策略
            if stock['status'] == 'wait_sell':
                triggered, reason = StrategyChecker.check_sell_condition(stock, current_price)
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
                triggered, reason = StrategyChecker.check_buy_condition(stock, current_price)
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
