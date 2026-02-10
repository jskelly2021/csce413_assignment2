## MITM
### Approach
* I used tcpdump to capture the traffic as I accessed different pages of the web app.

### Findings
* All captures were stored in mitm/
* I identified plain text SQL in all transmissions.
* The flag was found in /api/secrets
