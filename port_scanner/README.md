## Port Scanner
### Design
* CLI argument parsing and validation.
* Supports multiple targets as a list or CIDR notation.
* TCP port scanning
* Socket timeout
* Supports multithreading
* First performs passive banner grabbing by using recv(). This discovered ssh services.
* Next performs active probing which discovers http and mysql services. 

### Usage
* usage: port_scanner.py [-h] [-sp SP] [-ep EP] [-t T] [-nb] [-threads THREADS] targets [targets ...]
* positional arguments:
    * targets           Target hostname(s) or IP address(es)
* options:
    * -h, --help        show this help message and exit
    * -sp SP            Start port (default: 1)
    * -ep EP            End port (default: 65535)
    * -t T              Connection timeout in seconds (default: 1.0)
    * -nb               Disable service discovery (banner grabbing)
    * -threads THREADS  Number of threads to use (default: 10)

#### Example:
```bash
python3 port_scanner.py 172.20.0.10 172.20.0.11 172.20.5.0/16 -ep 34000 -t 1 -threads 50
```
