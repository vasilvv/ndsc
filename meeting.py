#!/usr/bin/python

#
# A simple tool to manage the discuss meetings.
#

import argparse
import discuss
import sys

acl_flags = "acdorsw"

def die(text):
    sys.stderr.write("%s\n" % text)
    sys.exit(1)

def get_user_realm(client):
    user = client.who_am_i()
    return user[user.find('@'):]

def add_meeting():
    if ":" in args.meeting:
        server, path = args.meeting.split(":", 2)
        if not path.startswith("/"):
            path = "/var/spool/discuss/" + path

        client = discuss.Client(server, timeout = 5)
        mtg = discuss.Meeting(client, path)
    else:
        mtg = discuss.locate(args.meeting)
        if not mtg:
            die("Meeting %s was not found." % args.meeting)

    rcfile = discuss.RCFile()
    rcfile.add(mtg)
    rcfile.save()

def list_meetings():
    rcfile = discuss.RCFile()
    rcfile.load()
    servers = list({ entry['hostname'] for entry in rcfile.entries.values() })
    servers.sort()
    for server in servers:
        meetings = [ "%s [%s]" % ( entry['displayname'], ", ".join(entry['names']) )
                for entry in rcfile.entries.values() if entry['hostname'] == server ]
        meetings.sort()
        print "--- Meetings on %s ---" % server
        for meeting in meetings:
            print "* %s" % meeting
        print ""

def get_meeting(name):
    rcfile = discuss.RCFile()
    meeting_location = rcfile.lookup(name)
    if not meeting_location:
        sys.stderr.write("Meeting %s not found in .meetings file\n" % name)
        sys.exit(1)

    server, path = meeting_location
    client = discuss.Client(server, timeout = 5)
    return discuss.Meeting(client, path)

def list_acl():
    meeting = get_meeting(args.meeting)
    acl = meeting.get_acl()
    acl.sort(key = lambda acl: acl[0])

    print "%s   Principal" % acl_flags
    print "%s   ---------" % ("-" * len(acl_flags))
    for principal, modes in acl:
        print "%s   %s" % (modes, principal)

def set_acl():
    meeting = get_meeting(args.meeting)

    if args.bits == "null" or args.bits == "none":
        bits = ""
    else:
        bits = args.bits

    bits = bits.replace(" ", "")
    if not all(bit in acl_flags for bit in bits):
        wrong_bits = ", ".join(set(bits) - set(acl_flags))
        die("Invalid bits present in ACL: %s" % wrong_bits)

    principal = args.principal
    if "@" not in principal:
        principal += get_user_realm(meeting.client)

    meeting.set_access(principal, bits)

def parse_args():
    global args

    argparser = argparse.ArgumentParser(description = "Manage discuss meetings")
    subparsers = argparser.add_subparsers()

    parser_add = subparsers.add_parser('add', help = 'Add a meeting to the personal meetings list')
    parser_add.add_argument('meeting', help = 'The name of the meeting (may be prefixed by server name using a colon)')

    parser_list = subparsers.add_parser('list', help = 'Show all the meetings in the personal list')

    parser_listacl = subparsers.add_parser('listacl', help = 'Show the ACL of the specified discuss meeting')
    parser_listacl.add_argument('meeting', help = 'The meeting to display the ACL of')

    parser_setacl = subparsers.add_parser('setacl', help = 'Change the access bits of the specified discuss user')
    parser_setacl.add_argument('meeting', help = 'The meeting to modify the ACL of')
    parser_setacl.add_argument('principal', help = 'The name of the Kerberos principal in question')
    parser_setacl.add_argument('bits', help = 'The access modes to be set for the specified principal')

    parser_add.set_defaults(handler = add_meeting)
    parser_list.set_defaults(handler = list_meetings)
    parser_listacl.set_defaults(handler = list_acl)
    parser_setacl.set_defaults(handler = set_acl)

    args = argparser.parse_args()
    args.handler()

try:
    parse_args()
except Exception as err:
    die(err)

