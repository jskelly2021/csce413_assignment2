from concurrent.futures import ThreadPoolExecutor, as_completed
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


def scan_range(target, start_port, end_port, timeout, threads):
    open_ports = []

    print(f"[*] Scanning {target} from port {start_port} to {end_port}")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(scan_port, target, port, timeout): port
            for port in range(start_port, end_port + 1)
        }

        for future in as_completed(futures):
            port = futures[future]
            try:
                is_open = future.result()
            except Exception as e:
                continue

            if is_open:
                print(f"    {target} {port}: open")
                open_ports.append(port)

    open_ports.sort()
    return open_ports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple port scanner")

    parser.add_argument("--target", help="Target hostname or IP address", required=True)
    parser.add_argument("--sport", type=int, default=1, help="Start port (default: 1)")
    parser.add_argument("--eport", type=int, default=65535, help="End port (default: 65535)")
    parser.add_argument("--timeout", type=float, default=1.0, help="Connection timeout in seconds (default: 1.0)")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads to use (default: 10)")

    return parser.parse_args()


def validate_args(args: argparse.Namespace):
    if args.sport < 1 or args.sport > 65535 or args.eport < 1 or args.eport > 65535:
        print("Error: Start and end port must be between 1 and 65535")
        sys.exit(1)

    if args.sport > args.eport:
        print("Error: Start port cannot be greater than end port")
        sys.exit(1)

    if args.timeout <= 0:
        print("Error: Timeout must be a positive number")
        sys.exit(1)

    if args.threads < 1:
        print("Error: Number of threads must be at least 1")
        sys.exit(1)


def main():
    args = parse_args()
    validate_args(args)

    print("Target:", args.target)
    print("Port range:", args.sport, "-", args.eport)
    print("Timeout:", args.timeout)
    print("Threads:", args.threads)
    print("-----------------------------\n")

    start_time = time.perf_counter()
    open_ports = scan_range(args.target, args.sport, args.eport, args.timeout, args.threads)
    end_time = time.perf_counter()

    print(f"\n[+] Scan complete!")
    print(f"[+] Found {len(open_ports)} open ports in {end_time - start_time:.2f} seconds")

    for port in open_ports:
        print(f"    Port {port}: open")


if __name__ == "__main__":
    main()
