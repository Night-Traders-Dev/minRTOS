import time
import socket
from minRTOS import Task, Scheduler

def http_server_task():
    """Simple HTTP server running as a minRTOS task."""
    print("🌐 HTTP Server Task Starting...")

    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 8080))  # Listen on port 8080
    server_socket.listen(5)

    print("✅ HTTP Server Listening on port 8080...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"📡 Connection from {client_address}")

            request = client_socket.recv(1024).decode("utf-8")
            if request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello from minRTOS HTTP Server!"
                client_socket.sendall(response.encode("utf-8"))

            client_socket.close()
    except KeyboardInterrupt:
        print("🛑 HTTP Server Stopping...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # Initialize minRTOS Scheduler
    scheduler = Scheduler(scheduling_policy="EDF")

    # Create HTTP server task
    http_task = Task(name="HTTPServer", update_func=http_server_task, priority=3)
    
    # Add task to scheduler
    scheduler.add_task(http_task)

    # Start scheduler
    scheduler.start()

    # Run for 10 seconds, then stop everything
    time.sleep(10)
    scheduler.stop_all()

    print("✅ HTTP Server Task Stopped")
