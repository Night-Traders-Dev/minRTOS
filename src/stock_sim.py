import random
import time
from collections import deque
from minRTOS import Task, Scheduler, Mutex

# Mutex to ensure safe transaction processing with priority inheritance
market_mutex = Mutex(enable_priority_inheritance=True)

# Blockchain-like ledger: Keeps the last 100 blocks of transactions
BLOCKCHAIN = deque(maxlen=100)

# Initialize stock market with 10 made-up stocks
STOCKS = {
    f"STK{i}": {
        "total_supply": random.randint(5000, 10000),
        "circulating_supply": random.randint(100, 5000),
        "price": random.uniform(50, 500),
    }
    for i in range(10)
}

# Generate 50 clients with random balances
CLIENTS = {
    f"Client{i}": {"balance": random.uniform(1000, 10000), "portfolio": {}} for i in range(50)
}

def create_block(transactions):
    """Creates a new block containing transactions."""
#    market_mutex.acquire()
    try:
        BLOCKCHAIN.append({
            "timestamp": time.time(),
            "transactions": transactions
        })
    finally:
        market_mutex.release()

def process_transactions():
    """Processes transactions from the blockchain and updates market data."""
#    market_mutex.acquire()
    try:
        for block in BLOCKCHAIN:
            for tx in block["transactions"]:
                stock = tx["stock"]
                amount = tx["amount"]
                action = tx["action"]

                if action == "buy":
                    STOCKS[stock]["circulating_supply"] -= amount
                elif action == "sell":
                    STOCKS[stock]["circulating_supply"] += amount

                # Price adjusts based on supply-demand ratio
                STOCKS[stock]["price"] = max(1, (STOCKS[stock]["total_supply"] / max(1, STOCKS[stock]["circulating_supply"])) * 10)
    finally:
        market_mutex.release()

class ClientTrader(Task):
    """A client that randomly buys and sells stocks."""
    def __init__(self, name):
        super().__init__(name, self.run, priority=2)

    def run(self):
        transactions = []
#        market_mutex.acquire()
        try:
            client = CLIENTS[self.name]
            stock = random.choice(list(STOCKS.keys()))
            action = random.choice(["buy", "sell"])
            amount = random.randint(1, 10)

            if action == "buy":
                cost = STOCKS[stock]["price"] * amount
                if client["balance"] >= cost:
                    client["balance"] -= cost
                    client["portfolio"][stock] = client["portfolio"].get(stock, 0) + amount
                    transactions.append({"client": self.name, "stock": stock, "amount": amount, "action": "buy"})
                    print(f"🟢 {self.name} bought {amount} of {stock} for ${cost:.2f}")

            elif action == "sell" and client["portfolio"].get(stock, 0) >= amount:
                client["balance"] += STOCKS[stock]["price"] * amount
                client["portfolio"][stock] -= amount
                transactions.append({"client": self.name, "stock": stock, "amount": amount, "action": "sell"})
                print(f"🔴 {self.name} sold {amount} of {stock}")

            if transactions:
                create_block(transactions)
        finally:
            market_mutex.release()

        time.sleep(random.uniform(0.5, 2))

class MarketOutput(Task):
    """Outputs market summary periodically."""
    def __init__(self):
        super().__init__("MarketOutput", self.run, period=3, priority=1)

    def run(self):
        process_transactions()
        print("\n📊 Stock Market Summary:")
#        market_mutex.acquire()
        try:
            for stock, data in STOCKS.items():
                held_by_clients = sum(client["portfolio"].get(stock, 0) for client in CLIENTS.values())
                print(f"{stock}: ${data['price']:.2f}, Supply: {data['circulating_supply']}, Held by Clients: {held_by_clients}")
        finally:
            market_mutex.release()

if __name__ == "__main__":
    scheduler = Scheduler(scheduling_policy="EDF")

    # Add client trading tasks
    for client in CLIENTS.keys():
        scheduler.add_task(ClientTrader(client))

    # Add market summary task
    scheduler.add_task(MarketOutput())

    # Start scheduler
    scheduler.start()

    # Run simulation for 20 seconds
    time.sleep(20)
    scheduler.stop_all()
    print("✅ Stock Market Simulation Complete")
