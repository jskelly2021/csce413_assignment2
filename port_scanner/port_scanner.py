import argparse


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


if __name__ == "__main__":
    main()