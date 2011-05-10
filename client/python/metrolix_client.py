#! /usr/bin/env python
import argparse, urllib2, simplejson, os, sys

parser = argparse.ArgumentParser(description='Interact with Metrolix server')

parser.add_argument('command', help='Command to pass to the server')
parser.add_argument('commandArgs', nargs='*', help='Command specific arguments')
parser.add_argument('--server', dest='server', action='store')

args = parser.parse_args()

serverAddr = args.server
if serverAddr is None:
  serverAddr = os.getenv("METROLIX_SERVER")
if serverAddr is None:
  raise Exception("Server address not found")

if args.command == "start-session":
  if len(args.commandArgs) == 0:
    raise Exception("Usage: start-session project-name [version] [testset]")

  # Hostinfo
  (sysname, nodename, release, version, machine) = os.uname()
  hostinfo = {"name" : nodename}
  hostinfo["cpus"] = 1
  hostinfo["ram_mb"] = 42

  # Global request
  req = {}
  req["project_name"] = args.commandArgs[0]
  req["version"] = "none"
  if len(args.commandArgs) >=  2:
    req["version"] = args.commandArgs[1]
  elif len(args.commandArgs) >= 3:
    req["testset"] = args.commandArgs[2]

  req["host_info"] = hostinfo

  # Send request
  data = simplejson.dumps(req)

  url = urllib2.urlopen(serverAddr + "/server/start_session", data)
  print "%s" % url.read()

elif args.command == "add-report":
  if len(args.commandArgs) != 3 and len(args.commandArgs) != 4:
    raise Exception("Usage: add-report session_token report_name report_type [file]")

  req = {}
  req["session_token"] = args.commandArgs[0]
  req["name"] = args.commandArgs[1]
  req["type"] = args.commandArgs[2]

  if len(args.commandArgs) == 4:
    f = open(args.commandArgs[3])
    lines = f.readlines()
  else:
    lines = sys.stdin.readlines()

  lines = map(lambda x : x.replace("\n", ""), lines)
  text = "\n".join(lines)
  req["text"] = text
  url = urllib2.urlopen(serverAddr + "/server/add_report", simplejson.dumps(req))

elif args.command == "report-result":
  req = {}
  req["session_token"] = args.commandArgs[0]
  req["path"] = args.commandArgs[1]
  req["value"] = args.commandArgs[2]
  if len(args.commandArgs) >= 4:
    req["title"] = args.commandArgs[3]
  if len(args.commandArgs) >= 5:
    req["type"] = args.commandArgs[4]
  url = urllib2.urlopen(serverAddr + "/server/report_result", simplejson.dumps(req))

else:
  print "Invalid command %s" % args.command
