# A股盯盘助手

一款面向个人投资者的智能股票监控与交易提醒工具，核心功能是帮助投资者实现"高抛低吸"的波段操作策略。

## 技术栈

- **Web框架**: Streamlit
- **数据源**: AkShare（免费）
- **部署平台**: Streamlit Cloud（免费）

## 功能特性

- 📊 **标的管理**: 添加/编辑/删除持仓标的
- ⚙️ **策略配置**: 设置买卖条件和提醒参数
- 📈 **实时监控**: 展示实时行情和监控状态
- 🔔 **提醒通知**: 页面提醒 + 邮件/微信推送
- 📋 **提醒记录**: 查看历史提醒和操作记录

## 快速开始

### 1. 安装依赖

```bash
cd a_stock_monitor
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

### 3. 访问应用

打开浏览器访问 http://localhost:8501

## 项目结构

```
a_stock_monitor/
├── app.py                    # 主程序入口
├── pages/                    # 功能页面
│   ├── 1_标的管理.py
│   ├── 2_策略配置.py
│   ├── 3_监控面板.py
│   └── 4_提醒记录.py
├── lib/                      # 工具库
│   ├── stock.py              # 股票数据获取
│   ├── strategy.py           # 策略判断
│   ├── notify.py             # 推送通知
│   └── data_manager.py       # 数据管理
├── data/                     # 数据存储
│   ├── stocks.json           # 标的配置
│   └── triggers.json         # 触发记录
├── .streamlit/
│   └── config.toml           # Streamlit配置
└── requirements.txt          # 依赖列表
```

## 部署到 Streamlit Cloud

1. 将代码推送到 GitHub 仓库
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 使用 GitHub 账号登录
4. 点击 "New app" 选择仓库和分支
5. 点击 "Deploy" 等待部署完成

## 部署到 Zeabur（支持 Gitee）

如果无法访问 GitHub，可以使用 Zeabur 部署，支持 Gitee 仓库。

### 步骤一：准备 Gitee 仓库

确保代码已推送到 Gitee（参考上方本地部署步骤）。

### 步骤二：部署到 Zeabur

1. 访问 [zeabur.com](https://zeabur.com)
2. 点击 **Sign up**，使用 **Gitee 账号登录**（或邮箱注册）
3. 登录后点击 **New Project**
4. 选择 **Deploy from Gitee**
5. 授权 Zeabur 访问你的 Gitee 仓库
6. 选择 `a_stock_monitor` 仓库

### 步骤三：配置服务

1. 选择服务类型：**Streamlit**
2. 设置启动命令：

   ```bash
   streamlit run app.py --server.port 8080 --server.address 0.0.0.0
   ```

3. 环境变量（可选）：如需配置推送功能，添加相关环境变量

### 步骤四：等待部署

1. 点击 **Deploy** 开始部署
2. 等待 2-3 分钟，部署完成后会获得一个公网 URL
3. 访问该 URL 即可使用

### Zeabur 注意事项

- 免费版每月有 1000 小时用量，超时会休眠
- 首次访问需要等待几秒唤醒
- 推荐保持应用活跃以获得最佳体验

## 使用说明

### 添加标的

1. 进入"标的管理"页面
2. 搜索并选择股票
3. 输入成本价和持仓数量
4. 点击"添加标的"

### 配置策略

1. 进入"策略配置"页面
2. 选择要配置的标的
3. 设置卖出/买入条件
4. 点击"保存策略配置"

### 查看监控

1. 进入"监控面板"页面
2. 查看所有标的的实时行情
3. 根据策略状态进行操作

## 注意事项

- 本工具仅供个人投资参考，不构成投资建议
- 请合理设置提醒条件，避免过度交易
- 数据来源为免费接口，可能存在延迟
