#!/usr/bin/python
# -*- coding: utf-8 -*-

# 
# This is a very simple discuss client which was created to make reading discuss
# meetings less painful. It is sort of ugly and contains globals.
#

from __future__ import division
from __future__ import print_function

import curses, discuss  # discuss always comes with curses

import argparse
import locale
import signal
import sys

# Globals initialization
pos_cur = 0
pos_top = 0
viewed_transaction = None

# Functions

def die(reason = ""):
    try:
        screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
    except:
        pass

    if screen != "":
        print(reason, file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)

class ProgressDisplay(object):
    def __init__(self):
        self.last_text = ""
        curses.curs_set(0)
        screen.nodelay(True)

    def display_progress(this, cur, total, left):
        done = total - left
        percent = done / total * 100
        output = "%.02f %% (%i / %i)" % (percent, done, total)

        max_y, max_x = screen.getmaxyx()
        mid_y = max_y // 2
        mid_x = max_x // 2

        screen.erase()
        screen.addstr(mid_y, mid_x - len(output) // 2, output)
        screen.refresh()

        ch = screen.getch()
        if ch == ord('q') or ch == 27:
            die("Terminated by user while reading the list of the meetings")

def init_meeting():
    global client, meeting, transactions

    try:
        client = discuss.Client(server)
        meeting = discuss.Meeting(client, path)
        transactions = list(meeting.transactions(feedback=ProgressDisplay().display_progress))
    except Exception as err:
        die(err.message)

def init_ui():
    global screen

    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()

def pad(text, maxlen, right=False):
    padding = " " * (maxlen - len(text))
    if right:
        return padding + text
    else:
        return text + padding

def format_transaction_row(trn, width):
    number_column_len = len(str(max_number))
    sender_column_len = min(width // 4, max_sender_len)
    date_column_len = 19 if 19 <= width // 4 else 10
    subject_column_len = width - number_column_len - sender_column_len - date_column_len - 14
    if subject_column_len < 0:
        # Terminal is too narrow, give up
        return ""

    def truncate_column(text, maxlen):
        if len(text) <= maxlen:
            return pad(text, maxlen)
        else:
            return text[0:maxlen-1] + '…'

    number_column = pad(str(trn.number), number_column_len, True)
    sender_column = truncate_column(trn.signature, sender_column_len)
    subject_column = truncate_column(trn.subject, subject_column_len)
    date_column = trn.date_entered.isoformat(' ')[0:date_column_len]
    return " %s    %s    %s    %s " % (number_column, sender_column, subject_column, date_column)

def redraw():
    global pos_cur, pos_top, viewed_transaction, rows

    max_y, max_x = screen.getmaxyx()
    rows = max_y - 6

    # Scrolling down
    if pos_cur - pos_top > rows:
        pos_top += 1
    # Resizing or scrolling up
    if pos_cur - pos_top > rows or pos_cur < pos_top:
        pos_top = pos_cur
    # Out-of-range safeguards 
    if pos_cur < 0:
        pos_cur = 0
        pos_top = 0
    if pos_cur >= len(transactions):
        pos_cur = len(transactions) - 1
    if pos_top > len(transactions) - rows:
        pos_top = len(transactions) - rows - 1 
    if pos_top < 0:
        pos_top = 0

    screen.erase()
    
    # Corners of the main window
    screen.addstr(1, 1, '┌')
    screen.addstr(max_y-2, 1, '└')
    screen.addstr(1, max_x-2, '┐')
    screen.addstr(max_y-2, max_x-2, '┘')

    # Borders of the main window
    for i in range(2, max_y-2):
        screen.addstr(i, 1, '│')
        screen.addstr(i, max_x-2, '│')
    for i in range(2, max_x-2):
        screen.addstr(1, i, '─')
        screen.addstr(max_y-2, i, '─')

    current_transactions = transactions[pos_top:pos_top + rows + 1]

    for i in range(0, len(current_transactions)):
        cur = pos_cur - pos_top == i
        trn = current_transactions[i]
        text = format_transaction_row(trn, max_x - 6)
        if cur:
            screen.addstr(2 + i, 3, text, curses.A_REVERSE)
        else:
            screen.addstr(2 + i, 3, text)

    footer = " %i/%i " % (pos_cur + 1, len(transactions))
    screen.addstr(max_y-2, 6, footer)

def main_loop():
    global pos_cur, pos_top, viewed_transaction
    global max_number, max_sender_len

    screen.nodelay(False)
    screen.keypad(True)

    max_number = max(trn.number for trn in transactions)
    max_sender_len = max(len(trn.signature) for trn in transactions)

    redraw()

    while True:
        ch = screen.getch()

        if viewed_transaction == None:
            if ch == ord('q'):
                return
            if ch == curses.KEY_DOWN:
                pos_cur += 1
            if ch == curses.KEY_UP:
                pos_cur -= 1
            if ch == curses.KEY_PPAGE:
                pos_top -= rows
                pos_cur -= rows
            if ch == curses.KEY_NPAGE:
                pos_top += rows
                pos_cur += rows
            if ch == curses.KEY_HOME:
                pos_cur = 0
                pos_top = 0
            if ch == curses.KEY_END:
                pos_cur = len(transactions) - 1
                pos_top = pos_cur - rows

        redraw()

def main():
    global name, server, path

    locale.setlocale(locale.LC_ALL, '')
    arg_parser = argparse.ArgumentParser(description="Discuss meeting viewer")
    arg_parser.add_argument('meeting_name', help="Name of the meeting to view")

    args = arg_parser.parse_args()
    name = args.meeting_name

    rcfile = discuss.RCFile()
    meeting_location = rcfile.lookup(name)
    if not meeting_location:
        die("Meeting %s not found in .meetings file" % name)
    server, path = meeting_location

    init_ui()
    init_meeting()

    main_loop()
    die()

if __name__ == '__main__':
    main()

