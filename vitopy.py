#!/usr/bin/env python3

# Retrieve register values from a Viessmann central heating system.
# With thanks to https://openv.wikispaces.com/

import argparse
import json
import datetime
from vitolib import optolink
from vitolib.optomessage import *
import logging

PROG='vitopy'
VERSION='0.82'

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

def setup_logging():
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
    
if __name__ == "__main__":
    setup_logging()
    logging.info("%s %s starting up at %s." % (
        PROG,
        VERSION,
        datetime.datetime.now(datetime.timezone.utc).isoformat()))

    args = parse_args()
    config = parse_config_file(args.conf)

    o = optolink.OptoLink()
    o.open_port(args.port)
    o.init()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    allreadings = retrieve_all_readings_as_per_configuration(o,config)
    o.deinit()
    o.close_port()
    
    ts = now_utc.timestamp()
    ts_iso8601 = now_utc.isoformat()
    data = dict(comment="https://github.com/grindylow/vitopy",
                 generator="%s %s"%(PROG,VERSION),
                 ts=ts, ts_iso8601=ts_iso8601, vals=allreadings)
    
    f = open(args.outfile, 'a')
    f.write(json.dumps(data, sort_keys=True, indent=2)+'\n')
    f.close()
