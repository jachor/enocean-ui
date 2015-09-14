import logging
import array
from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.internet.protocol import Protocol


def encode_bytes(a):
    return ''.join('{:02x}'.format(x) for x in a)


def decode_bytes(s):
    return [int(s[i:i+2], 16) for i in xrange(0,len(s),2)]


def crc8(data):
    # https://chromium.googlesource.com/chromiumos/platform/vboot_reference/+/master/firmware/lib/crc8.c
    crc = 0
    for b in data:
        crc ^= b << 8
        for i in xrange(8):
            if (crc & 0x8000) != 0:
                crc ^= (0x1070 << 3)
            crc <<= 1
    return crc >> 8


def _repr_hex_array(a):
    return '[' + ', '.join('0x{:02X}'.format(x) for x in a) + ']'

class Packet(object):
    def __init__(self, packet_type, data, optional_data):
        self.packet_type = packet_type
        self.data = data
        self.optional_data = optional_data

    def __str__(self):
        return 'Packet(0x{:02X}, {}, {})'.format(self.packet_type, _repr_hex_array(self.data), _repr_hex_array(self.optional_data))
    
    __repr__ = __str__

    def encode(self):
        data_len = len(self.data)
        header = [data_len >> 8, data_len & 0xff, len(self.optional_data), self.packet_type]
        return ([0x55] + header + [crc8(header)] +
                self.data + self.optional_data +
                [crc8(self.data + self.optional_data)])

    @classmethod
    def read(clazz, data):
        data_len = (data[1]<<8) + data[2]
        opt_data_len = data[3]
        packet_type = data[4]
        data_portion = data[6:-1]
        return clazz(packet_type, data_portion[:data_len], data_portion[data_len:])
    
    @classmethod
    def from_string(clazz, s):
        X = s.split('.')
        if len(X) != 3:
            raise ValueError('Bad format')
        return clazz(decode_bytes(X[0])[0], decode_bytes(X[1]), decode_bytes(X[2]))

    def to_string(self):
        return (encode_bytes([self.packet_type]) + '.' +
                encode_bytes(self.data) + '.' +
                encode_bytes(self.optional_data))


class RadioReceiverProtocol(Protocol):
    def __init__(self, radio):
        self.radio = radio
        self.data = []

    def gotPacket(self, data):
        #print 'got packet: ' + _repr_hex_array(data)
        self.radio.gotPacket(Packet.read(data))

    def dataReceived(self, data):
        self.data += array.array('B', data)
        while True:
            while len(self.data) > 0 and self.data[0] != 0x55:
                print 'additional data: ', self.data[0]
                self.data = self.data[1:]
            if len(self.data) < 7:
                break
            data_len = (self.data[1]<<8) + self.data[2]
            opt_data_len = self.data[3]
            #packet_type = self.data[4]
            header_crc = self.data[5]
            if crc8(self.data[1:5]) != header_crc:
                logging.info("Bad header CRC")
                self.data = self.data[1:]
                continue
            total_len = 6 + data_len + opt_data_len + 1
            if len(self.data) < total_len:
                break
            if crc8(self.data[6:(total_len-1)]) != self.data[total_len-1]:
                logging.info("Bad data CRC")
            else:
                self.gotPacket(self.data[:total_len])
            self.data = self.data[total_len:]
        if len(self.data) > 100:
            self.data = []


class Radio(object):
    def connect(self, port):
        self.serial = SerialPort(RadioReceiverProtocol(self), port, reactor, baudrate=57600)
        self.serial.flushInput()

    def __init__(self):
        self.listeners = []
        self.serial = None

    def send(self, packet):
        data = array.array('B', packet.encode()).tostring()
        print 'tx:', packet
        if self.serial is not None:
            self.serial.write(data)

    def gotPacket(self, packet):
        print 'rx:', packet
        for l in self.listeners:
            l(packet)


RADIO = Radio()


def start_radio(port='/dev/ttyAMA0'):
    logging.info('Starting radio at {}'.format(port))
    RADIO.connect(port)

