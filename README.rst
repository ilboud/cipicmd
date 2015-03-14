CiPiCmd - Cisco Prime Infrastructure Command Line script
========================================================

Script for extracting data from Cisco Prime Infrastructure via its HTTP REST API

* Please have a look at the usage examples until I've implemented better error messagages in code ;-)
* SECURITY Please clear your shell history after using this tool, because you'll have to specifiy the password as parameter atm
* SECURITY Python doesn't verify certificates on HTTPS connections by default! TODO
* You could also just use reports in Prime instead of this script, if you just want to have the inventory as CSV
* Tested with Python 2.7, but should work with 3.4 as well
* Tested with Prime Infrastructure 2.1 and 2.2

Usage Examplse
--------------

Get the inventory from Prime and return it on the command line as JSON output

::

        ./cipicmd.py --host 192.0.2.100 --username monitoring --password SuperSecret123 --dump
	

Read the Prime JSON data from a file and display it as CSV. --device-attributes is mandatory at the moment and specifies which attributes are shown in the output.

::

	foo@bar:~/cipicmd$ ./cipicmd.py --input inventory.json --device-attributes deviceType,managementStatus
	deviceType,managementStatus
	Cisco 3750 Stackable Switches,MANAGED_AND_SYNCHRONIZED
	Cisco Catalyst 2960S,MANAGED_AND_SYNCHRONIZED
	Cisco Catalyst 3560CG-8PC-S Compact Switch,MANAGED_AND_SYNCHRONIZED
	Cisco Catalyst 2960S,MANAGED_AND_SYNCHRONIZED
	Cisco Catalyst 2960S,MANAGED_AND_SYNCHRONIZED


Create a RANCID router.db file from the Prime inventory

::

	foo@bar:~/cipicmd$ ./cipicmd.py --input inventory.json --device-attributes deviceType,ipAddress --no-csv-header | grep Catalyst | awk -F ',' '{print $2":cisco:up"}'
	192.0.2.50:cisco:up
	192.0.2.51:cisco:up
	192.0.2.52:cisco:up
	192.0.2.53:cisco:up

License
-------

GPLv3

Feedback
--------

Bug reports, patches and ideas are welcome.

Please also let me know if I need to add any Trademark, Copyright foo before suing me. That would be nice :D

Just send me an e-mail (jochenbartl@mailbox.org) or open an issue on GitHub
