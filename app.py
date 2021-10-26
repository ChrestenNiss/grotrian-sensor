import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
import datetime, uuid, json, logging, os, sys, flask

from azure.cosmos.partition_key import PartitionKey
from flask import request
from configparser import ConfigParser
from os.path import exists
from logging.handlers import RotatingFileHandler

app = flask.Flask(__name__)

config = ConfigParser()

# Check if configuration file exists. If not query user for data
# Otherwise simply load all necessary information
if not exists('config.ini'):
    config["DBINFO"] = {
    "host" : input("Enter cloud host address: "),
    "master_key": input("Enter access key: "),
    "database_id": input("Enter database id/name: "),
    "source_id": input("Enter source unique identifier: "),
    "source_name": input("Enter source name: "),
    }
    with open('config.ini', 'w') as conf:
        config.write(conf)
        exit()
else:
    config.read('config.ini')
    HOST = config.get('DBINFO','host')
    MASTER_KEY = config.get('DBINFO','master_key')
    DATABASE_ID = config.get('DBINFO','database_id')
    SOURCE_ID = config.get('DBINFO','source_id')
    SOURCE_NAME = config.get('DBINFO','source_name')

# Define loggers

root = logging.getLogger()
operation = logging.getLogger('operationLogger')
azure = logging.getLogger('azure')

# Define handlers for logs

streamHandler = logging.StreamHandler(sys.stdout)
rootFH = RotatingFileHandler('main.log',maxBytes=52428800,backupCount=10)
opFH = RotatingFileHandler('operation.log',maxBytes=52428800,backupCount=10)
azFH = RotatingFileHandler('azure.log',maxBytes=52428800,backupCount=10)

# Configure loggers level

root.setLevel(logging.DEBUG)
operation.setLevel(logging.DEBUG)
azure.setLevel(logging.WARN)
streamHandler.setLevel(logging.DEBUG)

# Format loggers/handlers

defFormatter = logging.Formatter('%(asctime)s : %(name)s  : %(funcName)s : %(levelname)s : %(message)s')
streamHandler.setFormatter(defFormatter)
rootFH.setFormatter(defFormatter)
opFH.setFormatter(defFormatter)
azFH.setFormatter(defFormatter)

# Add handlers

root.addHandler(rootFH)
root.addHandler(streamHandler)
operation.addHandler(opFH)
azure.addHandler(azFH)

# Variable to handle logging with a block

actionLog = []

# Check if the sensor list file exists and load it. Otherwise notify of problem and exit

if exists('sensorList.json'):
    with open('sensorList.json') as f:
        sensorList = json.load(f)
else:
    open('sensorList.json','x').close()
    root.error('No sensor list file present, created empty file to prevent execution failure, restart the script once the sensor list has been created.')


# Default route
@app.route('/', methods=['GET'])
def home():
    return '''<h1>Sensor data ingestion API</h1>
                <p>Flask API has been reached. Other endpoints are available.</p>'''


# Siemens PLC error and timed values endpoint
@app.route('/S7/in/error', methods=['POST'])
def postSensorErrorData():
    
    # Instantiate locally used variables
    data = request.get_json()
    using_id = int(data['id'].strip())
    client = getCosmosClient()
    erval = 0
    currentDateTime = datetime.datetime.now()
    docID = str(uuid.uuid4())
    found = False
    locID = 0

    actionLog.append("LOCAL-ID{0} [RID:{0}\tVal:{1}] - {2}".format(using_id,erval,currentDateTime.strftime("%m/%d/%Y %H:%M:%S")))
    
    # Check if the sensor exists within the defined sensor list
    for s in sensorList:
        if('eID' in s):
            if type(s['eID']) is int:
                locID = s['eID']
            else:
                locID = int(s['eID'].strip())

            if(using_id == locID):
                sens = s
                found = True
                actionLog.append("[Found LOCAL-ID{0} within local sensor list]".format(using_id))

    if(not found):
        actionLog.append("[ LOCAL-ID{0} cannot be found within the local sensorlist ]".format(using_id))
        actionLog.append("END-LOCAL-ID{0} - {1}".format(using_id,currentDateTime))
        operation.warn("\n".join(actionLog))
        actionLog.clear()
        return "No such sensor",404

    # Check sensor ID
    # If its below 150 it is a normal error sensor and it is sent to the error container
    # Its value is also converted to a hexadecimal format for easy lookup
    # If its above 150 it is a timed sensor and sent to the appropriate container
    if(using_id>=150):
        USING_CONT_ID = "{0}_{1}_timed".format(SOURCE_NAME.replace(" ","_").lower(),sens['sensorType'])
        erval = int(data['v'].strip())
    else:
        USING_CONT_ID = "{0}_errors".format(SOURCE_NAME.replace(" ","_").lower())
        erval = hex(int(data['v'].strip()))

    container = getContainer(client,USING_CONT_ID)

    # Create sensor structure for the database
    sensor={
        'id' : docID,
        'partitionKey' : sens['sensorType'],
        'sourceName': SOURCE_NAME,
        'sourceGUID': SOURCE_ID,
        'sensorTimestamp' : currentDateTime.strftime("%d/%m/%Y %H:%M:%S"),
        'sensorDate': currentDateTime.strftime("%d/%m/%Y"),
        'sensorTime': currentDateTime.strftime("%H:%M:%S"),
        'sensorGUID' : sens['sensorGUID'],
        'sensorSource': sens['sensorSource'],
        'sensorType': sens['sensorType'],
        'sensorName': sens['sensorName'],
        'sensorLocation': sens['sensorLocation'],
        'sensorErr' : erval,
    }

    # Insert the sensor after processing into the database
    container.create_item(body=sensor)
    actionLog.append("[Successfully inserted sensor into container {0} with data:] \n[{1}]".format(USING_CONT_ID,data))
    actionLog.append("[Post processed data for LOCAL-ID{0} inserted as:]\n\t{1}".format(using_id,"\n\t".join("[{} : {}]".format(k,v) for k,v in sensor.items())))
    actionLog.append("END-LOCAL-ID{0} - {1}".format(using_id,currentDateTime))
    operation.debug("\n".join(actionLog))
    actionLog.clear()
    return 'Operation successful',200

# Siemens PLC sensor data endpoint
@app.route('/S7/in/sensor', methods=['POST'])
def postSensorData():

    # Instantiate locally used variables

    data = request.get_json()
    using_id = int(data['id'].strip())
    currentDateTime = datetime.datetime.now()
    docID = str(uuid.uuid4())
    found = False
    locID = 0

    actionLog.append("LOCAL-ID{0} [RID:{0}\tVal:{1}] - {2}".format(using_id,data['v'].strip(),currentDateTime.strftime("%m/%d/%Y %H:%M:%S")))

    # Check if the sensor exists within the defined sensor list
    for s in sensorList:
        if('id' in s):
            if type(s['id']) is int:
                locID = s['id']
            else:
                locID = int(s['id'].strip())

            if(using_id == locID):
                sens = s
                found = True
                actionLog.append("[Found LOCAL-ID{0} within local sensor list]".format(using_id))

    if(not found):
        actionLog.append("[ LOCAL-ID{0} cannot be found within the local sensorlist ]".format(using_id))
        actionLog.append("END-LOCAL-ID{0} - {1}".format(using_id,currentDateTime))
        operation.warn("\n".join(actionLog))
        actionLog.clear()
        return "No such sensor",404

    client = getCosmosClient()
    container = getContainer(client,"{0}_{1}".format(SOURCE_NAME.replace(" ","_").lower(),sens['sensorType']))

    # Create sensor structure for the database
    sensor={
        'id' : docID,
        'partitionKey' : sens['sensorType'],
        'sourceName': SOURCE_NAME,
        'sourceGUID': SOURCE_ID,
        'sensorTimestamp' : currentDateTime.strftime("%d/%m/%Y %H:%M:%S"),
        'sensorDate': currentDateTime.strftime("%d/%m/%Y"),
        'sensorTime': currentDateTime.strftime("%H:%M:%S"),
        'sensorGUID' : sens['sensorGUID'],
        'sensorSource' : sens['sensorSource'],
        'sensorType' : sens['sensorType'],
        'sensorName': sens['sensorName'],
        'sensorLocation' : sens['sensorLocation'],
        'sensorValue' : float(data['v'].strip())
    }

    # Insert the sensor after processing into the database
    container.create_item(body=sensor)
    actionLog.append("[Successfully inserted sensor into container {0} with data:] \n[{1}]".format("{0}_{1}".format(SOURCE_NAME.replace(" ","_").lower(),sens['sensorType']),data))
    actionLog.append("[Post processed data for LOCAL-ID{0} inserted as:]\n\t{1}".format(using_id,"\n\t".join("[{} : {}]".format(k,v) for k,v in sensor.items())))
    actionLog.append("END-LOCAL-ID{0} - {1}".format(using_id,currentDateTime))
    operation.debug("\n".join(actionLog))
    actionLog.clear()
    return 'Ok',200

# Retrieve azure cosmos DB container
def getContainer(client,USING_CONT_ID):
    try:
        try:
            db = client.create_database(id=DATABASE_ID)
            root.debug('Database with id \'{0}\' created'.format(DATABASE_ID))
        except exceptions.CosmosResourceExistsError:
            db = client.get_database_client(DATABASE_ID)
            root.info('Database with id \'{0}\' was found'.format(DATABASE_ID))
        try:
            container = db.create_container(id=USING_CONT_ID, partition_key=PartitionKey(path='/partitionKey'), analytical_storage_ttl=-1)
            root.debug('Container with id \'{0}\' created'.format(USING_CONT_ID))
        except exceptions.CosmosResourceExistsError:
            container = db.get_container_client(USING_CONT_ID)
            root.info('Container with id \'{0}\' was found'.format(USING_CONT_ID))

    except exceptions.CosmosHttpResponseError as e:
        root.error('\nCreating sensor data has caught an error. {0}'.format(e.message))
    finally:
        return container


# Retrieve azure cosmos DB client singleton.
def getCosmosClient():
    global client
    client = cosmos_client.CosmosClient(
        HOST, 
        {'masterKey': MASTER_KEY}, 
        user_agent="RaspberryPiS7Endpoint", 
        user_agent_overwrite=True
        )
    return client

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)