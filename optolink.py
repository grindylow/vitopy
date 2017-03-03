#!/usr/bin/env python3

# optolink.py
#
# Module for connecting to a Viessmann central heating system

from serial import *
import optomessage

class OptoLink:

    def __init__(self):
        self.port_name = None
        self.ser = None
    
    def open_port(self, port):
        """
        Open serial port that connects to the OptoLink adaptor.
        """
        self.port_name = port
        self.ser = Serial(port=self.port_name, baudrate=4800,
                          parity=PARITY_EVEN,
                          stopbits=STOPBITS_TWO,
                          timeout=2 )
        
    def close_port(self):
        self.ser.close()

    def init(self):
        """
        Tell the heating that we are about to perform some communications.
        """
        self.deinit()  # just in case the heating was left "open" from a previous comms attempt
        retrycounter = 1
        while True:
            print('tx init - attempt %s' % retrycounter)
            self.ser.write(b'\x16\x00\x00')
            s = self.ser.read()
            if len(s)==1:
                if s==b'\x06':
                    print('success')
                    break
                else:
                    print('received: %s' % hex(s[0]))
            retrycounter = retrycounter+1

    def deinit(self):
        """
        Tell the heating that we are done talking to it.
        """
        print("deinitialising")
        self.ser.write(b'\x04')
        # note: heating should start transmitting periodic 0x05-bytes.

    def query(self, cmd):
        """
        Low-level query function: 
         - send the given request to the heating system, then
         - wait for a reply and return this reply to caller
        This function is/will be used by higher-level "read register" functions.
        You may call it directly if you wish to do so.
        """
        self.ser.write(cmd)
        return optomessage.read_msg(self.ser)

if __name__ == "__main__":
    print("Not meant to be executed. May implement demo features here in the future.")
    
