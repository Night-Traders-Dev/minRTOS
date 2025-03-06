import random
import time
from collections import deque
from minRTOS import Task, Scheduler, Mutex

# Mutex for ensuring transaction safety
market_mutex = Mutex()

# Blockchain-like structure: each block contains transactions
BLOCKCHAIN = deque(maxlen=100)  # Keep last 100 blocks for simplicity

# Generate initial stock data (random initial supply)
STOCKS = {
    f"STK{i}": {
        "total_supply": random.randint(5000, 10000),
        "circulating_supply": random.randint(100, 5000),
        "price": random.uniform(50, 500),
    }
    for i in range(10)
}

# Generate client data
CLIENTS = {f"Client{i}": {"balance": random.uniform(1000, 10000), "portfolio": {}} for i in range(50)}

def create_block(transactions):
    """Creates a new block containing transactions."""
    with market_mutex:
        BLOCKCHAIN.append({
            "timestamp": time.time(),
            "transactions": transactions
        })

def process_transactions():
    """Processes transactions in the blockchain to update market data."""
    with market_mutex:
        for block in BLOCKCHAIN:
            for tx in block["transactions"]:
                stock = tx["stock"]
                amount = tx["amount"]
                action = tx["action"]

                if action == "buy":
                    STOCKS[stock]["circulating_supply"] -= amount  # Buying decreases available supply
                elif action == "sell":
                    STOCKS[stock]["circulating_supply"] += amount  # Selling increases supply

                # Adjust stock price based on supply and demand
                STOCKS[stock]["price"] = max(
                    1, 
                    (STOCKS[stock]["total_supply"] / max(1, STOCKS[stock]["circulating_supply"])) * 10
                )

class ClientTrader(Task):
    """Client trader task that buys and sells stocks."""
    def __init__(self, name):
        super().__init__(name, self.run, priority=2)

    def run(self):
        with market_mutex.enter(self.name):
            client = CLIENTS[self.name]
            stock = random.choice(list(STOCKS.keys()))
            action = random.choice(["buy", "sell"])
            amount = random.randint(1, 10)
            transactions = []

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

        self.sleep(random.uniform(0.5, 2))  # Non-blocking sleep

class MarketOutput(Task):
    """Periodic stock market summary."""
    def __init__(self):
        super().__init__("MarketOutput", self.run, period=3, priority=1)

    def run(self):
        process_transactions()
        print("\n📊 Stock Market Summary:")
        with market_mutex:
            for stock, data in STOCKS.items():
                held_by_clients = sum(client["portfolio"].get(stock, 0) for client in CLIENTS.values())
                print(f"{stock}: ${data['price']:.2f}, Supply: {data['circulating_supply']}, Held by Clients: {held_by_clients}")

if __name__ == "__main__":
    scheduler = Scheduler(scheduling_policy="EDF")

    # Add client trading tasks
    for client in CLIENTS.keys():
        scheduler.add_task(ClientTrader(client))

    # Add market summary output task
    scheduler.add_task(MarketOutput())

    # Start the scheduler in a separate thread
    import threading
    def run_scheduler():
        scheduler.start()

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Run for 20 seconds then stop
    time.sleep(20)
    scheduler.stop_all()

    print("✅ Stock Market Simulation Complete")
