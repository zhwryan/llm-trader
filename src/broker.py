from typing import Dict, List, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from .config import settings
from .market import get_quote


class PaperBroker:
    """本地纸面交易账户（MongoDB），支持入金、下单、持仓与订单记录"""

    def __init__(self, mongo_uri: str = None, db_name: str = None):
        self.mongo_uri = mongo_uri or settings.mongo_uri
        self.db_name = db_name or settings.mongo_db
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self._init_db()

    def _init_db(self):
        # 唯一索引：持仓按 symbol 唯一
        self.db.positions.create_index([("symbol", ASCENDING)], unique=True)
        # 初始化账户文档（仅首次插入）
        self.db.account.update_one({"_id": 1}, {"$setOnInsert": {
            "cash": 0.0
        }},
                                   upsert=True)

    def get_balance(self) -> float:
        doc = self.db.account.find_one({"_id": 1})
        return float(doc.get("cash", 0.0)) if doc else 0.0

    def deposit(self, amount: float):
        self.db.account.update_one({"_id": 1},
                                   {"$inc": {
                                       "cash": float(amount)
                                   }},
                                   upsert=True)

    def withdraw(self, amount: float):
        bal = self.get_balance()
        if amount > bal:
            raise ValueError("Insufficient cash")
        self.db.account.update_one({"_id": 1},
                                   {"$inc": {
                                       "cash": -float(amount)
                                   }})

    def get_positions(self) -> List[Dict[str, Any]]:
        rows = list(self.db.positions.find({}, {"_id": 0}))
        # 直接返回需要的字段
        return [{
            "symbol": r.get("symbol"),
            "market": r.get("market"),
            "quantity": float(r.get("quantity", 0.0)),
            "avg_price": float(r.get("avg_price", 0.0)),
        } for r in rows]

    def place_order(
        self,
        symbol: str,
        market: str,
        side: str,
        quantity: float,
        price: float = None,
    ):
        side = side.lower()
        if side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        if price is None:
            q = get_quote(symbol, market)
            if not q.get("price"):
                raise ValueError("No price available")
            price = float(q["price"])

        quantity = float(quantity)
        price = float(price)
        cost = price * quantity

        # 注意：未使用事务（本地单机默认无副本集），顺序执行保持简单一致性
        if side == "buy":
            # 资金充足校验
            if cost > self.get_balance():
                raise ValueError("Insufficient cash")
            # 减少账户现金
            self.db.account.update_one({"_id": 1}, {"$inc": {"cash": -cost}})
            # 更新/插入持仓与均价
            pos = self.db.positions.find_one({"symbol": symbol})
            if pos:
                old_q = float(pos.get("quantity", 0.0))
                old_avg = float(pos.get("avg_price", 0.0))
                new_q = old_q + quantity
                new_avg = (old_q * old_avg +
                           cost) / new_q if new_q > 0 else price
                self.db.positions.update_one(
                    {"symbol": symbol},
                    {"$set": {
                        "quantity": new_q,
                        "avg_price": new_avg
                    }},
                )
            else:
                self.db.positions.update_one(
                    {"symbol": symbol},
                    {
                        "$set": {
                            "symbol": symbol,
                            "market": market.upper(),
                            "quantity": quantity,
                            "avg_price": price,
                        }
                    },
                    upsert=True,
                )
        else:  # sell
            pos = self.db.positions.find_one({"symbol": symbol})
            if not pos:
                raise ValueError("Insufficient position")
            old_q = float(pos.get("quantity", 0.0))
            if old_q < quantity:
                raise ValueError("Insufficient position")
            new_q = old_q - quantity
            proceeds = price * quantity
            # 增加账户现金
            self.db.account.update_one({"_id": 1},
                                       {"$inc": {
                                           "cash": proceeds
                                       }})
            # 更新/删除持仓
            if new_q == 0:
                self.db.positions.delete_one({"symbol": symbol})
            else:
                self.db.positions.update_one({"symbol": symbol},
                                             {"$set": {
                                                 "quantity": new_q
                                             }})

        # 记录订单
        self.db.orders.insert_one({
            "symbol": symbol,
            "market": market.upper(),
            "side": side,
            "quantity": quantity,
            "price": price,
            "ts": datetime.utcnow(),
        })

    def get_orders(self) -> List[Dict[str, Any]]:
        rows = list(self.db.orders.find({}, sort=[("_id", -1)]))
        result = []
        for r in rows:
            result.append({
                "id": str(r.get("_id")),
                "symbol": r.get("symbol"),
                "market": r.get("market"),
                "side": r.get("side"),
                "quantity": float(r.get("quantity", 0.0)),
                "price": float(r.get("price", 0.0)),
                "ts": r.get("ts"),
            })
        return result
