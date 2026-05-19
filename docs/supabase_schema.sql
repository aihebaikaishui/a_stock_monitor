-- Supabase 数据库表结构
-- 在 Supabase Dashboard -> SQL Editor 中执行

-- 用户表（使用 Supabase 内置 auth.users，通过 id 关联）
-- 无需手动创建，Supabase Auth 自动管理

-- 持仓标的表
CREATE TABLE IF NOT EXISTS stocks (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    cost_price DECIMAL(10, 2) DEFAULT 0,
    quantity INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'wait_sell',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id)
);

-- 卖出策略配置表
CREATE TABLE IF NOT EXISTS sell_strategies (
    id UUID DEFAULT gen_random_uuid(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    type VARCHAR(20) DEFAULT 'none',
    value DECIMAL(10, 2),
    logic VARCHAR(10) DEFAULT 'AND',
    indicators JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id)
);

-- 买入策略配置表
CREATE TABLE IF NOT EXISTS buy_strategies (
    id UUID DEFAULT gen_random_uuid(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    type VARCHAR(20) DEFAULT 'none',
    value DECIMAL(10, 2),
    base_price DECIMAL(10, 2),
    logic VARCHAR(10) DEFAULT 'AND',
    indicators JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id)
);

-- 触发记录表
CREATE TABLE IF NOT EXISTS triggers (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    stock_id UUID REFERENCES stocks(id) ON DELETE SET NULL,
    stock_code VARCHAR(10),
    stock_name VARCHAR(100),
    price DECIMAL(10, 2),
    type VARCHAR(10),
    reason TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id)
);

-- 行级安全策略
ALTER TABLE stocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE sell_strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE buy_strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE triggers ENABLE ROW LEVEL SECURITY;

-- Stocks 表策略：用户只能操作自己的数据
CREATE POLICY "Users can manage own stocks" ON stocks
    FOR ALL USING (auth.uid() = user_id);

-- Sell strategies 表策略
CREATE POLICY "Users can manage own sell strategies" ON sell_strategies
    FOR ALL USING (
        stock_id IN (SELECT id FROM stocks WHERE user_id = auth.uid())
    );

-- Buy strategies 表策略
CREATE POLICY "Users can manage own buy strategies" ON buy_strategies
    FOR ALL USING (
        stock_id IN (SELECT id FROM stocks WHERE user_id = auth.uid())
    );

-- Triggers 表策略：用户只能操作自己的记录
CREATE POLICY "Users can manage own triggers" ON triggers
    FOR ALL USING (auth.uid() = user_id);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_stocks_user_id ON stocks(user_id);
CREATE INDEX IF NOT EXISTS idx_triggers_user_id ON triggers(user_id);
CREATE INDEX IF NOT EXISTS idx_triggers_created_at ON triggers(created_at DESC);
