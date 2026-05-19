"""数据管理模块 - 支持本地JSON和Supabase"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
import streamlit as st

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
STOCKS_FILE = os.path.join(DATA_DIR, 'stocks.json')
TRIGGERS_FILE = os.path.join(DATA_DIR, 'triggers.json')

USE_SUPABASE = True


def get_user_id():
    """获取当前用户ID"""
    if USE_SUPABASE:
        try:
            from lib.supabase_client import get_supabase_client
            supabase = get_supabase_client()
            session = supabase.auth.get_session()
            if session and session.user:
                return session.user.id
        except Exception as e:
            logger.error(f"获取用户ID失败: {e}")
    return None


class DataManager:
    """数据管理类"""
    
    @staticmethod
    def _load_stocks_from_json() -> List[Dict]:
        """从JSON文件加载标的数据"""
        try:
            if os.path.exists(STOCKS_FILE):
                with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载标的数据失败: {e}")
        return []
    
    @staticmethod
    def _save_stocks_to_json(stocks: List[Dict]):
        """保存标的数据到JSON文件"""
        try:
            with open(STOCKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(stocks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存标的数据失败: {e}")
    
    @staticmethod
    def load_stocks() -> List[Dict]:
        """加载标的数据"""
        if USE_SUPABASE:
            user_id = get_user_id()
            if not user_id:
                return []
            try:
                from lib.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                result = supabase.table('stocks').select('*').eq('user_id', user_id).execute()
                return result.data if result.data else []
            except Exception as e:
                logger.error(f"从Supabase加载标的数据失败: {e}")
                return []
        else:
            return DataManager._load_stocks_from_json()
    
    @staticmethod
    def save_stocks(stocks: List[Dict]):
        """保存标的数据"""
        if not USE_SUPABASE:
            DataManager._save_stocks_to_json(stocks)
    
    @staticmethod
    def add_stock(stock: Dict) -> bool:
        """添加标的"""
        if USE_SUPABASE:
            user_id = get_user_id()
            if not user_id:
                logger.error("用户未登录")
                return False
            
            try:
                from lib.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                
                existing = supabase.table('stocks').select('id').eq('user_id', user_id).eq('code', stock['code']).execute()
                if existing.data:
                    logger.warning(f"股票 {stock['code']} 已存在")
                    return False
                
                stock['user_id'] = user_id
                stock['status'] = 'wait_sell'
                result = supabase.table('stocks').insert(stock).execute()
                return bool(result.data)
            except Exception as e:
                logger.error(f"添加标的失败: {e}")
                st.error(f"添加标的失败: {e}")
                return False
        else:
            stocks = DataManager._load_stocks_from_json()
            for s in stocks:
                if s['code'] == stock['code']:
                    logger.warning(f"股票 {stock['code']} 已存在")
                    return False
            
            stock['id'] = len(stocks) + 1
            stock['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            stock['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            stock['status'] = 'wait_sell'
            
            stocks.append(stock)
            DataManager._save_stocks_to_json(stocks)
            return True
    
    @staticmethod
    def update_stock(stock_id: str, stock_data: Dict) -> tuple[bool, str]:
        """更新标的"""
        if USE_SUPABASE:
            try:
                from lib.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                stock_data['updated_at'] = datetime.now().isoformat()
                result = supabase.table('stocks').update(stock_data).eq('id', stock_id).execute()
                return True, "更新成功"
            except Exception as e:
                error_msg = f"更新标的失败: {e}"
                logger.error(error_msg)
                return False, error_msg
        else:
            stocks = DataManager._load_stocks_from_json()
            for i, stock in enumerate(stocks):
                if stock['id'] == stock_id:
                    stock_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    stocks[i] = {**stock, **stock_data}
                    DataManager._save_stocks_to_json(stocks)
                    return True
            return False
    
    @staticmethod
    def delete_stock(stock_id: str) -> bool:
        """删除标的"""
        if USE_SUPABASE:
            try:
                from lib.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                result = supabase.table('stocks').delete().eq('id', stock_id).execute()
                return True
            except Exception as e:
                logger.error(f"删除标的失败: {e}")
                return False
        else:
            stocks = DataManager._load_stocks_from_json()
            for i, stock in enumerate(stocks):
                if stock['id'] == stock_id:
                    stocks.pop(i)
                    DataManager._save_stocks_to_json(stocks)
                    return True
            return False
    
    @staticmethod
    def load_triggers() -> List[Dict]:
        """加载触发记录"""
        if USE_SUPABASE:
            user_id = get_user_id()
            if not user_id:
                return []
            try:
                from lib.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                result = supabase.table('triggers').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(100).execute()
                return result.data if result.data else []
            except Exception as e:
                logger.error(f"从Supabase加载触发记录失败: {e}")
                return []
        else:
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
        if not USE_SUPABASE:
            try:
                with open(TRIGGERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(triggers, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"保存触发记录失败: {e}")
    
    @staticmethod
    def add_trigger(trigger: Dict):
        """添加触发记录"""
        if USE_SUPABASE:
            user_id = get_user_id()
            if not user_id:
                return
            trigger['user_id'] = user_id
            trigger['is_read'] = False
            try:
                from lib.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                supabase.table('triggers').insert(trigger).execute()
            except Exception as e:
                logger.error(f"添加触发记录失败: {e}")
        else:
            triggers = DataManager.load_triggers()
            trigger['id'] = len(triggers) + 1
            trigger['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            triggers.insert(0, trigger)
            if len(triggers) > 100:
                triggers = triggers[:100]
            DataManager.save_triggers(triggers)
    
    @staticmethod
    def update_stock_status(stock_id: str, status: str):
        """更新标的监控状态"""
        if USE_SUPABASE:
            try:
                from lib.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                supabase.table('stocks').update({
                    'status': status,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', stock_id).execute()
            except Exception as e:
                logger.error(f"更新标的状态失败: {e}")
        else:
            stocks = DataManager._load_stocks_from_json()
            for i, stock in enumerate(stocks):
                if stock['id'] == stock_id:
                    stocks[i]['status'] = status
                    stocks[i]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    DataManager._save_stocks_to_json(stocks)
                    return True
            return False
