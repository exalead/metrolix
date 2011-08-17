#! /usr/bin/env python
import urllib2, json, os, sys
from optparse import OptionParser

parser = OptionParser(usage='Interact with Metrolix server')

parser.add_option("-c", "--command", dest="command", help='Command to pass to the server (start-session, report-result or add-report)')
#parser.add_option('commandArgs', nargs='*', help='Command specific arguments')
parser.add_option("-s", '--server', dest='server', action='store')

parser.add_option("-p", '--project', dest='project', help="Project name (for start-session only)")
parser.add_option("-v", '--version', dest='version', help="Project version (for start-session only)")
parser.add_option("-b", '--branch', dest='branch', help="Project branch (for start-session only)")

parser.add_option("-n", '--session-name', dest='sn', help="Session name (for start-session only)")
parser.add_option("-t", '--session-testset', dest='st', help="Session test-set (for start-session only)")

(opts, args) = parser.parse_args()

command = opts.command
if command is None:
  print "Command not specified"
  parser.print_help()
  sys.exit(1)

serverAddr = opts.server
if serverAddr is None:
  serverAddr = os.getenv("METROLIX_SERVER")
if serverAddr is None:
  print "Server address not specified"
  parser.print_help()
  sys.exit(1)

if command == "start-session":
  # Hostinfo
  (sysname, nodename, release, version, machine) = os.uname()
  hostinfo = {"name" : nodename}
  hostinfo["cpus"] = 1
  hostinfo["ram_mb"] = 42

  if opts.project is None:
    print "Project not specified"
    parser.print_help()
    sys.exit(1)

  # Global request
  req = {}
  req["project_name"] = opts.project
  req["version"] = opts.version
  req["branch"] = opts.branch
  req["session_name"] = opts.sn
  req["testset"] = opts.st
  req["host_info"] = hostinfo

  data = json.dumps(req)
  url = urllib2.urlopen(serverAddr + "/server/start_session", data)
  print "%s" % url.read()

elif command == "add-report":
  if len(commandArgs) != 3 and len(commandArgs) != 4:
    print "add-report  session_token report_name report_type [file]"
    parser.print_help()
    sys.exit(1)

  req = {}
  req["session_token"] = commandArgs[0]
  req["name"] = commandArgs[1]
  req["type"] = commandArgs[2]

  if len(commandArgs) == 4:
    f = open(commandArgs[3])
    lines = f.readlines()
  else:
    lines = sys.stdin.readlines()

  lines = map(lambda x : x.replace("\n", ""), lines)
  text = "\n".join(lines)
  req["text"] = text
  url = urllib2.urlopen(serverAddr + "/server/add_report", json.dumps(req))

elif command == "report-result":
  if len(args) < 3:
    print "report-result session_token path value [title] [type]"
    parser.print_help()
    sys.exit(1)

  req = {}
  req["session_token"] = args[0]
  req["path"] = args[1]
  req["value"] = args[2]
  if len(args) >= 4:
    req["title"] = args[3]
  if len(args) >= 5:
    req["type"] = args[4]
  url = urllib2.urlopen(serverAddr + "/server/report_result", json.dumps(req))

else:
  print "Invalid command %s" % command
