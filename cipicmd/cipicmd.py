#!/usr/bin/env python
# License:
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Jochen Bartl <jochenbartl@mailbox.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Tested with Prime 2.2

import sys
import json
import base64
import urllib
import httplib
import os.path
from pprint import pprint
import socket
from argparse import ArgumentParser, ArgumentTypeError


__VERSION__ = "0.1.1"

# TODO Replace custom error messages with logging module
class CiPiConnection(object):
    def __init__(self, host, username, password, port=443, timeout=5):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout

    def _httpconn_get_request(self, url, parameters, fmt='json'):
        auth = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')
        headers = {'Authorization': "Basic %s" % auth, 'Accept': 'application/json'}
        parametersencoded = urllib.urlencode(parameters)

        self._httpconn = httplib.HTTPSConnection(self.host, self.port, timeout=self.timeout)
        uri = "{}.{}?{}".format(url, fmt, parametersencoded)

        try:
            self._httpconn.request('GET', uri, headers=headers)
        except socket.error as e:
            print("[ERROR] Unable to conntect to remote host. errmsg: {}".format(e))
            sys.exit(1)

        response = self._httpconn.getresponse()

        # Authentication failed
        if response.status == 401:
            print("[ERROR] HTTP authentication failed: wrong username or password")
            sys.exit(1)

        data = response.read()

        try:
            jsondata = json.loads(data)
        except ValueError as e:
            print("[ERROR] We dind't get any JSON data back from the web server. errmsg: {}".format(e))
            sys.exit(1)
        finally:
            self._httpconn.close()

        return jsondata

    def get_devices(self, fulldetails=True, maxresults=1000):
        """
        fulldetails - Retrieve detailed device information

        TODO There will be a possibility to add filters to the Prime http requiest in the future.
             For now it will request the full device table all the time!!!

        Returns JSON data received from Prime
        """

        parameters = {}

        if fulldetails:
            parameters['.full'] = 'true'

        parameters['.maxResults'] = str(maxresults)

        jsondata = self._httpconn_get_request('/webacs/api/v1/data/Devices', parameters)

        return jsondata


_DEFAULT_DEVICE_ATTRIBUTES = ["clearedAlarms",
                                "collectionDetail",
                                "collectionTime",
                                "creationTime",
                                "criticalAlarms",
                                "deviceId",
                                "deviceName",
                                "deviceType",
                                "informationAlarms",
                                "ipAddress",
                                "location",
                                "majorAlarms",
                                "managementStatus",
                                "manufacturerPartNrs", # Documentation said it is manufacturerPartNr
                                "minorAlarms",
                                "productFamily",
                                "reachability",
                                "softwareType",
                                "softwareVersion",
                                "warningAlarms"]


class CiPiDevices(object):
    def __init__(self, jsondata):
        self.jsondata = jsondata

    def filter_by_attributes(self, attributes):
        """
        Filters JSON data from Prime and returns a list of dictionaries.

        Example: [{'deviceName': 'rtr1.example.com', 'ipAddress': '192.0.2.1'}]

        attributes -- List of attribute values to return

        TODO Just return everything unfiltered if attributes is empty?

        """
        # jsondata['queryResponse']['entity'][PYTHONLIST['devicesDTO']['ipAddress']

        # TODO How should we handle list values? Example: manufacturerPartNrs

        devicesdata = []

        for e in self.jsondata['queryResponse']['entity']:
            devicedata = {}

            for attribute in attributes:
                try:
                    devicedata[attribute] = e['devicesDTO'][attribute]
                except KeyError:
                    # productFamily: Third Party Device, doesn't have all fields!!
                    # Check keys in json data first
                    # FIXME Inserting an empty field for now
                    devicedata[attribute] = ''

            devicesdata.append(devicedata)

        return devicesdata

    def output_csv(self, data, fields, header=True):
        """
        data - Dictonary generated by one of the parse_ functions
        fields - List of columns/attributes to print
        header - Print a header which contains the field names

        TODO Build fields automatically if None

        """

        headerstr = ""
        strformat = ""

        for field in fields:
            strformat += "{" + field + "},"
            headerstr += field + ","

        strformat = strformat[0:-1]
        headerstr = headerstr[0:-1]

        if header:
            print(headerstr)

        for e in data:
            print(strformat.format(**e))


def csv_output(jsondata, attributes, nocsvheader):
    devices = CiPiDevices(jsondata)

    if len(attributes) == 0:
        attributes = _DEFAULT_DEVICE_ATTRIBUTES

    data = devices.filter_by_attributes(attributes)

    if nocsvheader:
        devices.output_csv(data, attributes, header=False)
    else:
        devices.output_csv(data, attributes)


def arg_check_port(port):
    try:
        port = int(port)
    except ValueError:
        raise ArgumentTypeError("{} is not a number".format(port))

    if not port in range(1, 65535):
        raise ArgumentTypeError("Port number {} is invalid. Valid numbers are 1 - 65535".format(port))
    else:
        return port

def arg_check_deviceattrs(attributes):
    """Checks Device attributes and returns them as list

    Arguments:

    attributes - String - Device attributes separated by ,

    """

    if len(attributes) == 0:
        return _DEFAULT_DEVICE_ATTRIBUTES

    attributes = attributes.split(",")

    result = filter(lambda x: x not in _DEFAULT_DEVICE_ATTRIBUTES, attributes)

    # FIXME Simpler/Nicer error message
    if len(result) > 0:
        errmsg = "\n\nInvalid Device attribute(s)\n\n"
        for e in result:
            errmsg += "{}\n".format(e)

        errmsg += "\n\nValid attributes are:\n\n"
        for e in _DEFAULT_DEVICE_ATTRIBUTES:
            errmsg += "{}\n".format(e)

        raise ArgumentTypeError(errmsg)
    else:
        return attributes


def main():
    argparser = ArgumentParser(description='Cisco Prime Infrastructure cli tool')
    # TODO epilog="Usage examples" ??
    argparser.add_argument('-V', '--version', action='version', version="%(prog)s " + __VERSION__)
    argparser.add_argument('-H', '--host', dest='host', help='Prime host')
    argparser.add_argument('-P', '--port', dest='port', default=443, type=arg_check_port, help='Prime API port')
    argparser.add_argument('-t', '--timeout', dest='timeout', default=5, type=int, help='HTTPS connection timeout in seconds')
    argparser.add_argument('-u', '--username', dest='username')
    argparser.add_argument('-p', '--password', dest='password')
    argparser.add_argument('--dump', dest='dumpjson', action='store_true', default=False, help='Return data as JSON dump')
    argparser.add_argument('--dump-dict', dest='dumpdict', action='store_true', default=False, help='Return data as Python dictionary')
    argparser.add_argument('--dump-dict-pretty', dest='dumpdictpretty', action='store_true', default=False, help='Return data as pretty printed Python dictionary')
    # TODO Use builtin type=File... magic 
    argparser.add_argument('-i', '--input', dest='inputjson', help='Read JSON data from a file instead of connection to a Prime server')
    argparser.add_argument('-a', '--device-attributes', dest='attributes', default="", type=arg_check_deviceattrs,
                           help='Specify which Device attributes to display. Separated by comma. Defaults to all')
    argparser.add_argument('--no-csv-header', dest='nocsvheader', action='store_true', help='Suppress CSV header ')
    args = argparser.parse_args()

    # Input JSON
    if args.inputjson:
        inputfile = args.inputjson

        if not os.path.exists(inputfile):
            print("Cannot open JSON input file. File \"{}\" does not exist".format(inputfile))
            sys.exit(1)

        try:
            with open(inputfile, 'r') as f:
                jsondata = json.load(f)
        # Catch file permission issues
        except IOError as e:
            print("Cannot open JSON input file \"{}\". I/O error({}): {}".format(inputfile, e.errno, e.strerror))
            sys.exit(1)
    # Input via REST API
    else:
        # FIXME Implment arg error handling with argparser
        if not args.host:
            print("No --host specified")
            sys.exit(1)
        elif not args.username:
            print("No --username specified")
            sys.exit(1)
        elif not args.password:
            print("No --password specified")
            sys.exit(1)

        # No input file specified. Let's connect to Prime
        conn = CiPiConnection(args.host, args.username, args.password, port=args.port, timeout=args.timeout)
        jsondata = conn.get_devices()

    if args.dumpjson:
        print(json.dumps(jsondata))
        sys.exit(0)
    # TODO JSON pretty print
    # elif args.dumpjsonpretty:
    #     print(json.dumps(jsondata))
    #     sys.exit(0)
    elif args.dumpdict:
        print(jsondata)
        sys.exit(0)
    elif args.dumpdictpretty:
        pprint(jsondata)
        sys.exit(0)

    if args.attributes:
        csv_output(jsondata, args.attributes, args.nocsvheader)
    else:
        csv_output(jsondata, "", args.nocsvheader)

    # TODO Return helath status by default if no parameters except host, user, pass are specified

    sys.exit(0)

if __name__ == '__main__':
    main()
