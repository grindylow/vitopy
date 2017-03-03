#!/usr/bin/env python3

# Retrieve register values from a Viessmann central heating system.
# With thanks to https://openv.wikispaces.com/

import argparse
import optolink
import json

parser = argparse.ArgumentParser(description='Query Viessmann central heating systems.')
parser.add_argument('--port', '-p', type=str,
                    help='serial port that the OptoLink interface is connected to',
                    default='/dev/ttyAMA0')
parser.add_argument('--outfile', '-o', type=str,
                    help='name of output file that data will be appended to',
                    default='vitoout.json')
args = parser.parse_args()

print(args)

o = optolink.OptoLink()

from optomessage import *
#m = ReadRequest()
#print([hex(x) for x in m.assemble()])
#exit(1)

o.open_port(args.port)
o.init()
#o.query(bytes([0x41,0x05,0x00,0x01,0x55,0x25,0x02,0x82]))

allreadings = {}

m = ReadRequest()
reply = o.query(m.assemble())  # Gerätekennung
print(reply)
print(reply.get_readings_as_uint16())
allreadings.update(dict(reply.get_readings_as_uint16()))

m = ReadRequest(0x0800,6)
reply = o.query(m.assemble())  # Temperaturen
print(reply)
allreadings.update(dict(reply.get_readings_as_uint8()))

m = ReadRequest(0x2301,8)
reply = o.query(m.assemble())  # Betriebszustände
print(reply)
allreadings.update(dict(reply.get_readings_as_uint8()))

o.deinit()
o.close_port()

data = [dict(comment="Read by vitopy", ts=1234, ts_iso8601="123T45", vals=allreadings)]

f = open(args.outfile,'a')
f.write(json.dumps(data, sort_keys=True, indent=2))
f.close()
