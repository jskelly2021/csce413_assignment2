## Port Knocking Starter Template
### Design
* Each port in the sequence has a thread dedicated to listening for knocks.
* When it gets a knock, it updates a registry of IP addresses and previous knocks and
their times.
* It then checks:
    * Have there been the correct # of knocks for the sequence. If yes checks:
        * If not, continue listening.
    * Is the sequence completed in correct amount of time
        * Clears knock registry for IP if no.
    * Is the sequence violated
        * Clears knock registry for the IP if violated
        * Open protected port if good.
* Implemented with TCP connections
* Uses iptables to handle networking rules

Starting the server:
* flushes the rules with iptables -F
* Disallows Inbound traffic on the protected port
* Allows traffic on all the sequenced ports

### Example Usage
* WARNING: Only run in a container. Flushes all entries of the iptable when server starts.

```bash
python3 knock_client.py --target 172.20.0.40 --sequence 1234,5678,9012
```
