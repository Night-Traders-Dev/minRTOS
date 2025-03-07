import time
import multiprocessing
from minRTOS import Scheduler, Task

scheduler = Scheduler(scheduling_policy="EDF")

# Shared integer counter for task executions
task_timer = multiprocessing.Value('i', 0)  # 'i' -> shared integer

def my_task():
    with task_timer.get_lock():  # Ensure atomic access
        print(f"Task Timer: {task_timer.value}")
        
        if task_timer.value >= 3:  # Stop after 10 tasks
            print("🛑 Stopping minRTOS...")
            scheduler.stop_all()  # Stop all tasks safely
            return
        
        print("🔧 Task Running")
        time.sleep(0.5)
        
        task_timer.value += 1  # Increment task count
        
        # Remove old task and add a new one with an updated name
        task_name = f"Task{task_timer.value}"
        scheduler.remove_task(f"Task{task_timer.value - 1}")
        new_task = Task(task_name, my_task, period=1, priority=1, deadline=1.5)
        scheduler.add_task(new_task)

if __name__ == "__main__":
    initial_task = Task(f"Task{task_timer.value}", my_task, period=1, priority=1, deadline=1.5)
    scheduler.add_task(initial_task)
    scheduler.start()
    
    # Wait for scheduler to finish
    scheduler.join()
    
    print("✅ All tasks stopped successfully.")
