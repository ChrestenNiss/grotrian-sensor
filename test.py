import random, requests, time

url = 'http://192.168.50.179:5000/S7/in/sensor'
ts1guid = '2bda14f2-e487-45b8-9dd3-6da8c9062001'
ts1t = 'temp'
ts1l = 'Tank 1'
ts2guid = 'cd0005fc-6544-41fb-aba9-98d3f67451b9'
ts2t = 'temp'
ts2l = 'Tank 2'
ts3guid = '7f0764bd-5955-4cf9-84c1-5aa015e242b2'
ts3t = 'temp'
ts3l = 'Tank 3'
ts4guid = '7caeae21-fb48-4c43-ba6f-4a4c3669b72c'
ts4t = 'temp'
ts4l = 'Stald'
hs1guid = '0e2acc0e-67e9-468b-826d-b2f0774a5af7'
hs1t = 'humidity'
hs1l = 'Stald 1'
hs2guid = '4c69c474-1569-45a9-819f-93ffca8630be'
hs2t = 'humidity'
hs2l = 'Stald 2'
hs3guid = 'b3493e0e-1a75-4fbd-ae4d-58c9662d43de'
hs3t = 'humidity'
hs3l = 'Milking Stable'
hs4guid = 'cd82fd9b-9cc8-4bee-94ca-b49f0a79cdc8'
hs4t = 'humidity'
hs4l = 'Hall'
as1guid = '136d7824-6435-4746-942d-586a02367498'
as1t = 'accel'
as1l = 'Cleaning 1'
as2guid = 'cdef7186-dc87-4f22-8958-8e65f56143f8'
as2t = 'accel'
as2l = 'Cleaning 1-2'
as3guid = '14530d6b-9359-4ab7-b01c-bbde047d9961'
as3t = 'accel'
as3l = 'Cleaning 2'

while True:
    requests.post(url, json = {
        'sensorGUID': ts1guid,
        'sensorType': ts1t,
        'sensorValue': str(round(random.uniform(20,25),2)),
        'sensorLoc': ts1l
    })
    requests.post(url, json = {
        'sensorGUID': ts2guid,
        'sensorType': ts2t,
        'sensorValue': str(round(random.uniform(20,25),2)),
        'sensorLoc': ts2l
    })
    requests.post(url, json = {
        'sensorGUID': ts3guid,
        'sensorType': ts3t,
        'sensorValue': str(round(random.uniform(20,25),2)),
        'sensorLoc': ts3l
    })
    requests.post(url, json = {
        'sensorGUID': ts4guid,
        'sensorType': ts4t,
        'sensorValue': str(round(random.uniform(20,25),2)),
        'sensorLoc': ts4l
    })
    requests.post(url, json = {
        'sensorGUID': hs1guid,
        'sensorType': hs1t,
        'sensorValue': str(round(random.uniform(65,99)))+'%',
        'sensorLoc': hs1l
    })
    requests.post(url, json = {
        'sensorGUID': hs2guid,
        'sensorType': hs2t,
        'sensorValue': str(round(random.uniform(65,99)))+'%',
        'sensorLoc': hs2l
    })
    requests.post(url, json = {
        'sensorGUID': hs3guid,
        'sensorType': hs3t,
        'sensorValue': str(round(random.uniform(65,99)))+'%',
        'sensorLoc': hs3l
    })
    requests.post(url, json = {
        'sensorGUID': hs4guid,
        'sensorType': hs4t,
        'sensorValue': str(round(random.uniform(65,99)))+'%',
        'sensorLoc': hs4l
    })
    requests.post(url, json = {
        'sensorGUID': as1guid,
        'sensorType': as1t,
        'sensorValue': str(round(random.uniform(30,100))),
        'sensorLoc': as1l
    })
    requests.post(url, json = {
        'sensorGUID': as2guid,
        'sensorType': as2t,
        'sensorValue': str(round(random.uniform(30,100))),
        'sensorLoc': as2l
    })
    requests.post(url, json = {
        'sensorGUID': as3guid,
        'sensorType': as3t,
        'sensorValue': str(round(random.uniform(30,100))),
        'sensorLoc': as3t
    })
    print('Sent simulated sensor data')
    time.sleep(60)
    
