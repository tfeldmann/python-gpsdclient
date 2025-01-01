import socket
import threading
import time
from pathlib import Path

VERSION_HEADER = '{"class":"VERSION","release":"3.17","rev":"3.17","proto_major":3,"proto_minor":12}\n'
WATCH_COMMAND = '?WATCH={"enable":true,"json":true}\n'
WATCH_COMMAND_WITH_PPS = '?WATCH={"enable":true,"json":true,"pps":true}\n'
GPSD_OUTPUT = Path("tests/example_output.jsonl").read_text()


def fake_server() -> None:
    addr = ("127.0.0.1", 20000)
    if hasattr(socket, "create_server"):
        sock = socket.create_server(address=addr, reuse_port=True)
    else:
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(addr)
        sock.listen(1)
    client, _ = sock.accept()
    client.send(VERSION_HEADER.encode("utf-8"))
    buffer = b""
    while not buffer.decode("utf-8").endswith("\n"):
        buffer += client.recv(1)
    if buffer.decode("utf-8") in [WATCH_COMMAND, WATCH_COMMAND_WITH_PPS]:
        n = 120
        # Send back the output in 120 byte chunks
        if buffer.decode("utf-8") == WATCH_COMMAND:
            output = Path("tests/example_output.jsonl").read_text()
        elif buffer.decode("utf-8") == WATCH_COMMAND_WITH_PPS:
            output = Path("tests/example_output_with_toff.jsonl").read_text()
        else:
            output = ""

        for chunk in [output[i : i + n] for i in range(0, len(output), n)]:
            client.send(chunk.encode("utf-8"))
            time.sleep(0.001)


def main() -> None:
    server = threading.Thread(target=fake_server)
    server.start()


if __name__ == "__main__":
    main()
