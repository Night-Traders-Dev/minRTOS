import time
from minRTOS import Scheduler, Task

# Task functions
def fast_task():
    print("⚡ Fast task running")
    time.sleep(0.1)  

def slow_task():
    print("🐢 Slow task running")
    time.sleep(1.5)  

def event_task():
    print("🔔 Event Task Triggered!")

# Create scheduler with EDF
scheduler = Scheduler(scheduling_policy="EDF")

# Add tasks with different deadlines
scheduler.add_task(Task("FastTask", fast_task, period=0.5, priority=1, deadline=1))
scheduler.add_task(Task("SlowTask", slow_task, period=2, priority=2, deadline=1.2, overrun_action="kill"))
event_driven_task = Task("EventTask", event_task, priority=3, event_driven=True)
scheduler.add_task(event_driven_task)

scheduler.start()

# Trigger the event-driven task only ONCE
time.sleep(2)
scheduler.trigger_task("EventTask")

# Remove the slow task dynamically
time.sleep(1)
scheduler.remove_task("SlowTask")

# Stop all tasks
time.sleep(2)
scheduler.stop_all()
