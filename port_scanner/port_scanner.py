import argparse
import socket


def scan_port(target, port, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((target, port))
            print(f"[*] Port {port}: open")
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        print(f"[*] Port {port}: timeout or closed")
        return False


def scan_range(target, start_port, end_port, timeout):
    open_ports = []

    print(f"[*] Scanning {target} from port {start_port} to {end_port}")

    for port in range(start_port, end_port + 1):
        if scan_port(target, port, timeout):
            open_ports.append(port)

    return open_ports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple port scanner")

    parser.add_argument("--target", help="Target hostname or IP address", required=True)
    parser.add_argument("--start", type=int, default=1, help="Start port (default: 1)")
    parser.add_argument("--end", type=int, default=1024, help="End port (default: 1024)")
    parser.add_argument("--timeout", type=float, default=1.0, help="Connection timeout in seconds (default: 1.0)")

    return parser.parse_args()


def main():
    args = parse_args()

    print("Target:", args.target)
    print("Port range:", args.start, "-", args.end)
    print("Timeout:", args.timeout)

    open_ports = scan_range(args.target, args.start, args.end, args.timeout)

    print(f"\n[+] Scan complete!")
    print(f"[+] Found {len(open_ports)} open ports:")

    for port in open_ports:
        print(f"    Port {port}: open")


if __name__ == "__main__":
    main()
