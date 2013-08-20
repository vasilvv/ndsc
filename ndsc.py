#!/usr/bin/python

# 
# This is a very simple discuss client which was created to make reading discuss
# meetings less painful
#

from __future__ import print_function

import curses, discuss  # discuss always comes with curses
import argparse, sys

def die(reason):
    print(reason, file=sys.stderr)
    sys.exit(1)

def init_meeting():
    global client, meeting, transactions

    try:
        client = discuss.Client(server)
        meeting = discuss.Meeting(client, path)
        transactions = list(meeting.transactions())
    except Exception as err:
        die(err.message)

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

    init_meeting()

if __name__ == '__main__':
    main()

