import time
from minRTOS import Scheduler, Task, Mutex

def simple_update():
    print("Task is running.")
    time.sleep(0.05)

def deadline_update():
    print("Deadline task running.")
    time.sleep(0.2)  # Intentionally longer than deadline

def mutex_update(mutex, name):
    print(f"{name} attempting to acquire mutex...")
    acquired = mutex.acquire(task=Task(name, lambda: None))
    if acquired:
        print(f"{name} acquired mutex!")
        time.sleep(0.1)
        mutex.release()
        print(f"{name} released mutex!")
    else:
        print(f"{name} failed to acquire mutex!")

def blockchain_contract_update(contract_name, state):
    print(f"[Blockchain] Executing contract: {contract_name}, current state: {state['value']}")
    # Simulate contract logic: increment state, check for overflow
    state['value'] += 1
    if state['value'] > 5:
        print(f"[Blockchain] {contract_name} state overflow!")
        raise Exception("State overflow")
    time.sleep(0.07)

def blockchain_event_update(contract_name, event_queue):
    if not event_queue:
        print(f"[Blockchain] {contract_name} waiting for event...")
        return
    event = event_queue.pop(0)
    print(f"[Blockchain] {contract_name} processing event: {event}")
    time.sleep(0.05)

def main():
    print("--- minRTOS Test Start ---")
    scheduler = Scheduler()

    # Test: Add a simple periodic task
    task1 = Task("SimpleTask", simple_update, period=0.1, priority=2, max_runs=3)
    scheduler.add_task(task1)

    # Test: Add a deadline task (should be killed after deadline overrun)
    task2 = Task("DeadlineTask", deadline_update, period=0.1, priority=1, deadline=0.1, overrun_action="kill", max_runs=2)
    scheduler.add_task(task2)

    # Test: Mutex with two tasks
    mutex = Mutex()
    def mutex_task1():
        mutex_update(mutex, "MutexTask1")
    def mutex_task2():
        mutex_update(mutex, "MutexTask2")
    mtask1 = Task("MutexTask1", mutex_task1, period=0.15, priority=3, max_runs=2)
    mtask2 = Task("MutexTask2", mutex_task2, period=0.15, priority=4, max_runs=2)
    scheduler.add_task(mtask1)
    scheduler.add_task(mtask2)

    # Blockchain contract simulation: stateful contract
    contract_state = {'value': 0}
    def contract_task():
        blockchain_contract_update("DemoContract", contract_state)
    contract = Task("DemoContractTask", contract_task, period=0.12, priority=5, max_runs=7)
    scheduler.add_task(contract)

    # Blockchain event-driven contract
    event_queue = ["Deposit", "Withdraw", "Transfer"]
    def event_contract_task():
        blockchain_event_update("EventContract", event_queue)
    event_contract = Task("EventContractTask", event_contract_task, period=0.09, priority=6, max_runs=5)
    scheduler.add_task(event_contract)

    # Edge case: contract with zero period (should run once)
    def zero_period_contract():
        print("[Blockchain] Zero period contract executed.")
    zero_contract = Task("ZeroPeriodContract", zero_period_contract, period=0, priority=7, max_runs=1)
    scheduler.add_task(zero_contract)

    # Edge case: contract with missed deadline and pause
    def slow_contract():
        print("[Blockchain] Slow contract running.")
        time.sleep(0.2)
    slow_contract_task = Task("SlowContractTask", slow_contract, period=0.1, priority=8, deadline=0.1, overrun_action="pause", max_runs=2)
    scheduler.add_task(slow_contract_task)

    scheduler.start()
    time.sleep(3)  # Let tasks run
    scheduler.stop_all()
    scheduler.join()
    print("--- minRTOS Test End ---")

    # Print metrics for all tasks
    print("\nTask Metrics:")
    for tname, task in scheduler.tasks.items():
        print(f"Task: {tname}")
        for k, v in task.metrics.items():
            print(f"  {k}: {v}")
        if tname == "DemoContractTask":
            print(f"  Final contract state: {contract_state['value']}")
        if tname == "EventContractTask":
            print(f"  Remaining events: {event_queue}")

if __name__ == "__main__":
    main()
