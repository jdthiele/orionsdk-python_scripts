# imports
import requests
import orionsdk
import argparse
import getpass
import sys
from validations import val_date, calc_dur

# define the variables needed for automating the process
npm_server = 'SolarWinds-Orion'
cert='server.pem'

# handle some arguments
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", help="Provide the user to connect to the OrionSDK as", required=True)
parser.add_argument("-p", "--password", help="Provide the password for the given user")
parser.add_argument("-n", "--nodes", help="Provide a comma separated list of nodes you want to blackout without any spaces", required=True)
parser.add_argument("-m", "--method", help="Provide the blackout method you want to use in SolarWinds - 'mute' / 'unmanage'", required=True)
parser.add_argument("-s", "--start", help="Provide the start time")
parser.add_argument("-S", "--stop", help="Provide the stop time")
parser.add_argument("-d", "--duration", help="Provide the duration")
args = parser.parse_args()
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
else:
    print("please provide a start stop or duration argument")
    sys.exit(1)

# set the plan timing type and validate/calculate values
if start and stop:
    timetype = "startandStop"
    # validate start
    startdate = val_date(start)
    # validate stop
    stopdate = val_date(stop)
elif start and duration:
    timetype = "startandDuration"
    # validate start
    startdate = val_date(start)
    # validate duration
    stopdate = calc_dur(startdate, duration)
elif start:
    timetype = "start"
    # assume a 1 day duration when no duration or stop arguments are given
    duration = "1d"
    # validate start
    startdate = val_date(start)
    # calculate stop as "duration" from start
    stopdate = calc_dur(startdate, duration)
elif stop:
    timetype = "stop"
    # assume a start time of now
    startdate = None
    # validate stop
    stopdate = val_date(stop)
    # calculate start as now
elif duration:
    timetype = "duration"
    # assume a start time of now
    startdate = None
    # validate duration
    stopdate = calc_dur(startdate, duration)
else:
    print("how did you get here??")

# ask for a password if not provided in args
if args.password:
    password = args.password
else:
    password = getpass.getpass()

# load the swis client and login to the NPM server
swis = orionsdk.SwisClient(npm_server, user, password, verify=False)

# start processing each node
for node in nodes:
    # get the entity URI
    uri_query = 'SELECT Uri from Orion.Nodes where Caption=\'' + node + '\''
    results = swis.query(uri_query)
    node_uri = results['results'][0]['Uri']
    
    # check if the node is already muted
    query = 'SELECT A.ID, N.Caption, A.SuppressFrom, A.SuppressUntil FROM Orion.AlertSuppression A JOIN Orion.Nodes N ON N.Uri = A.EntityUri WHERE N.Caption = \'' + node + '\''
    muted_results = swis.query(query)
    if muted_results:
        print(muted_results)
        print("node is already muted, skipping")
        continue

    # check if the node is already unmanaged
    query = 'SELECT Caption, UnManageFrom, UnManageUntil FROM Orion.Nodes WHERE Unmanaged = TRUE AND Caption = \'' + node + '\''
    unmanaged_results = swis.query(query)
    if unmanaged_results:
        print(unmanaged_results)
        print("node is already unmanaged, skipping")
        continue

    # mute alerts
    if method == 'mute':
        results = swis.invoke('Orion.AlertSuppression','SuppressAlerts', node_uri, startdate, stopdate )
    elif method == 'unmanaged':
        print('not ready for this yet')
    else:
        print('please provide a method of either "mute" or "unmanage"')
        sys.exit(5)

# Exit with a code of 0 indicating all went well
sys.exit(0)