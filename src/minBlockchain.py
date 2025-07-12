import hashlib
import time
import random
from minMutex import Mutex

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
    tx = {'to': contract_name, 'amount': random.randint(1, 10)}
    state_manager.apply_transaction(tx)
    time.sleep(0.05)

# Network simulation
def network_task(state_manager):
    print("[Network] Simulating peer message...")
    tx = {'to': f'user{random.randint(1,5)}', 'amount': random.randint(1, 20)}
    state_manager.add_transaction(tx)
    time.sleep(0.03)

# API simulation
def api_task(state_manager):
    print("[API] Querying blockchain state...")
    print(f"[API] Current state: {state_manager.state}")
    time.sleep(0.02)
