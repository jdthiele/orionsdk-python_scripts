# imports
import requests
import orionsdk
import argparse
import getpass
import sys
import urllib3
from datetime import datetime
from . import manage #import mute_nodes, unmanage_nodes, resume_nodes
from . import date_validations #import val_date, calc_dur

#shorten functions path
mute_nodes = manage.mute_nodes
unmanage_nodes = manage.unmanage_nodes
resume_nodes = manage.resume_nodes
val_date = date_validations.val_date
calc_dur = date_validations.calc_dur

# disable insecure warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# define some help menu strings

help_header = """This script will help automate the process to mute / unmanage / resume nodes in SolarWinds.

Refer to https://github.com/jdthiele/orionsdk-python_scripts/tree/master/sw-mute-unmanage for detailed help."""

# handle some arguments
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=help_header)
  parser.add_argument("-w", "--npm_server", help="Provide the name of the SolarWinds server", required=True)
  parser.add_argument("-n", "--nodes", help="Provide a comma separated list of nodes you want to blackout without any spaces", required=True)
  parser.add_argument("-m", "--method", help="Provide the blackout method you want to use in SolarWinds - mute / unmanage / resume", required=True)
  parser.add_argument("-u", "--user", help="Provide the user to connect to the OrionSDK as", required=True)
  parser.add_argument("-p", "--password", help="Provide the password for the given user, or omit to be prompted")
  parser.add_argument("-s", "--start", help="Provide the start time")
  parser.add_argument("-S", "--stop", help="Provide the stop time")
  parser.add_argument("-d", "--duration", help="Provide the duration")
  args = parser.parse_args()
  npm_server = args.npm_server
  user = args.user
  nodes = args.nodes.split(",")
  method = args.method
  start = args.start
  stop = args.stop
  duration = args.duration
  
  # check for proper timing type arguments
  if start or stop or duration:
      if stop and duration:
          print("I cannot take a stop time with duration")
          sys.exit(2)
      if method == 'resume':
          print("NOTICE: resume method will ignore any time arguments given")
          start = None
          stop = None
          duration = None
  elif method == 'resume':
      True
  else:
      print("please provide a start stop or duration argument")
      sys.exit(1)
  
  
  # set the plan timing type and validate/calculate values
  if start and stop:
      # validate start
      startdate = val_date(start)
      # validate stop
      stopdate = val_date(stop)
  elif start and duration:
      # validate start
      startdate = val_date(start)
      # validate duration
      stopdate = calc_dur(startdate, duration)
  elif start:
      # assume a 1 day duration when no duration or stop arguments are given
      duration = "1d"
      # validate start
      startdate = val_date(start)
      # calculate stop as "duration" from start
      stopdate = calc_dur(startdate, duration)
  elif stop:
      # assume a start time of now
      startdate = datetime.utcnow()
      # validate stop
      stopdate = val_date(stop)
      # calculate start as now
  elif duration:
      # assume a start time of now
      startdate = datetime.utcnow()
      # validate duration
      stopdate = calc_dur(startdate, duration)
  elif method == 'resume':
      True
  else:
      print("how did you get here??")
  
  # ask for a password if not provided in args
  if args.password:
      password = args.password
  else:
      password = getpass.getpass()
  
  # load the swis client and login to the NPM server
  swis = orionsdk.SwisClient(npm_server, user, password, verify=False)
  
  # execute the proper method 
  if method == 'mute':
      mute_nodes(nodes, swis, startdate, stopdate)
  elif method == 'unmanage':
      unmanage_nodes(nodes, swis, startdate, stopdate)
  elif method == 'resume':
      resume_nodes(nodes, swis)
  else:
      print('please provide a method of either "mute" or "unmanage"')
      sys.exit(5)
  
# Exit with a code of 0 indicating all went well
sys.exit(0)