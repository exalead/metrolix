#! /usr/bin/env python
import urllib2, simplejson, os, sys
from optparse import OptionParser

parser = OptionParser(usage='Interact with Metrolix server')

#parser.add_option('command', help='Command to pass to the server')
#parser.add_option('commandArgs', nargs='*', help='Command specific arguments')
parser.add_option('--server', dest='server', action='store')

(opts, args) = parser.parse_args()

if len(args) < 1:
  raise Exception("Usage: command commandArgs")

command = args[0]
commandArgs = args[1:]

serverAddr = opts.server
if serverAddr is None:
  serverAddr = os.getenv("METROLIX_SERVER")
if serverAddr is None:
  raise Exception("Server address not found")

if command == "start-session":
  if len(commandArgs) == 0:
    raise Exception("Usage: start-session project-name [version] [testset]")

  # Hostinfo
  (sysname, nodename, release, version, machine) = os.uname()
  hostinfo = {"name" : nodename}
  hostinfo["cpus"] = 1
  hostinfo["ram_mb"] = 42

  # Global request
  req = {}
  req["project_name"] = commandArgs[0]
  if len(commandArgs) >=  2:
    req["version"] = commandArgs[1]
  if len(commandArgs) >= 3:
    req["testset"] = commandArgs[2]

  req["host_info"] = hostinfo

  # Send request
  data = simplejson.dumps(req)

  url = urllib2.urlopen(serverAddr + "/server/start_session", data)
  print "%s" % url.read()

elif command == "add-report":
  if len(commandArgs) != 3 and len(commandArgs) != 4:
    raise Exception("Usage: add-report session_token report_name report_type [file]")

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
  url = urllib2.urlopen(serverAddr + "/server/add_report", simplejson.dumps(req))

elif command == "report-result":
  req = {}
  req["session_token"] = commandArgs[0]
  req["path"] = commandArgs[1]
  req["value"] = commandArgs[2]
  if len(commandArgs) >= 4:
    req["title"] = commandArgs[3]
  if len(commandArgs) >= 5:
    req["type"] = commandArgs[4]
  url = urllib2.urlopen(serverAddr + "/server/report_result", simplejson.dumps(req))

else:
  print "Invalid command %s" % command
