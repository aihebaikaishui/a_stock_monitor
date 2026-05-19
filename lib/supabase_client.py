"""Supabase 客户端模块"""
import os
from supabase import create_client, Client

SUPABASE_URL = "https://shuywvnmfgahhvotakrx.supabase.co"
SUPABASE_KEY = "sb_publishable_TwPUTDwfncCDUiqi8h3A6w_dPzOwnDi"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase_client() -> Client:
    """获取 Supabase 客户端实例"""
    return supabase
