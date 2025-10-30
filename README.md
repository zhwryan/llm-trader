# AI量化个人交易系统（LLM驱动，Python）

此项目为个人量化/交易实践的最小可用系统，包含：
- 金融信息搜索能力（DuckDuckGo解析，后续可接入 Bing/SerpAPI）
- A股与港股行情获取（yfinance 优先，回退 Yahoo Quote API）
- 本地纸面交易账户（MongoDB）
- 基于LLM的多智能体协作（信息→行情→组合→执行的闭环）

## 环境与安装

1) 安装依赖
```
pip3 install -r requirements.txt
```

2) 可选：配置LLM与搜索提供方（环境变量）
```
# LLM（默认使用本地 Ollama）
export LLM_PROVIDER=ollama
export LLM_MODEL=qwen2.5:7b
# 如使用OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# 搜索（默认 duckduckgo）；如有 Google Serper 可提升成功率
export SEARCH_PROVIDER=duckduckgo
export SERPER_API_KEY=your_serper_key_here

# 账户数据库（MongoDB）
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB="ai_trader"
```

## 命令行使用

- 搜索金融信息
```
python3 cli.py search "新能源与AI交叉行业最新进展"
```

- 查询报价
```
python3 cli.py quote --a 600519
python3 cli.py quote --hk 0700
```

- 账户操作与查看
```
python3 cli.py account --deposit 100000
python3 cli.py account --withdraw 5000
```

- 多智能体演示工作流（入金并下单）
```
python3 cli.py demo --topic "TMT与算力产业链" --deposit 1000000
```

## 说明
- 本系统不直接连接券商，账户模块为纸面仿真，后续可扩展真实券商API适配。
- 行情数据来源于公开接口，可能存在延迟与不完整。
- LLM默认调用本地 Ollama（需运行本地服务），如无LLM也可运行演示但建议使用LLM以获得更佳交互体验。