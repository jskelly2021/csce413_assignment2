#!/usr/bin/env python3

import logging
import os
import time
import threading

LOG_PATH = "/app/logs/honeypot.log"
PORT = "2222"


def handle_connection(conn, addr, connect_time):
    """Handle the connection attempt"""


def setup_logging():
    os.makedirs("/app/logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
    )


def run_honeypot():
    logger = logging.getLogger("Honeypot")
    logger.info("Honeypot starter template running.")
    logger.info("TODO: Implement protocol simulation, logging, and alerting.")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", PORT))
            s.listen()

            logging.info("Listening for connection attempts on port %s...", PORT)

            while True:
                conn, addr = s.accept()
                connect_time = time.time()

                logging.info("Connection attempt from %s at %s", addr[0], time.ctime(connect_time))
                threading.Thread(target=handle_connection, args=(conn, addr[0], connect_time), daemon=True).start()

    except Exception as e:
        logging.error("Error listening on port %s: %s", PORT, e)

    while True:
        time.sleep(60)


if __name__ == "__main__":
    setup_logging()
    run_honeypot()
