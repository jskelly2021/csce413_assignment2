#!/usr/bin/env python3

import argparse
import logging
import socket
import time
import threading

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_SEQUENCE_WINDOW = 10.0

knock_attempts = {}
lock = threading.Lock()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def check_sequence(ip, sequence, window_seconds, protected_port):
    with lock:
        if not len(knock_attempts[ip]) == len(sequence):
            return False

        if knock_attempts[ip][-1][1] - knock_attempts[ip][0][1] > window_seconds:
            logging.info("Sequence window exceeded for IP %s", ip)
            knock_attempts[ip].clear()
            return False

        for i, (port, _) in enumerate(knock_attempts[ip]):
            if port != sequence[i]:
                logging.info("Incorrect knock sequence from IP %s", ip)
                knock_attempts[ip].clear()
                return False

        knock_attempts[ip].clear()

    logging.info("Correct knock sequence from IP %s. Opening protected port.", ip)

    return True

def listen_on_port(port, sequence, window_seconds, protected_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", port))
        s.listen()

        logging.info("Listening for knocks on port %s...", port)

        while True:
            conn, addr = s.accept()
            knock_time = time.time()

            with lock:
                knock_attempts[addr[0]].append((port, knock_time))

            if check_sequence(addr[0], sequence, window_seconds, protected_port):
                    open_protected_port(protected_port)

            conn.close()


def open_protected_port(protected_port):
    """Open the protected port using firewall rules."""
    # TODO: Use iptables/nftables to allow access to protected_port.
    logging.info("TODO: Open firewall for port %s", protected_port)


def close_protected_port(protected_port):
    """Close the protected port using firewall rules."""
    # TODO: Remove firewall rules for protected_port.
    logging.info("TODO: Close firewall for port %s", protected_port)


def listen_for_knocks(sequence, window_seconds, protected_port):
    """Listen for knock sequence and open the protected port."""
    logger = logging.getLogger("KnockServer")
    logger.info("Listening for knocks: %s", sequence)
    logger.info("Protected port: %s", protected_port)

    # TODO: Create UDP or TCP listeners for each knock port.
    # TODO: Track each source IP and its progress through the sequence.
    # TODO: Enforce timing window per sequence.
    # TODO: On correct sequence, call open_protected_port().
    # TODO: On incorrect sequence, reset progress.

    for port in sequence:
        threading.Thread(target=listen_on_port, args=(port, sequence, window_seconds, protected_port), daemon=True).start()

    while True:
        time.sleep(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Port knocking server starter")
    parser.add_argument(
        "--sequence",
        default=",".join(str(port) for port in DEFAULT_KNOCK_SEQUENCE),
        help="Comma-separated knock ports",
    )
    parser.add_argument(
        "--protected-port",
        type=int,
        default=DEFAULT_PROTECTED_PORT,
        help="Protected service port",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=DEFAULT_SEQUENCE_WINDOW,
        help="Seconds allowed to complete the sequence",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging()

    try:
        sequence = [int(port) for port in args.sequence.split(",")]
    except ValueError:
        raise SystemExit("Invalid sequence. Use comma-separated integers.")

    listen_for_knocks(sequence, args.window, args.protected_port)


if __name__ == "__main__":
    main()
