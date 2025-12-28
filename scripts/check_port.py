
import socket

host = "dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com"
port = 5432

def check_port():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"Port {port} is OPEN")
        else:
            print(f"Port {port} is CLOSED or BLOCKED (result: {result})")
        sock.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_port()
