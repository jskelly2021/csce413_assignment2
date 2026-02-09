from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import socket
import time
import ipaddress
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


def recv_banner(sock: socket.socket, max_bytes: int = 4096) -> bytes:
    data = bytearray()
    while len(data) < max_bytes:
        try:
            chunk = sock.recv(min(1024, max_bytes - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if b"\n" in chunk and len(data) >= 64:
                break
        except Exception as e:
            break

    return bytes(data)


def grab_banner(target, port, timeout):
    probes = [
        f"GET / HTTP/1.1\r\nHost: {target}\r\nConnection: close\r\n\r\n".encode("ascii", "ignore"),
        b"\r\n",
        b"HEAD / HTTP/1.0\r\n\r\n",
    ]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((target, port))

            data = recv_banner(s)
            if not data:
                for probe in probes:
                    try:
                        s.sendall(probe)
                        data = recv_banner(s)
                        if data:
                            break
                    except Exception as e:
                        continue

            if not data:
                return "no banner"

            return data.decode("utf-8", errors="replace").strip()

    except Exception as e:
        return "no banner"


def grab_banners(target, ports, timeout, threads):
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
                continue

    return banners


def guess_service(banner):
    if not banner:
        return "unknown"

    if "http" in banner.lower():
        return "http"
    elif "ssh" in banner.lower():
        return "ssh"
    elif "ftp" in banner.lower():
        return "ftp"
    elif "smtp" in banner.lower():
        return "smtp"
    elif "mysql" in banner.lower():
        return "mysql"
    elif "redis" in banner.lower():
        return "redis"
    else:
        return "unknown"


def expand_addresses(addresses):
    expanded = []

    for entry in addresses:
        entry = entry.strip()

        if "/" in entry:
            network = ipaddress.IPv4Network(entry, strict=False)
            for ip in network:
                expanded.append(str(ip))
        else:
            ip = ipaddress.IPv4Address(entry)
            expanded.append(str(ip))

    return expanded


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

    targets = expand_addresses(args.targets)

    open_ports = {}
    scan_times = {}
    banners = {}

    print("Number of targets:", len(targets))
    print("Port range:", args.sp, "-", args.ep)
    print("Timeout:", args.t)
    print("Banner grabbing:", "disabled" if args.nb else "enabled")
    print("Threads:", args.threads)
    print("-----------------------------")

    for target in targets:
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
            banners.update(grab_banners(target, ports, args.t, args.threads))

    print(f"\n[*] Scan complete! ({sum(scan_times.values()):.2f} seconds)")

    for target in open_ports:
        if not open_ports[target]:
            continue

        print(f"[{target}]")
        print(f"    {'PORT':<8}{'STATE':<8}{'SERVICE':<8}")

        for port in open_ports[target]:
            service = guess_service(banners.get((target, port)))
            print(f"    {port:<8}{'open':<8}{service}")

if __name__ == "__main__":
    main()
