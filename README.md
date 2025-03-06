## minRTOS

A lightweight real-time operating system (RTOS) for Python, designed to utilize Python 3.14’s no-GIL threading for true parallel execution.

## Features

✅ Preemptive Scheduling (EDF & RMS)
✅ High-Precision Timing (using time.perf_counter())
✅ Event-Driven Tasks
✅ Dynamic Task Creation & Removal
✅ Task Deadline Enforcement
✅ Thread-Based Execution


---

## Installation

Clone the repository:
```bash
git clone https://github.com/Night-Trader-Dev/minRTOS.git
cd minRTOS
```
Ensure you are using Python 3.14+ (for no-GIL threading).


---

## Usage

1. Creating and Running Tasks

Create tasks and add them to the scheduler:
```python
import time
from minrtos import Scheduler, Task

def my_task():
    print("🔧 Task Running")
    time.sleep(0.5)

scheduler = Scheduler(scheduling_policy="EDF")
task1 = Task("Task1", my_task, period=1, priority=1, deadline=1.5)

scheduler.add_task(task1)
scheduler.start()

time.sleep(5)  
scheduler.stop_all()  # Stop all tasks
```

---

2. Event-Driven Tasks

Tasks can wait for an external trigger:
```python
def event_task():
    print("🔔 Event Task Triggered!")

event_driven_task = Task("EventTask", event_task, priority=3, event_driven=True)
scheduler.add_task(event_driven_task)

# Trigger the task manually
time.sleep(2)
scheduler.trigger_task("EventTask")
```

---

3. Removing Tasks Dynamically
```python
scheduler.remove_task("Task1")
```

---

Scheduler Policies

Earliest Deadline First (EDF)

Tasks with the earliest deadline run first.

Dynamically adjusts execution order at runtime.


Rate Monotonic Scheduling (RMS)

Shorter-period tasks get higher priority.


To use RMS:
```python
scheduler = Scheduler(scheduling_policy="RMS")
```

---

## Upcoming Features

🚀 Priority Inheritance for Mutexes
🚀 Time-Based Task Preemption
🚀 Interrupt-Based Scheduling


---

## License

This project is licensed under the MIT License.



