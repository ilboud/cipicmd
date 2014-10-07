I've just created this file to collect some ideas and todo items

# Input
* Prime API
* Json dump from file
* Json dump from Stdin?

# Output formats
* csv
* json


# Password

-u myusername -p

Empty password will ask for it interactively

* Read credentials from config


# HTTPS
* Cert check by default
* Ask on first connection if cert should be trusted. Save answer and don't bother user again
  - Only complain if cert changes

# Command examples

cmd.py --resource devices --format=json --display-filter=ipAddress 192.168.0.1 deviceType contains "Catalyst"

'devices' should be the default resource. --format=json, default. Filter params like Tshark -> -f capture -F display filter??

cmd.py -F ipAddress 192.168.0.1 deviceType contains "Catalyst"

# Display filter fields as header, like CSV for example
cmd.py --display-filter-header -F ipAddress 192.168.0.1 deviceType contains "Catalyst"

# UnitTests!!!
