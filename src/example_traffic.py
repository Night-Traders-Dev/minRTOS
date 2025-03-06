import time
from minRTOS import Scheduler, Task

traffic_light_state = "🔴 RED"

def update_traffic_light():
    """Simulate traffic light change."""
    global traffic_light_state
    if traffic_light_state == "🔴 RED":
        traffic_light_state = "🟡 YELLOW"
    elif traffic_light_state == "🟡 YELLOW":
        traffic_light_state = "🟢 GREEN"
    else:
        traffic_light_state = "🔴 RED"
    
    print(f"🚦 Traffic Light: {traffic_light_state}")

def emergency_vehicle_pass():
    """Handles emergency vehicle priority."""
    global traffic_light_state
    print("🚑 Emergency Vehicle Detected! Turning GREEN.")
    traffic_light_state = "🟢 GREEN"

scheduler = Scheduler(scheduling_policy="EDF")

# Periodic task: Traffic light updates every 3 seconds
scheduler.add_task(Task("TrafficLight", update_traffic_light, period=3, deadline=3.5))

# Event-driven task: Emergency vehicle priority
scheduler.add_task(Task("EmergencyPass", emergency_vehicle_pass, event_driven=True))

scheduler.start()

# Simulate normal operation with an emergency event
time.sleep(6)
scheduler.trigger_task("EmergencyPass")
time.sleep(5)

scheduler.stop_all()
