#!/usr/bin/env python3

# Retrieve register values from a Viessmann central heating system.
# With thanks to https://openv.wikispaces.com/

import argparse
import json
import datetime
from vitolib import optolink
from vitolib.optomessage import *
import logging
import signal
#from vcd import VCDWriter
import paho.mqtt.client as mqtt   # pip3 install paho-mqtt

PROG = 'vitopy'
VERSION = '0.82'
SIGINT = False

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
    parser.add_argument('--publishmqtt', action='store_true',
                        help='(try to) publish all polled vcd variables to local MQTT broker',
                        default=False)
    parser.add_argument('--version', '-v', action='version', version='%s %s'%(PROG, VERSION))
    return parser.parse_args()

def my_sigint_handler(signal, frame):
    """
    Called when program is interrupted with CTRL+C
    """
    global SIGINT
    logging.info("SIGINT detected")
    SIGINT = True
    return

def retrieve_all_readings_as_per_configuration(o,cfg):
    readings = {}
    if 'datapoints' in cfg.keys():
        for line in cfg["datapoints"]:
            logging.debug(line)
            if not 'addr' in line:
                continue
            if type(line['addr']) is str:
                line['addr'] = int(line['addr'],0)  # parse non-decimal numbers
            m = ReadRequest(line['addr'], line['bytes'])

            reply = o.query(m.assemble())
            if isinstance(reply, ErrorReply):
                logging.warning('request for addr %s resulted in ErrorReply.'%hex(line['addr']))
                continue
                
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

    # some post-processing so we can use our configuration
    # data more easily

    # - add unique id to each actual data point
    # - convert all addresses to integer

    uid = 1
    for v in cfg["datapoints"]:
        logging.debug(v)
        if not 'addr' in v:
            continue
        v['uid'] = uid
        uid = uid+1
        if type(v['addr']) is str:
            v['addr'] = int(v['addr'],0)  # parse non-decimal numbers
        if not 'id' in v:
            v['id'] = 'NOID(%s)'%v['addr']
        if not 'TTL' in v:
            v['TTL'] = 900
    
    return cfg

def setup_logging():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')


def log_to_vcd(cfg):
    """
    Cyclically poll heating and log results to VCD file.
    """
    global SIGINT

    # set up VCD logging
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    vcdwriter = VCDWriter(open('vitopy1.vcd','w'),
                          timescale='1s',
                          init_timestamp=now_utc.timestamp())
    vcdvars = {}
    for v in config['datapoints']:
        if not 'addr' in v:
            continue
        name = '%s_%s'%(v['id'],v['addr'])
        if 'uint8'==v['type']:
            logging.info('Adding variable %s' % v['addr'])
            vcdvars.update( { v['addr']: vcdwriter.register_var('vitopy',name,'integer',size=8) } )
        if 'int8'==v['type']:
            logging.info('Adding variable %s' % v['addr'])
            vcdvars.update( { v['addr']: vcdwriter.register_var('vitopy',name,'integer',size=8) } )
        if 'uint16'==v['type']:
            logging.info('Adding variable %s' % v['addr'])
            vcdvars.update( { v['addr']: vcdwriter.register_var('vitopy',name,'integer',size=16) } )
        if 'int16'==v['type']:
            logging.info('Adding variable %s' % v['addr'])
            vcdvars.update( { v['addr']: vcdwriter.register_var('vitopy',name,'integer',size=16) } )
        if 'uint32'==v['type']:
            logging.info('Adding variable %s' % v['addr'])
            vcdvars.update( { v['addr']: vcdwriter.register_var('vitopy',name,'integer',size=32) } )
    
    # poll heating
    o = optolink.OptoLink()
    o.open_port(args.port)
    o.init()
    while True:
        logging.info('-- start of query --')
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        allreadings = retrieve_all_readings_as_per_configuration(o,config)
        print(allreadings)
        
        for k in allreadings.keys():
            r = allreadings[k]
            if k in vcdvars:
                vcdwriter.change(vcdvars[k], now_utc.timestamp(), r)
                # k is the address, look up the ID-string associated with this address
                id = ''
                for point in config['datapoints']:
                    if not 'addr' in point:
                        continue
                    if point['addr'] == k:
                        id = point['id']
                        break
                if args.publishmqtt:
                    mqttc.publish(id, r)
            

        vcdwriter.flush()
        
        for i in range(10):
            time.sleep(1)
            if SIGINT:
                break
        if SIGINT:
            break
        logging.info('-- end of query --')
        
    o.deinit()
    o.close_port()
    vcdwriter.close()
    
    return


def cyclically_poll_heating(cfg):
    """
    Cyclically poll heating. Send any values that have changed to various
    outputs as configured by the command line arguments.
    """
    global SIGINT

    # We read all values for which our configuration has a
    # unique ID.

    # @future: where would be best implement aggregated blocks of readings?

    # We remember the previous reading, so we can react to changes
    prev_vals = {}
    
    # poll heating
    o = optolink.OptoLink()
    o.open_port(args.port)
    o.init()
    
    while not SIGINT:
        logging.info('-- start of query --')
        
        for v in cfg['datapoints']:
            if not 'uid' in v:
                continue
        
            logging.debug(v)
            now = time.time()
            m = ReadRequest(v['addr'], v['bytes'])

            reply = o.query(m.assemble())
            if isinstance(reply, ErrorReply):
                logging.warning('request for addr %s resulted in ErrorReply.'%hex(v['addr']))
                continue
            
            r = {}
            t = v['type']
            if 'uint8'==t:
                r = reply.get_readings_as_uint8()
            elif 'uint16'==t:
                r = reply.get_readings_as_uint16()
            elif 'int16'==t:
                r = reply.get_readings_as_int16()
            elif 'uint32'==t:
                r = reply.get_readings_as_uint32()

            # r is an array of (addr, val) tuples
            # But currently we only ever retrieve one reading
            assert(len(r)==1)
            assert(r[0][0]==v['addr'])
            val = r[0][1]

            # only output if changed or previous value too old
            remain_quiet = True
            if v['uid'] not in prev_vals:
                logging.info('NOT remaining quiet about this value because we don''t have a previous value yet: %s=%s',
                             v['id'], val)
                prev_vals[v['uid']] = {'last_changed':0, 'val':None}
                remain_quiet = False
            elif prev_vals[v['uid']]['last_changed']+v['TTL'] < now:
                logging.info('NOT remaining quiet about this value because time-to-live has expired: %s=%s',
                             v['id'], val)
                remain_quiet = False
            elif prev_vals[v['uid']]['val'] != val:
                logging.info('NOT remaining quiet about this value because value has changed: %s changed from %s to %s',
                             v['id'], prev_vals[v['uid']]['val'], val)
                remain_quiet = False
            # @future: could also implement hysteresis

            if not remain_quiet:
                prev_vals[v['uid']]['last_changed'] = now
                prev_vals[v['uid']]['val'] = val
                if args.publishmqtt:
                    mqttc.publish(v['id'], val)
            else:
                logging.info('remaining quiet about this value: %s', val)

        # sleep, unless rudely interrupted
        for i in range(10):
            time.sleep(1)
            if SIGINT:
                logging.info('-- interrupted by SIGINT --')
                break
        
        logging.info('-- end of query --')
        
    o.deinit()
    o.close_port()
    return
    
if __name__ == "__main__":
    setup_logging()
    logging.info("%s %s starting up at %s." % (
        PROG,
        VERSION,
        datetime.datetime.now(datetime.timezone.utc).isoformat()))

    signal.signal(signal.SIGINT, my_sigint_handler)

    args = parse_args()
    config = parse_config_file(args.conf)

    if args.publishmqtt:
        mqttc = mqtt.Client("vitopy")
        mqttc.enable_logger()
        mqttc.connect("localhost")
        mqttc.loop_start()

    cyclically_poll_heating(config)
        
    if args.publishmqtt:
        mqttc.disconnect()

    sys.exit(0)

    # old stuff
    if args.vcd:
        log_to_vcd(config)
        if args.publishmqtt:
            mqttc.disconnect()
        sys.exit(0)
        
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
