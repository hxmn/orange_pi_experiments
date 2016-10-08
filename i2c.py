#!/usr/bin/env python
# coding=utf-8
import locale
from math import sqrt

import smbus
import time
import curses

import sys

locale.setlocale(locale.LC_ALL, '')


# 2014-08-26 PCF8591-x.py
# Connect Pi 3V3 - VCC, Ground - Ground, SDA - SDA, SCL - SCL.
# ./PCF8591-x.py

def length(a):
    return sum([x > 0 for x in a])


def mean(a):
    return sum(a) / length(a)


def std(a):
    m = mean(a)
    return sqrt(sum([(x - m) * (x - m) for x in a])) / length(a)


bus = smbus.SMBus(1)
fs = 25
measure_time = 1000  # milliseconds
calibration = False

scr = curses.initscr()
curses.noecho()
curses.cbreak()

aout = 0

scr.addstr(6, 0, "Measure Time: ")
scr.addstr(8, 0, "Calibration: ")
scr.addstr(10, 0, "Brightness")
# scr.addstr(12, 0, "Temperature")
# scr.addstr(14, 0, "AOUT->AIN2")
# scr.addstr(16, 0, "Resistor")
scr.addstr(18, 0, "Output")

scr.nodelay(1)

brightness = [0] * (measure_time / fs)
pointer = 0

total_count = 0
low_brightness = 0
high_brightness = 0

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

        if calibration:
            if low_brightness == 0 and total_count > 2 * (measure_time / fs):
                low_brightness = mean(brightness)
                aout = 60

            if high_brightness == 0 and total_count > 4 * (measure_time / fs):
                high_brightness = mean(brightness)
                aout = 0

        scr.addstr(10, 12, '%d ± %.2f' % (mean(brightness), std(brightness)))
        scr.addstr(18, 12, str(aout) + ' ')

        scr.addstr(6, 15, '%.2f s.' % (float(measure_time) / 1000))
        scr.addstr(8, 15, '%d - %d' % (low_brightness, high_brightness))
        scr.refresh()

        time.sleep(1 / float(fs))

        c = scr.getch()
        if c == ord('+'):
            aout += 1
            if aout > 255:
                aout = 255
        elif c == ord('-'):
            aout -= 1
            if (aout < 0):
                aout = 0
        elif c != curses.ERR:
            break
except:
    print "Unexpected error:", sys.exc_info()[0]
    raise
curses.nocbreak()
curses.echo()
curses.endwin()
