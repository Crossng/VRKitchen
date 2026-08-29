import argparse
import json
import os
import socket
import struct
import sys
import uuid


def recv_exact(sock, size):
    chunks = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("socket closed before full frame was received")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_request(host, port, payload, timeout):
    body = json.dumps(payload).encode("utf-8")
    frame = struct.pack(">I", len(body)) + body
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(frame)
        header = recv_exact(sock, 4)
        length = struct.unpack(">I", header)[0]
        response_body = recv_exact(sock, length)
    return json.loads(response_body.decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="UnrealBridge TCP 客户端")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--token",
        default=None,
        help="鉴权 token；设置 UNREAL_BRIDGE_TOKEN 后可省略。",
    )
    parser.add_argument("--ping", action="store_true")
    parser.add_argument("--script")
    parser.add_argument("--script-file")
    args = parser.parse_args()
    token = args.token if args.token is not None else os.environ.get("UNREAL_BRIDGE_TOKEN", "")

    if args.ping:
        payload = {"id": str(uuid.uuid4()), "command": "ping"}
    else:
        if bool(args.script) == bool(args.script_file):
            parser.error("provide exactly one of --script or --script-file unless --ping is used")
        script = args.script
        if args.script_file:
            with open(args.script_file, "r", encoding="utf-8") as f:
                script = f.read()
        payload = {"id": str(uuid.uuid4()), "script": script, "timeout": args.timeout}

    if token:
        payload["token"] = token

    response = send_request(args.host, args.port, payload, args.timeout)
    json.dump(response, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
