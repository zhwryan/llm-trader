import requests
from typing import List, Dict
from .config import settings


class LLM:
    """统一的LLM接口，支持OpenAI与本地Ollama，其他可扩展"""

    def __init__(self, model: str = None, provider: str = None):
        self.model = model or settings.model_name
        self.provider = (provider or settings.llm_provider).lower()

    def chat(self,
             messages: List[Dict[str, str]],
             temperature: float = 0.3) -> str:
        if self.provider == "openai" and settings.openai_api_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            try:
                r = requests.post(url,
                                  json=payload,
                                  headers=headers,
                                  timeout=30)
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                return f"[LLM error] {e}"
        elif self.provider == "ollama":
            # 将messages拼接为prompt
            prompt = "\n\n".join(
                [f'{m["role"]}: {m["content"]}' for m in messages])
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature
            }
            try:
                r = requests.post(url, json=payload, timeout=30)
                r.raise_for_status()
                data = r.json()
                return data.get("response", "")
            except Exception as e:
                return f"[LLM error] {e}"
        else:
            # 简单回退：拼接用户消息（便于无LLM时调试）
            return "\n".join(
                [m["content"] for m in messages if m["role"] == "user"])
