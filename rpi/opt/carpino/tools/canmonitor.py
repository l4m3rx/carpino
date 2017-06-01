#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Code from:
#   https://github.com/alexandreblin/python-can-monitor
#

import argparse
import curses
import sys
import threading
import traceback

import serial

should_redraw = threading.Event()
stop_serial = threading.Event()

can_messages = {}
can_messages_lock = threading.Lock()

thread_exception = None


def read_until_newline(serial_device):
    """Read data from `serial_device` until the next newline character."""
    line = serial_device.readline()
    while len(line) == 0 or line[-1] != '\n':
        line = line + serial_device.readline()

    return line.strip()


def serial_run_loop(serial_device):
    """Background thread for serial reading."""
    try:
        while not stop_serial.is_set():
            line = read_until_newline(serial_device)

            # Sample frame from Arduino: FRAME:ID=246:LEN=8:8E:62:1C:F6:1E:63:63:20
            # Split it into an array (e.g. ['FRAME', 'ID=246', 'LEN=8', '8E', '62', '1C', 'F6', '1E', '63', '63', '20'])
            frame = line.split()

            try:
            #if  1==1:
                frame_id = int(frame[1],16)
                frame_length = int(frame[2][1])  # get the length from the 'LEN=8' string

                data = [int(byte, 16) for byte in frame[3:]]  # convert the hex strings array to an integer array
                data = [byte for byte in data if byte >= 0 and byte <= 255]  # sanity check

                if len(data) != frame_length:
                    # Wrong frame length or invalid data
                    continue

                # Add the frame to the can_messages dict and tell the main thread to refresh its content
                with can_messages_lock:
                    can_messages[frame_id] = data
                    should_redraw.set()
            except:
                # Invalid frame
                continue
    except:
        if not stop_serial.is_set():
            # Only log exception if we were not going to stop the thread
            # When quitting, the main thread calls close() on the serial device
            # and read() may throw an exception. We don't want to display it as
            # we're stopping the script anyway
            global thread_exception
            thread_exception = sys.exc_info()


def init_window(stdscr):
    """Init a window filling the entire screen with a border around it."""
    stdscr.clear()
    stdscr.refresh()

    max_y, max_x = stdscr.getmaxyx()
    root_window = stdscr.derwin(max_y, max_x, 0, 0)

    root_window.box()

    return root_window


def main(stdscr, serial_thread):
    """Main function displaying the UI."""
    # Don't print typed character
    curses.noecho()
    curses.cbreak()

    # Set getch() to non-blocking
    stdscr.nodelay(True)

    win = init_window(stdscr)

    while True:
        # should_redraw is set by the serial thread when new data is available
        if should_redraw.is_set():
            max_y, max_x = win.getmaxyx()

            column_width = 50
            id_column_start = 2
            bytes_column_start = 13
            text_column_start = 38

            # Compute row/column counts according to the window size and borders
            row_start = 3
            lines_per_column = max_y - (1 + row_start)
            num_columns = (max_x - 2) / column_width

            # Setting up column headers
            for i in range(0, num_columns):
                win.addstr(1, id_column_start + i * column_width, 'ID')
                win.addstr(1, bytes_column_start + i * column_width, 'Bytes')
                win.addstr(1, text_column_start + i * column_width, 'Text')

            win.addstr(3, id_column_start, "Press 'q' to quit")

            row = row_start + 2  # The first column starts a bit lower to make space for the 'press q to quit message'
            current_column = 0

            # Make sure we don't read the can_messages dict while it's being written to in the serial thread
            with can_messages_lock:
                for frame_id in sorted(can_messages.keys()):
                    msg = can_messages[frame_id]

                    # convert the bytes array to an hex string (separated by spaces)
                    msg_bytes = ' '.join('%02X' % byte for byte in msg)

                    # try to make an ASCII representation of the bytes
                    # nonprintable characters are replaced by '?'
                    # and spaces are replaced by '.'
                    msg_str = ''
                    for byte in msg:
                        char = unichr(byte)
                        if char == '\0':
                            msg_str = msg_str + '.'
                        elif ord(char) < 32 or ord(char) > 126:
                            msg_str = msg_str + '?'
                        else:
                            msg_str = msg_str + char

                    # print frame ID in decimal and hex
                    win.addstr(row, id_column_start + current_column * column_width, '%s' % str(frame_id).ljust(5))
                    win.addstr(row, id_column_start + 5 + current_column * column_width, '%X'.ljust(5) % frame_id)

                    # print frame bytes
                    win.addstr(row, bytes_column_start + current_column * column_width, msg_bytes.ljust(23))

                    # print frame text
                    win.addstr(row, text_column_start + current_column * column_width, msg_str.ljust(8))

                    row = row + 1

                    if row >= lines_per_column + row_start:
                        # column full, switch to the next one
                        row = row_start
                        current_column = current_column + 1

                        if current_column >= num_columns:
                            break

            win.refresh()

            should_redraw.clear()

        c = stdscr.getch()
        if c == ord('q') or not serial_thread.is_alive():
            break
        elif c == curses.KEY_RESIZE:
            win = init_window(stdscr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CAN data from a serial device.')
    parser.add_argument('serial_device', type=str)
    parser.add_argument('baud_rate', type=int, default=115200,
                        help='Serial baud rate in bps (default: 115200)')

    args = parser.parse_args()

    serial_device = None
    serial_thread = None

    try:
        # Open serial device with non-blocking read() (timeout=0)
        serial_device = serial.Serial(args.serial_device, args.baud_rate, timeout=0)

        # Start the serial reading background thread
        serial_thread = threading.Thread(target=serial_run_loop, args=(serial_device,))
        serial_thread.start()

        # Make sure to draw the UI the first time even if there is no serial data
        should_redraw.set()

        # Start the main loop
        curses.wrapper(main, serial_thread)
    finally:
        # Cleanly stop serial thread before exiting
        if serial_thread:
            stop_serial.set()

            if serial_device:
                serial_device.close()

            serial_thread.join()

            # If the thread returned an exception, print it
            if thread_exception:
                traceback.print_exception(*thread_exception)
                sys.stderr.flush()
