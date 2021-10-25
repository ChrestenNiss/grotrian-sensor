import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import datetime, uuid, json, logging, os, sys

import flask
from flask import request

app = flask.Flask(__name__)

from configparser import ConfigParser
from os.path import exists

config = ConfigParser()

if not exists('config.ini'):
    config["DBINFO"] = {
    "host" : input("Enter cloud host address: "),
    "master_key": input("Enter access key: "),
    "database_id": input("Enter database id/name: "),
    "container_id": input("Enter container id/name: "),
    "partition_key": input("Enter partition key/name: "),
    "error_container_id": input("Enter error container key/name: "),
    "source_id": input("Enter source unique identifier: "),
    "source_name": input("Enter source name: "),
    "occasional_container_id": input("Enter timed container key/name: "),
    }
    with open('config.ini', 'w') as conf:
        config.write(conf)
        exit()
else:
    config.read('config.ini')
    HOST = config.get('DBINFO','host')
    MASTER_KEY = config.get('DBINFO','master_key')
    DATABASE_ID = config.get('DBINFO','database_id')
    CONTAINER_ID = config.get('DBINFO','container_id')
    PARTITION_KEY = config.get('DBINFO','partition_key')
    SOURCE_ID = config.get('DBINFO','source_id')
    SOURCE_NAME = config.get('DBINFO','source_name')
    ERROR_CONTAINER_ID = config.get('DBINFO','error_container_id')
    OC_CONT_ID = config.get('DBINFO','occasional_container_id')

if not exists('requests.log'):
    open('requests.log','x').close()

if not exists('actions.log'):
    open('actions.log','x').close()

gbSize = 1073741824

if(os.stat('requests.log').st_size > gbSize):
    os.remove('requests.log')

if(os.stat('actions.log').st_size > gbSize):
    os.remove('actions.log')

root = logging.getLogger()
root.setLevel(logging.DEBUG)

applog = logging.getLogger("actionlogger")
applog.setLevel(logging.DEBUG)

logging.getLogger('azure').setLevel(logging.ERROR)
stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)
streamformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
stream.setFormatter(streamformat)

rootfilehandler = logging.FileHandler('requests.log')
actionfilehandler = logging.FileHandler('actions.log')

root.addHandler(rootfilehandler)
applog.addHandler(actionfilehandler)
actionLog = []


if exists('sensorList.json'):
    with open('sensorList.json') as f:
        sensorList = json.load(f)
else:
    open('sensorList.json','x').close()
    root.debug('No sensor list file present, created empty file to prevent execution failure, restart the script once the sensor list has been created.')


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Local testing ground</h1>
<p>Reached flask api</p>'''

@app.route('/S7/in/error', methods=['POST'])
def postSensorErrorData():
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    
    data = request.get_json()
    using_id = int(data['id'].strip())

    if(using_id>=150):
        USING_CONT_ID = OC_CONT_ID
        eval = int(data['v'].strip())
        actionLog.append("LOCAL-ID{0} [RID:{0}\tVal:{1}] - {2}".format(using_id,eval,datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")))
    else:
        USING_CONT_ID = ERROR_CONTAINER_ID
        eval = hex(int(data['v'].strip()))
        actionLog.append("LOCAL-ID{0} [RID:{0}\tVal:{1}] - {2}".format(using_id,eval,datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")))

    try:
        try:
            db = client.create_database(id=DATABASE_ID)
            root.debug('Database with id \'{0}\' created'.format(DATABASE_ID))
        except exceptions.CosmosResourceExistsError:
            db = client.get_database_client(DATABASE_ID)
            #root.debug('Database with id \'{0}\' was found'.format(DATABASE_ID))
        try:
            container = db.create_container(id=USING_CONT_ID, partition_key=PartitionKey(path='/partitionKey'), analytical_storage_ttl=-1)
            root.debug('Container with id \'{0}\' created'.format(USING_CONT_ID))
        except exceptions.CosmosResourceExistsError:
            container = db.get_container_client(USING_CONT_ID)
            #root.debug('Container with id \'{0}\' was found'.format(USING_CONT_ID))

    except exceptions.CosmosHttpResponseError as e:
        root.debug('\nCreating sensor data has caught an error. {0}'.format(e.message))

    finally:
            currentDateTime = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            docID = str(uuid.uuid4())
            found = False
            locID = 0

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
                applog.debug("\n".join(actionLog))
                actionLog.clear()
                return "No such sensor",404

            sensor={
                'id' : docID,
                'partitionKey' : sens['sensorType'],
                'sourceName': SOURCE_NAME,
                'sourceGUID': SOURCE_ID,
                'sensorTimestamp' : currentDateTime,
                'sensorGUID' : sens['sensorGUID'],
                'sensorSource': sens['sensorSource'],
                'sensorType': sens['sensorType'],
                'sensorErr' : eval,
            }

            container.create_item(body=sensor)
            actionLog.append("[Successfully inserted sensor into container {0} with data:] \n[{1}]".format(USING_CONT_ID,data))
            actionLog.append("[Post processed data for LOCAL-ID{0} inserted as:]\n\t{1}".format(using_id,"\n\t".join("[{} : {}]".format(k,v) for k,v in sensor.items())))
            actionLog.append("END-LOCAL-ID{0} - {1}".format(using_id,currentDateTime))
            applog.debug("\n".join(actionLog))
            actionLog.clear()
            return 'Ok',200

@app.route('/S7/in/sensor', methods=['POST'])
def postSensorData():
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)

    try:
        try:
            db = client.create_database(id=DATABASE_ID)
            root.debug('Database with id \'{0}\' created'.format(DATABASE_ID))
        except exceptions.CosmosResourceExistsError:
            db = client.get_database_client(DATABASE_ID)
            #root.debug('Database with id \'{0}\' was found'.format(DATABASE_ID))
        try:
            container = db.create_container(id=CONTAINER_ID, partition_key=PartitionKey(path='/partitionKey'), analytical_storage_ttl=-1)
            root.debug('Container with id \'{0}\' created'.format(CONTAINER_ID))
        except exceptions.CosmosResourceExistsError:
            container = db.get_container_client(CONTAINER_ID)
            #root.debug('Container with id \'{0}\' was found'.format(CONTAINER_ID))

    except exceptions.CosmosHttpResponseError as e:
        root.debug('\nCreating sensor data has caught an error. {0}'.format(e.message))

    finally:
            data = request.get_json()
            using_id = int(data['id'].strip())

            currentDateTime = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            docID = str(uuid.uuid4())
            
            found = False
            locID = 0
            actionLog.append("LOCAL-ID{0} [RID:{0}\tVal:{1}] - {2}".format(using_id,data['v'].strip(),currentDateTime))

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
                applog.debug("\n".join(actionLog))
                actionLog.clear()
                return "No such sensor",404

            sensor={
                'id' : docID,
                'partitionKey' : sens['sensorType'],
                'sourceName': SOURCE_NAME,
                'sourceGUID': SOURCE_ID,
                'sensorTimestamp' : currentDateTime,
                'sensorType' : sens['sensorType'],
                'sensorSource' : sens['sensorSource'],
                'sensorGUID' : sens['sensorGUID'],
                'sensorValue' : float(data['v'].strip())
            }

            container.create_item(body=sensor)
            actionLog.append("[Successfully inserted sensor into container {0} with data:] \n[{1}]".format(CONTAINER_ID,data))
            actionLog.append("[Post processed data for LOCAL-ID{0} inserted as:]\n\t{1}".format(using_id,"\n\t".join("[{} : {}]".format(k,v) for k,v in sensor.items())))
            actionLog.append("END-LOCAL-ID{0} - {1}".format(using_id,currentDateTime))
            applog.debug("\n".join(actionLog))
            actionLog.clear()
            return 'Ok',200
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")