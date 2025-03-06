import time
from minRTOS import Task, Scheduler

# Dictionary to store active tasks
TASK_TABLE = {}
scheduler = Scheduler(scheduling_policy="EDF")

def process_monitor_task():
    """Monitors and displays process statuses in minRTOS"""
    while True:
        print("\n=== Process Monitor ===")
        for task_id, task in TASK_TABLE.items():
            print(f"[{task_id}] {task.name} | Priority: {task.priority}")
        time.sleep(5)

def example_task(name):
    """Dummy task to simulate a running process"""
    while True:
        print(f"[{name}] Running...")
        time.sleep(3)

def example_task_runner(name):
    """Wrapper function for example_task"""
    example_task(name)

def run_shell():
    """Runs the shell in the main process"""
    while True:
        command = input("minRTOS> ").strip().split()
        if not command:
            continue

        cmd = command[0]

        if cmd == "ps":
            print("\nProcess List:")
            for task_id, task in TASK_TABLE.items():
                print(f"[{task_id}] {task.name}, Priority: {task.priority}")

        elif cmd == "kill" and len(command) > 1:
            task_id = command[1]
            if task_id in TASK_TABLE:
                scheduler.remove_task(TASK_TABLE[task_id])  # Properly remove task
                del TASK_TABLE[task_id]
                print(f"Task {task_id} terminated.")
            else:
                print(f"Task {task_id} not found.")

        elif cmd == "priority" and len(command) > 2:
            task_id, new_priority = command[1], int(command[2])
            if task_id in TASK_TABLE:
                TASK_TABLE[task_id].priority = new_priority
                print(f"Task {task_id} priority changed to {new_priority}.")
            else:
                print(f"Task {task_id} not found.")

        elif cmd == "exit":
            print("Shutting down...")
            break

        else:
            print("Unknown command. Available commands: ps, kill <task_id>, priority <task_id> <new_priority>, exit")

        time.sleep(0.1)  # Prevent busy waiting

if __name__ == "__main__":
    # Add process monitor task
    monitor = Task("ProcessMonitor", process_monitor_task, priority=1, period=5)
    TASK_TABLE["monitor"] = monitor
    scheduler.add_task(monitor)

    # Add example tasks
    for i in range(3):
        task_name = f"Task{i}"
        task = Task(task_name, example_task_runner, priority=2, args=(task_name,))
        TASK_TABLE[str(i)] = task
        scheduler.add_task(task)

    # Start minRTOS scheduler
    scheduler.start()

    # Run shell in main process
    run_shell()

    # Stop scheduler before exiting
    scheduler.stop_all()
