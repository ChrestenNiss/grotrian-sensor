import json,uuid;

print("How many sensors do you wish to configure?\n")
sensNum = int(input('>'));
print("How many sensors do you wish to configure for error sending?\n")
errsensNum = int(input('>'));
print("How many timed sensors do you wish to configure for sending?\n")
timsensNum = int(input('>'));

sList=[]

for i in range(0,sensNum):
	sensor={
		'id' : str(i),
    	'eID' : str(i+100),
    	'sensorGUID' : str(uuid.uuid4()),
    	'sensorSource': 'sensorSource',
    	'sensorType': 'sensorType',
		'sensorName' : 'sensorName',
		'sensorLocation' : 'sensorLocation',
	}
	sList.append(sensor)

for i in range (0,errsensNum):
	sensor={
    	'eID' : str(sensNum+i+100),
    	'sensorGUID' : str(uuid.uuid4()),
    	'sensorSource': 'sensorSource',
    	'sensorType': 'sensorType',
		'sensorName' : 'sensorName',
		'sensorLocation' : 'sensorLocation',
	}
	sList.append(sensor)

for i in range (0,timsensNum):
	sensor={
    	'eID' : str(i+150),
    	'sensorGUID' : str(uuid.uuid4()),
    	'sensorSource': 'sensorSource',
    	'sensorType': 'sensorType',
		'sensorName' : 'sensorName',
		'sensorLocation' : 'sensorLocation',
	}
	sList.append(sensor)

with open('sensorList.json', 'w') as f:
	json.dump(sList, f, indent=4)