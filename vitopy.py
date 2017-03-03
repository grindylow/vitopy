#!/usr/bin/env python3

# Retrieve register values from a Viessmann central heating system.
# With thanks to https://openv.wikispaces.com/

import argparse
import json
import datetime
from vitolib import optolink
from vitolib.optomessage import *

PROG='vitopy'
VERSION='0.6'

parser = argparse.ArgumentParser(description='Query Viessmann central heating systems.')
parser.add_argument('--port', '-p', type=str,
                    help='serial port that the OptoLink interface is connected to',
                    default='/dev/ttyAMA0')
parser.add_argument('--outfile', '-o', type=str,
                    help='name of output file that data will be appended to',
                    default='out/vitoout.json')
parser.add_argument('--version', '-v', action='version', version='%s %s'%(PROG, VERSION))
args = parser.parse_args()

print(args)

o = optolink.OptoLink()

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

now_utc = datetime.datetime.now(datetime.timezone.utc)
ts = now_utc.timestamp()
ts_iso8601 = now_utc.isoformat()

data = [dict(comment="https://github.com/grindylow/vitopy",
             generator="%s %s"%(PROG,VERSION),
             ts=ts, ts_iso8601=ts_iso8601, vals=allreadings)]

f = open(args.outfile,'a')
f.write(json.dumps(data, sort_keys=True, indent=2)+'\n')
f.close()
