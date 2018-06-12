#!/usr/bin/env python
# encoding: utf-8

import locale
import os
import sys
import threading
import time
from math import sqrt

import smbus
from tornado import websocket, web, ioloop

locale.setlocale(locale.LC_ALL, '')
cl = []
fs = 25
measure_time = 1000  # milliseconds
calibration = False

brightness = [0] * (measure_time / fs)
pointer = 0

low_brightness = 0
high_brightness = 0
total_count = 0
aout = 0


def length(a):
    return sum([x > 0 for x in a])


def mean(a):
    return sum(a) / length(a)


def std(a):
    m = mean(a)
    return sqrt(sum([(x - m) * (x - m) for x in a])) / length(a)


class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")


class ApiHandler(web.RequestHandler):
    @web.asynchronous
    def get(self, *args):
        self.finish()
        action = self.get_argument("action")
        if action == 'start':
            print 'Start sending info'
            t = threading.Thread(target=start_i2c, args=[])
            t.start()


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in cl:
            cl.append(self)

    def on_close(self):
        if self in cl:
            cl.remove(self)

    def on_message(self, message):
        global aout
        print message
        if message.startswith("dac:"):
            aout = int(message.replace("dac:", ""))
            print 'set new DAC value: ' + str(aout)
            if aout < 0:
                aout = 0
            elif aout > 255:
                aout = 255
        elif message.startswith("steps:"):
            os.system("/root/http/move.sh " + message.replace("steps:", ""))


try:
    bus = smbus.SMBus(1)
except:
    print 'Device is not initialized'


def get_state():
    return '%d|%d|%d' % (aout, mean(brightness), std(brightness))


def start_i2c():
    global total_count, pointer
    try:
        while True:
            total_count += 1
            for a in range(0, 4):
                bus.write_byte_data(0x48, 0x40 | ((a + 1) & 0x03), aout)
                v = bus.read_byte(0x48)
                if a == 0:  # brightness
                    brightness[pointer] = v
                    pointer += 1
                    pointer %= measure_time / fs

            time.sleep(1 / float(fs))
            for c in cl:
                c.write_message(get_state())
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise


app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
])

if __name__ == '__main__':
    app.listen(8888)
    ioloop.IOLoop.instance().start()
