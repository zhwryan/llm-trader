# AI量化个人交易系统（LLM驱动，Python）

此项目为个人量化/交易实践的最小可用系统，包含：
- 金融信息搜索能力（DuckDuckGo解析，后续可接入 Bing/SerpAPI）
- A股与港股行情获取（yfinance 优先，回退 Yahoo Quote API）
- 本地纸面交易账户（MongoDB）
- 基于LLM的多智能体协作（信息→行情→组合→执行的闭环）
