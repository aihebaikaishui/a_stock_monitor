"""数据管理模块"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 数据文件路径
STOCKS_FILE = '/workspace/projects/a_stock_monitor/data/stocks.json'
TRIGGERS_FILE = '/workspace/projects/a_stock_monitor/data/triggers.json'


class DataManager:
    """数据管理类"""
    
    @staticmethod
    def load_stocks() -> List[Dict]:
        """加载标的数据"""
        try:
            if os.path.exists(STOCKS_FILE):
                with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载标的数据失败: {e}")
        return []
    
    @staticmethod
    def save_stocks(stocks: List[Dict]):
        """保存标的数据"""
        try:
            with open(STOCKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(stocks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存标的数据失败: {e}")
    
    @staticmethod
    def add_stock(stock: Dict) -> bool:
        """添加标的"""
        stocks = DataManager.load_stocks()
        
        # 检查是否已存在
        for s in stocks:
            if s['code'] == stock['code']:
                logger.warning(f"股票 {stock['code']} 已存在")
                return False
        
        stock['id'] = len(stocks) + 1
        stock['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stock['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stock['status'] = 'wait_sell'  # 初始状态：等待卖出
        
        stocks.append(stock)
        DataManager.save_stocks(stocks)
        return True
    
    @staticmethod
    def update_stock(stock_id: int, stock_data: Dict) -> bool:
        """更新标的"""
        stocks = DataManager.load_stocks()
        
        for i, stock in enumerate(stocks):
            if stock['id'] == stock_id:
                stock_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                stocks[i] = {**stock, **stock_data}
                DataManager.save_stocks(stocks)
                return True
        
        return False
    
    @staticmethod
    def delete_stock(stock_id: int) -> bool:
        """删除标的"""
        stocks = DataManager.load_stocks()
        
        for i, stock in enumerate(stocks):
            if stock['id'] == stock_id:
                stocks.pop(i)
                DataManager.save_stocks(stocks)
                return True
        
        return False
    
    @staticmethod
    def load_triggers() -> List[Dict]:
        """加载触发记录"""
        try:
            if os.path.exists(TRIGGERS_FILE):
                with open(TRIGGERS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载触发记录失败: {e}")
        return []
    
    @staticmethod
    def save_triggers(triggers: List[Dict]):
        """保存触发记录"""
        try:
            with open(TRIGGERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(triggers, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存触发记录失败: {e}")
    
    @staticmethod
    def add_trigger(trigger: Dict):
        """添加触发记录"""
        triggers = DataManager.load_triggers()
        trigger['id'] = len(triggers) + 1
        trigger['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        triggers.insert(0, trigger)  # 最新的记录在前
        
        # 只保留最近100条记录
        if len(triggers) > 100:
            triggers = triggers[:100]
        
        DataManager.save_triggers(triggers)
    
    @staticmethod
    def update_stock_status(stock_id: int, status: str):
        """更新标的监控状态"""
        stocks = DataManager.load_stocks()
        
        for i, stock in enumerate(stocks):
            if stock['id'] == stock_id:
                stocks[i]['status'] = status
                stocks[i]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                DataManager.save_stocks(stocks)
                return True
        
        return False
