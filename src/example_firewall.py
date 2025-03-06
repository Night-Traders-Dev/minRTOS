import time
import random
from minRTOS import Scheduler, Task

def packet_checker():
    """Simulated packet inspection."""
    packet_id = random.randint(1000, 9999)
    threat_detected = random.choice([False, False, False, True])  # 25% chance of a threat
    print(f"📡 Packet {packet_id} checked. Threat: {'YES' if threat_detected else 'NO'}")
    
    if threat_detected:
        scheduler.trigger_task("ThreatLogger")

def log_threat():
    """Logs a detected threat."""
    print("⚠️ Security Alert: Suspicious packet detected!")

scheduler = Scheduler(scheduling_policy="EDF")

# Periodic task: Network packet inspection
scheduler.add_task(Task("PacketChecker", packet_checker, period=1, deadline=1.5))

# Event-driven task: Threat logger
scheduler.add_task(Task("ThreatLogger", log_threat, event_driven=True))

scheduler.start()
time.sleep(10)  # Simulate 10 seconds of packet processing
scheduler.stop_all()
