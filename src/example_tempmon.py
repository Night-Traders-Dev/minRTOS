import time
import random
from minRTOS import Scheduler, Task

# Shared temperature value
temperature = 25  

def read_temperature():
    """Simulate temperature reading from a sensor."""
    global temperature
    temperature = random.uniform(20, 40)
    print(f"🌡 Temperature Reading: {temperature:.2f}°C")

def alert_task():
    """Trigger an alert if temperature is too high."""
    print("🚨 ALERT! High temperature detected!")

scheduler = Scheduler(scheduling_policy="EDF")

# Periodic task: Reads temperature every 1 second
scheduler.add_task(Task("TemperatureSensor", read_temperature, period=1, deadline=1.2))

# Event-driven task: Triggers alert when needed
alert_event_task = Task("AlertTask", alert_task, event_driven=True)
scheduler.add_task(alert_event_task)

scheduler.start()

# Simulate monitoring
for _ in range(10):
    time.sleep(1)
    if temperature > 35:  
        scheduler.trigger_task("AlertTask")  

scheduler.stop_all()
