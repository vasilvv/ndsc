#!/usr/bin/python

# 
# This is a very simple discuss client which was created to make reading discuss
# meetings less painful
#

from __future__ import division
from __future__ import print_function

import curses, discuss  # discuss always comes with curses
import argparse
import signal
import sys

def die(reason):
    try:
        screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
    except:
        pass

    print(reason, file=sys.stderr)
    sys.exit(1)

class ProgressDisplay(object):
    def __init__(self):
        self.last_text = ""
        curses.curs_set(0)
        screen.nodelay(True)
        screen.keypad(0)

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
    screen.keypad(1)

def main():
    global name, server, path

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

    die("Test")

if __name__ == '__main__':
    main()

