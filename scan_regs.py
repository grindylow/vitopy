#!/usr/bin/env python3

# nmap for Vito

import argparse
import json
import datetime
from vitolib import optolink
from vitolib.optomessage import *
import logging
import signal
from vcd import VCDWriter

PROG = 'scanregs'
VERSION = '0.01'

def parse_args():
    parser = argparse.ArgumentParser(description='Query Viessmann central heating systems.')
    parser.add_argument('--port', '-p', type=str,
                        help='serial port that the OptoLink interface is connected to',
                        default='/dev/ttyAMA0')
    parser.add_argument('--outfile', '-o', type=str,
                        help='name of output file that data will be appended to',
                        default='out/vitoout.json')
    parser.add_argument('--conf', '-c', type=str,
                        help='name of configuration file (in JSON format)',
                        default='vitopy.cfg.json')
    parser.add_argument('--vcd', action='store_true',
                        help='cyclically output all variables to VCD file',
                        default=False)
    parser.add_argument('--version', '-v', action='version', version='%s %s'%(PROG, VERSION))
    return parser.parse_args()

def retrieve_all_readings_as_per_configuration(o,cfg):
    readings = {}
    if 'datapoints' in cfg.keys():
        for line in cfg["datapoints"]:
            logging.debug(line)
            if type(line['addr']) is str:
                line['addr'] = int(line['addr'],0)  # parse non-decimal numbers
            m = ReadRequest(line['addr'], line['bytes'])

            reply = o.query(m.assemble())
                
            r = {}
            if 'uint8'==line['type']:
                r = reply.get_readings_as_uint8()
            elif 'uint16'==line['type']:
                r = reply.get_readings_as_uint16()
            elif 'int16'==line['type']:
                r = reply.get_readings_as_int16()
            elif 'uint32'==line['type']:
                r = reply.get_readings_as_uint32()
            readings.update(dict(r))
    return readings

def create_default_configuration():
    return {"datapoints":[]}

def parse_config_file(filename):
    cfg = create_default_configuration()
    if not os.path.isfile(filename):
        logging.error("Could not find %s."%filename)
    else:
        cfg = json.load(open(filename,'r',encoding='cp437'))
    logging.info(cfg)
    return cfg

    
if __name__ == "__main__":

    args = parse_args()

    o = optolink.OptoLink()
    o.open_port(args.port)
    o.init()

    addr = 0
    nrofbytes = 2
    while addr < 65535:
        print("Scanning addr=%s " % addr, end='')
        m = ReadRequest(addr, nrofbytes)
        reply = o.query(m.assemble())
        if isinstance(reply,ErrorReply):
            print("nix ", end='')
        else:
            vals = reply.get_readings_as_uint8()[0]
            sys.stderr.write('%s,%s\n'%vals)
        addr = addr+1
        sys.stdout.flush()
    
    o.deinit()
    o.close_port()
