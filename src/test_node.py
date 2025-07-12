import time
from minRTOS import Scheduler, Task
from minBlockchain import (
    BlockchainStateManager,
    consensus_task,
    tx_validation_task,
    contract_sandbox_task,
    network_task,
    api_task
)

def main():
    print("--- minRTOS Blockchain Node Simulation ---")
    scheduler = Scheduler()
    state_manager = BlockchainStateManager()
    difficulty = 3

    # Network: receive transactions
    net_task = Task("NetworkTask", lambda: network_task(state_manager), period=0.1, priority=5, max_runs=10)
    scheduler.add_task(net_task)

    # Validation: validate transactions
    validation_task = Task("TxValidationTask", lambda: tx_validation_task(state_manager), period=0.12, priority=6, max_runs=8)
    scheduler.add_task(validation_task)

    # Consensus: mine blocks
    consensus = Task("ConsensusTask", lambda: consensus_task(state_manager, difficulty), period=0.15, priority=7, max_runs=5)
    scheduler.add_task(consensus)

    # Contract: execute contract logic
    contract = Task("ContractSandboxTask", lambda: contract_sandbox_task("DemoContract", state_manager), period=0.13, priority=8, max_runs=6)
    scheduler.add_task(contract)

    # API: query blockchain state
    api = Task("APITask", lambda: api_task(state_manager), period=0.2, priority=4, max_runs=7)
    scheduler.add_task(api)

    scheduler.start()
    time.sleep(4)
    scheduler.stop_all()
    scheduler.join()
    print("--- Node Simulation End ---")

    print("\nBlockchain State:")
    print(f"Blocks: {len(state_manager.blocks)}")
    for block in state_manager.blocks:
        print(f"  Block {block.index}: Hash={block.hash}, TxCount={len(block.transactions)}")
    print(f"State: {state_manager.state}")
    print(f"Tx Pool: {state_manager.tx_pool}")

if __name__ == "__main__":
    main()