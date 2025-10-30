from typing import List, Dict, Any
from .llm import LLM
from .search import search_finance
from .market import get_quote
from .broker import PaperBroker


class InfoAgent:

    def run(self, topic: str, max_results: int = 6) -> List[Dict[str, Any]]:
        return search_finance(topic, max_results=max_results)


class MarketAgent:

    def run(self, tickers: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        quotes = []
        for t in tickers:
            quotes.append(get_quote(t["symbol"], t["market"]))
        return quotes


class PortfolioAgent:

    def __init__(self, llm: LLM = None):
        self.llm = llm or LLM()

    def suggest_allocation(self,
                           research: List[Dict[str, Any]],
                           quotes: List[Dict[str, Any]],
                           goal: str = "稳健增值") -> str:
        msg = [
            {
                "role": "system",
                "content": "你是资深投研助理，结合研究结果与报价给出简明配置建议。"
            },
            {
                "role":
                "user",
                "content":
                f"目标: {goal}\n研究摘要: {research}\n报价: {quotes}\n请给出配置思路与权重建议（不超过200字）。"
            },
        ]
        return self.llm.chat(msg, temperature=0.2)


class ExecutionAgent:

    def __init__(self, broker: PaperBroker = None):
        self.broker = broker or PaperBroker()

    def buy(self,
            symbol: str,
            market: str,
            quantity: float,
            price: float = None):
        self.broker.place_order(symbol, market, "buy", quantity, price)

    def sell(self, symbol: str, market: str, quantity: float):
        self.broker.place_order(symbol, market, "sell", quantity)


class Coordinator:

    def __init__(self, llm: LLM = None, broker: PaperBroker = None):
        self.info = InfoAgent()
        self.market = MarketAgent()
        self.portfolio = PortfolioAgent(llm)
        self.exec = ExecutionAgent(broker)

    def demo_workflow(self,
                      topic: str,
                      targets: List[Dict[str, str]],
                      buy_plan: Dict[str, float],
                      deposit_amount: float = 1_000_000):
        # 1) 信息收集
        research = self.info.run(topic)
        # 2) 行情查询
        quotes = self.market.run(targets)
        # 3) 配置建议
        advice = self.portfolio.suggest_allocation(research, quotes)
        # 4) 执行计划
        self.exec.broker.deposit(deposit_amount)
        for t in targets:
            qn = buy_plan.get(t["symbol"]) or 0
            if qn > 0:
                price = None
                for q in quotes:
                    if (q.get("symbol", "").endswith(
                            t["symbol"])) or (q.get("symbol") == t["symbol"]):
                        price = q.get("price")
                        break
                if price:
                    self.exec.buy(t["symbol"], t["market"], qn, price=price)
        return {
            "research": research,
            "quotes": quotes,
            "advice": advice,
            "balance": self.exec.broker.get_balance(),
            "positions": self.exec.broker.get_positions(),
            "orders": self.exec.broker.get_orders(),
        }
