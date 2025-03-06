import time
from minRTOS import Scheduler, Task

def conveyor_task():
    print("🛠 Conveyor Belt Moving...")
    time.sleep(0.5)

def emergency_stop():
    print("⛔ Emergency Stop Activated!")

scheduler = Scheduler(scheduling_policy="EDF")

# Periodic conveyor belt task
scheduler.add_task(Task("ConveyorBelt", conveyor_task, period=1, deadline=1.2))

# Event-driven emergency stop task
stop_task = Task("EmergencyStop", emergency_stop, event_driven=True)
scheduler.add_task(stop_task)

scheduler.start()

# Simulating normal operation and an emergency stop event
time.sleep(3)
scheduler.trigger_task("EmergencyStop")  # Simulating emergency
time.sleep(2)

scheduler.stop_all()
