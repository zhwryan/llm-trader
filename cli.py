import argparse
from src.search import search_finance
from src.market import get_quote
from src.broker import PaperBroker
from src.agents import Coordinator


def cmd_search(args):
    results = search_finance(args.query, max_results=args.top)
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['title']}\n{r['url']}\n{r['snippet']}\n")


def cmd_quote(args):
    if args.a:
        q = get_quote(args.a, "A")
    elif args.hk:
        q = get_quote(args.hk, "HK")
    else:
        print("请提供 --a 或 --hk 代码")
        return
    print(q)


def cmd_account(args):
    b = PaperBroker()
    if args.deposit:
        b.deposit(args.deposit)
    if args.withdraw:
        try:
            b.withdraw(args.withdraw)
        except Exception as e:
            print("取款失败:", e)
    print("现金余额:", b.get_balance())
    print("持仓:", b.get_positions())
    print("订单:", b.get_orders())


def cmd_demo(args):
    coor = Coordinator()
    targets = [
        {
            "symbol": "600519",
            "market": "A"
        },  # 贵州茅台
        {
            "symbol": "0700",
            "market": "HK"
        },  # 腾讯控股
    ]
    buy_plan = {"600519": 10, "0700": 10}
    result = coor.demo_workflow(topic=args.topic,
                                targets=targets,
                                buy_plan=buy_plan,
                                deposit_amount=args.deposit)
    print("研究结果(Top):")
    for i, r in enumerate(result["research"][:5], 1):
        print(f"[{i}] {r['title']} -> {r['url']}")
    print("\n报价:")
    for q in result["quotes"]:
        print(q)
    print("\n组合建议:\n", result["advice"])
    print("\n现金余额:", result["balance"])
    print("持仓:", result["positions"])
    print("订单:", result["orders"])


def main():
    parser = argparse.ArgumentParser(description="AI量化交易系统CLI")
    sub = parser.add_subparsers()

    p1 = sub.add_parser("search", help="搜索金融信息")
    p1.add_argument("query")
    p1.add_argument("--top", type=int, default=6)
    p1.set_defaults(func=cmd_search)

    p2 = sub.add_parser("quote", help="查询A股/HK报价")
    g = p2.add_mutually_exclusive_group()
    g.add_argument("--a", help="A股代码，如600519")
    g.add_argument("--hk", help="港股代码，如0700")
    p2.set_defaults(func=cmd_quote)

    p3 = sub.add_parser("account", help="账户操作与查看")
    p3.add_argument("--deposit", type=float, help="入金金额")
    p3.add_argument("--withdraw", type=float, help="出金金额")
    p3.set_defaults(func=cmd_account)

    p4 = sub.add_parser("demo", help="多智能体演示工作流")
    p4.add_argument("--topic", default="新能源与AI交叉行业最新进展")
    p4.add_argument("--deposit", type=float, default=1_000_000)
    p4.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
