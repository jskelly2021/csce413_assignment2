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
                open_ports.append(port)

    open_ports.sort()
    return open_ports


def grab_banner(target, port, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((target, port))
            banner = s.recv(1024).decode().strip()
            return banner
    except (socket.timeout, ConnectionRefusedError, OSError):
        return "no banner"


def grab_banners(target, ports, timeout=2.0, threads=10):
    banners = {}

    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures  = {
            ex.submit(grab_banner, target, port, timeout): port
            for port in ports
        }

        for future in as_completed(futures):
            port = futures[future]
            try:
                banners[(target, port)] = future.result()
            except Exception as e:
                banners[(target, port)] = "no banner"
                continue

    return banners


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple port scanner")

    parser.add_argument("targets", nargs="+", help="Target hostname(s) or IP address(es)")
    parser.add_argument("-sp", type=int, default=1, help="Start port (default: 1)")
    parser.add_argument("-ep", type=int, default=65535, help="End port (default: 65535)")
    parser.add_argument("-t", type=float, default=1.0, help="Connection timeout in seconds (default: 1.0)")
    parser.add_argument("-nb", action="store_true", help="Disable service discovery (banner grabbing)")
    parser.add_argument("-threads", type=int, default=10, help="Number of threads to use (default: 10)")

    return parser.parse_args()


def validate_args(args: argparse.Namespace):
    if args.sp < 1 or args.sp > 65535 or args.ep < 1 or args.ep > 65535:
        print("Error: Start and end port must be between 1 and 65535")
        sys.exit(1)

    if args.sp > args.ep:
        print("Error: Start port cannot be greater than end port")
        sys.exit(1)

    if args.t <= 0:
        print("Error: Timeout must be a positive number")
        sys.exit(1)

    if args.threads < 1:
        print("Error: Number of threads must be at least 1")
        sys.exit(1)


def main():
    args = parse_args()
    validate_args(args)

    open_ports = {}
    scan_times = {}
    banners = {}

    print("Port range:", args.sp, "-", args.ep)
    print("Timeout:", args.t)
    print("Banner grabbing:", "enabled" if args.nb else "disabled")
    print("Threads:", args.threads)
    print("-----------------------------")

    for target in args.targets:
        print(f"\n[*] Scanning {target} from port {args.sp} to {args.ep}")

        start_time = time.perf_counter()
        open_ports[target] = scan_range(target, args.sp, args.ep, args.t, args.threads)
        end_time = time.perf_counter()

        scan_times[target] = end_time - start_time
        print(f"    Found {len(open_ports[target])} open ports in {scan_times[target]:.2f} seconds")

    if not args.nb:
        for target, ports in open_ports.items():
            if not ports:
                continue
            banners.update(grab_banners(target, ports, args.t))

    print(f"\n[*] Scan complete! ({sum(scan_times.values()):.2f} seconds)")

    for target in open_ports:
        print(f"[{target}]")
        print(f"    {'PORT':<8}{'STATE':<8}{'SERVICE':<8}")

        for port in open_ports[target]:
            banner = banners.get((target, port), "unknown")
            print(f"    {port:<8}{'open':<8}{banner:<8}")

if __name__ == "__main__":
    main()
