#!/usr/bin/env python3

import argparse
import logging
import socket
import time
import threading
import subprocess

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


def open_protected_port(protected_port):
    """Open the protected port using firewall rules."""

    check = subprocess.run([
        "iptables",
        "-C","INPUT",
        "-p","tcp",
        "--dport",str(protected_port),
        "-j","ACCEPT"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    subprocess.run([
        "iptables",
        "-I", "INPUT", "1",
        "-p", "tcp",
        "--dport",
        str(protected_port),
        "-j", "ACCEPT"
    ], check=True)

    logging.info("Protected port %s is now open", protected_port)


def close_protected_port(protected_port):
    """Close the protected port using firewall rules."""

    subprocess.run([
        "iptables",
        "-D", "INPUT",
        "-p", "tcp",
        "--dport",
        str(protected_port),
        "-j", "ACCEPT"
    ], check=True)

    logging.info("Protected port %s is now closed", protected_port)


def setup_iptables(protected_port, sequence=DEFAULT_KNOCK_SEQUENCE):
    """Set up iptables rules to block the protected port by default."""

    subprocess.run([
        "iptables",
        "-F"
    ], check=True)

    for port in sequence:
        subprocess.run([
            "iptables",
            "-A", "INPUT",
            "-p", "tcp",
            "--dport", str(port),
            "-j", "ACCEPT"
        ], check=True)

    subprocess.run([
        "iptables",
        "-A", "INPUT",
        "-p", "tcp",
        "--dport", str(protected_port),
        "-j", "DROP"
    ], check=True)

    logging.info("iptables configured to block protected port %s by default", protected_port)


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


def listen_on_protected_port(protected_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", protected_port))
            s.listen()

            logging.info("Listening on protected port %s...", protected_port)

            while True:
                conn, addr = s.accept()
                logging.info("Connection received on protected port from %s", addr[0])
                conn.close()

    except Exception as e:
        logging.error("Error listening on protected port %s: %s", protected_port, e)


def listen_on_port(port, sequence, window_seconds, protected_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
            s.listen()

            logging.info("Listening for knocks on port %s...", port)

            while True:
                conn, addr = s.accept()
                knock_time = time.time()

                with lock:
                    if addr[0] not in knock_attempts:
                        knock_attempts[addr[0]] = []

                    knock_attempts[addr[0]].append((port, knock_time))

                if check_sequence(addr[0], sequence, window_seconds, protected_port):
                    open_protected_port(protected_port)

                conn.close()

    except Exception as e:
        logging.error("Error listening on port %s: %s", port, e)


def listen_for_knocks(sequence, window_seconds, protected_port):
    """Listen for knock sequence and open the protected port."""
    logger = logging.getLogger("KnockServer")
    logger.info("Listening for knocks: %s", sequence)
    logger.info("Protected port: %s", protected_port)

    for port in sequence:
        threading.Thread(target=listen_on_port, args=(port, sequence, window_seconds, protected_port), daemon=True).start()

    threading.Thread(target=listen_on_protected_port, args=(protected_port,), daemon=True).start()

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

    setup_iptables(args.protected_port, sequence)
    listen_for_knocks(sequence, args.window, args.protected_port)


if __name__ == "__main__":
    main()
