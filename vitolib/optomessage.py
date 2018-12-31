#!/usr/bin/env python3

# optomessage.py
#
# Module encapsulating knowledge of the Viessmann OptoLink message format.

from serial import *
from .optoexceptions import *
import logging
import struct

class OptoMessage:
    def __init__(self, payload=b''):
        self.my_payload = payload

    def assemble(self):
        r = b'\x41' # telegram start
        r += struct.pack('B', len(self.my_payload))
        r += self.my_payload
        r += struct.pack('B', (len(self.my_payload) + sum(self.my_payload))&0xff)
        return r

    def create_from_payload(p):
        """
        Create a message of the type that is described by the payload.
        Returns None if message cannot be interpreted.
        """
        functions_to_try = [ ReadReply.create_from_payload,
                             ErrorReply.create_from_payload
        ]
        r = None
        for creator in functions_to_try:
            r = creator(p)
            if r is not None:
                break
        return r

class ReadRequest(OptoMessage):
    def __init__(self, addr=0x00f8, nrofbytes=2):
        payload = bytes([0x00, 0x01]) # request, read_data
        payload += struct.pack('>H', addr)
        payload += struct.pack('B', nrofbytes)
        super().__init__(payload)

class ReadReply(OptoMessage):
    def get_readings_as_uint16(self):
        """
        Return an array of (addr,reading) tuples containing all
        data in our payload, interpreted as unsigned 16-bit integers.
        """
        addr = struct.unpack('>H', self.my_payload[2:4])[0]
        nrofbytes = self.my_payload[4]
        if nrofbytes % 2 != 0:
            raise CannotInterpretOddNumberOfBytesAsArrayOfIntegersException
        r = []
        for i in range(0,nrofbytes,2):
            val = struct.unpack('<H', self.my_payload[5+i:5+i+2])[0]
            # values are apparently stored as little-endian
            r.append((addr, val))
            addr += 2
        return r
        
    def get_readings_as_int16(self):
        """
        Return an array of (addr,reading) tuples containing all
        data in our payload, interpreted as signed 16-bit integers.
        """
        addr = struct.unpack('>H', self.my_payload[2:4])[0]
        nrofbytes = self.my_payload[4]
        if nrofbytes % 2 != 0:
            raise CannotInterpretOddNumberOfBytesAsArrayOfIntegersException
        r = []
        for i in range(0,nrofbytes,2):
            val = struct.unpack('<h', self.my_payload[5+i:5+i+2])[0]
            # values are apparently stored as little-endian
            r.append((addr, val))
            addr += 2
        return r
        
    def get_readings_as_uint32(self):
        """
        Return an array of (addr,reading) tuples containing all
        data in our payload, interpreted as unsigned 32-bit integers.
        """
        addr = struct.unpack('>H', self.my_payload[2:4])[0]
        nrofbytes = self.my_payload[4]
        if nrofbytes % 4 != 0:
            raise CannotInterpretNonDivisibleByFourNumberOfBytesAsArrayOf32BitIntegersException
        r = []
        for i in range(0,nrofbytes,4):
            val = struct.unpack('<I', self.my_payload[5+i:5+i+4])[0]
            r.append((addr, val))
            addr += 4
        return r
        
    def get_readings_as_uint8(self):
        """
        Return an array of (addr,reading) tuples containing all
        data in our payload, interpreted as unsigned 8-bit integers.
        """
        addr = struct.unpack('>H', self.my_payload[2:4])[0]
        nrofbytes = self.my_payload[4]
        r = []
        for i in range(0,nrofbytes):
            val = struct.unpack('B', self.my_payload[5+i:5+i+1])[0]
            r.append((addr, val))
            addr += 1
        return r
        
    def create_from_payload(p):
        if p[0] != 0x01:
            return None
        if p[1] != 0x01:
            return None
        return ReadReply(p)

class ErrorReply(OptoMessage):
    def create_from_payload(p):
        if p[0] != 0x03:
            return None
        return ErrorReply(p)
                

#
# module functions
#
def read_msg(port):
    """
    Read a sequence of bytes from the central heating system, interpreting it as an
    OptoLink message.
    """
    try:
        expect(port, 0x06)
    except ReceivedUnexpectedByteValueException:
        expect(port, 0x06)  # try once more before failing
    expect(port, 0x41)
    l = port.read()[0]   # Länge der Nutzdaten
    logging.info('reply length is %s' % l)
    payload = port.read(l)
    if len(payload) != l:
        logging.warning('timeout while reading payload')
        raise(TimeoutWhileReadingPayloadException())
    logging.info('reply payload is %s' % [hex(b) for b in payload])
    
    calculated_chksum = (l+sum(payload)) & 0xff
    chksum_in_msg = port.read()[0]
    if calculated_chksum != chksum_in_msg:
        logging.warning('checksum mismatch: calculated: %s, is: %s' % (calculated_chksum, chksum_in_msg))
        raise(ChecksumMismatchException())
    logging.debug('checksums match')
    return OptoMessage.create_from_payload(payload)


#
# helper functions
#
def expect(port, b):
    """
    Receive a single byte, expect it to be b. Raise an exception if not received.
    """
    s = port.read()
    if s==bytes([b]):
        logging.info('success: received %s' % hex(s[0]))
    else:
        logging.warning('expect failed: received %s' % hex(s[0]))
        raise(ReceivedUnexpectedByteValueException())


if __name__ == "__main__":
    print("Not meant to be executed. May implement demo features here in the future.")
    
