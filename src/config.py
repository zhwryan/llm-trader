import os
from dataclasses import dataclass


@dataclass
class Settings:
    # LLM配置
    llm_provider: str = os.environ.get("LLM_PROVIDER", "ollama")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    model_name: str = os.environ.get("LLM_MODEL", "qwen2.5:7b")

    # 搜索配置
    search_provider: str = os.environ.get("SEARCH_PROVIDER", "duckduckgo")
    serpapi_key: str = os.environ.get("SERPAPI_KEY", "")
    serper_api_key: str = os.environ.get("SERPER_API_KEY", "")
    bing_key: str = os.environ.get("BING_API_KEY", "")

    # 行情配置
    yf_proxy: str = os.environ.get("YF_PROXY", "")

    # 账户配置
    db_path: str = os.environ.get("BROKER_DB_PATH", "./ai_trader_data.db")
    mongo_uri: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    mongo_db: str = os.environ.get("MONGO_DB", "ai_trader")


settings = Settings()
