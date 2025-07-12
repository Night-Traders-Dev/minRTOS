import time
import hashlib
import random
from minRTOS import Scheduler, Task, Mutex

class Block:
    def __init__(self, index, prev_hash, transactions):
        self.index = index
        self.prev_hash = prev_hash
        self.transactions = transactions
        self.nonce = 0
        self.hash = None
        self.timestamp = time.time()

    def compute_hash(self):
        block_string = f"{self.index}{self.prev_hash}{self.transactions}{self.nonce}{self.timestamp}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine(self, difficulty):
        prefix = '0' * difficulty
        while True:
            self.hash = self.compute_hash()
            if self.hash.startswith(prefix):
                break
            self.nonce += 1

class BlockchainStateManager:
    def __init__(self):
        self.state = {}
        self.blocks = []
        self.tx_pool = []
        self.lock = Mutex()

    def add_block(self, block):
        self.blocks.append(block)
        print(f"[Blockchain] Block {block.index} added. Hash: {block.hash}")

    def add_transaction(self, tx):
        self.tx_pool.append(tx)
        print(f"[Blockchain] Transaction added: {tx}")

    def apply_transaction(self, tx):
        # Simulate state update
        self.state[tx['to']] = self.state.get(tx['to'], 0) + tx['amount']
        print(f"[Blockchain] State updated: {tx['to']} -> {self.state[tx['to']]}")

# Consensus simulation (PoW)
def consensus_task(state_manager, difficulty):
    if not state_manager.tx_pool:
        print("[Consensus] No transactions to mine.")
        return
    block = Block(len(state_manager.blocks), state_manager.blocks[-1].hash if state_manager.blocks else '0'*64, list(state_manager.tx_pool))
    print(f"[Consensus] Mining block {block.index} with {len(block.transactions)} txs...")
    block.mine(difficulty)
    state_manager.add_block(block)
    state_manager.tx_pool.clear()

# Transaction validation
def tx_validation_task(state_manager):
    if not state_manager.tx_pool:
        print("[Validation] No transactions to validate.")
        return
    for tx in list(state_manager.tx_pool):
        if tx['amount'] <= 0:
            print(f"[Validation] Invalid transaction: {tx}")
            state_manager.tx_pool.remove(tx)
        else:
            print(f"[Validation] Transaction valid: {tx}")

# Contract execution sandbox
def contract_sandbox_task(contract_name, state_manager):
    print(f"[Sandbox] Executing contract: {contract_name}")
    # Simulate contract logic
    tx = {'to': contract_name, 'amount': random.randint(1, 10)}
    state_manager.apply_transaction(tx)
    time.sleep(0.05)

# Network simulation
def network_task(state_manager):
    print("[Network] Simulating peer message...")
    # Simulate receiving a transaction
    tx = {'to': f'user{random.randint(1,5)}', 'amount': random.randint(1, 20)}
    state_manager.add_transaction(tx)
    time.sleep(0.03)

# API simulation
def api_task(state_manager):
    print("[API] Querying blockchain state...")
    print(f"[API] Current state: {state_manager.state}")
    time.sleep(0.02)

def main():
    print("--- minRTOS Blockchain Test Start ---")
    scheduler = Scheduler()
    state_manager = BlockchainStateManager()
    difficulty = 3

    # Add network task
    net_task = Task("NetworkTask", lambda: network_task(state_manager), period=0.1, priority=5, max_runs=10)
    scheduler.add_task(net_task)

    # Add transaction validation task
    validation_task = Task("TxValidationTask", lambda: tx_validation_task(state_manager), period=0.12, priority=6, max_runs=8)
    scheduler.add_task(validation_task)

    # Add consensus (mining) task
    consensus = Task("ConsensusTask", lambda: consensus_task(state_manager, difficulty), period=0.15, priority=7, max_runs=5)
    scheduler.add_task(consensus)

    # Add contract sandbox task
    contract = Task("ContractSandboxTask", lambda: contract_sandbox_task("DemoContract", state_manager), period=0.13, priority=8, max_runs=6)
    scheduler.add_task(contract)

    # Add API task
    api = Task("APITask", lambda: api_task(state_manager), period=0.2, priority=4, max_runs=7)
    scheduler.add_task(api)

    scheduler.start()
    time.sleep(3.5)
    scheduler.stop_all()
    scheduler.join()
    print("--- minRTOS Blockchain Test End ---")

    print("\nBlockchain State:")
    print(f"Blocks: {len(state_manager.blocks)}")
    for block in state_manager.blocks:
        print(f"  Block {block.index}: Hash={block.hash}, TxCount={len(block.transactions)}")
    print(f"State: {state_manager.state}")
    print(f"Tx Pool: {state_manager.tx_pool}")

if __name__ == "__main__":
    main()
