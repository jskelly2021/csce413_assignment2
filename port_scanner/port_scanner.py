import argparse
import socket
import time
import sys

def scan_port(target, port, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((target, port))
            s.close()
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def scan_range(target, start_port, end_port, timeout):
    open_ports = []

    print(f"[*] Scanning {target} from port {start_port} to {end_port}")

    for port in range(start_port, end_port + 1):
        if scan_port(target, port, timeout):
            print(f"    {target} {port}: open")
            open_ports.append(port)

    return open_ports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple port scanner")

    parser.add_argument("--target", help="Target hostname or IP address", required=True)
    parser.add_argument("--start", type=int, default=1, help="Start port (default: 1)")
    parser.add_argument("--end", type=int, default=65535, help="End port (default: 65535)")
    parser.add_argument("--timeout", type=float, default=1.0, help="Connection timeout in seconds (default: 1.0)")

    return parser.parse_args()


def validate_args(args: argparse.Namespace):
    if args.start < 1 or args.start > 65535 or args.end < 1 or args.end > 65535:
        print("Error: Start and end port must be between 1 and 65535")
        sys.exit(1)

    if args.start > args.end:
        print("Error: Start port cannot be greater than end port")
        sys.exit(1)

    if args.timeout <= 0:
        print("Error: Timeout must be a positive number")
        sys.exit(1)


def main():
    args = parse_args()
    validate_args(args)

    print("Target:", args.target)
    print("Port range:", args.start, "-", args.end)
    print("Timeout:", args.timeout)
    print("-----------------------------\n")

    start_time = time.perf_counter()
    open_ports = scan_range(args.target, args.start, args.end, args.timeout)
    end_time = time.perf_counter()

    print(f"\n[+] Scan complete!")
    print(f"[+] Found {len(open_ports)} open ports in {end_time - start_time:.2f} seconds")

    for port in open_ports:
        print(f"    Port {port}: open")


if __name__ == "__main__":
    main()
