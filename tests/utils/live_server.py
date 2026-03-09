import socket
import time

import httpx
import uvicorn


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def wait_for_server(base_url: str, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if is_port_open("127.0.0.1", 8005):
                r = httpx.get(f"{base_url}/api/v1/health", timeout=1.0)
                if r.status_code == 200:
                    return
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError("Server did not start in time")


def run_server():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8005, log_level="warning")