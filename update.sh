#!/usr/bin/env bash

session="sensorInput"
workingDir="/home/pi/grotrian-sensor"

if [ ! -d $workingDir ]; then
	mkdir $workingDir
	cd $workingDir
else
	cd $workingDir
fi

function UOI() {
	cd $workingDir
	git clone https://github.com/AlexanderADM/grotrian-sensor.git
	shopt -s dotglob
	mv -u grotrian-sensor/* ./
	rm -fr grotrian-sensor
	git reset --hard
	git pull --force
	git checkout .
	pip3 install -r requirements.txt
}

function run() {
	git fetch
	if [ ! -f "app.py" ]; then
		echo "Python app not found, running update/install function."
		UOI
		echo "Finished installing the script."
		screen -dmS $session python3 app.py
		echo "Script is now running in session \'sensorInput\'"
	elif git status --branch --porcelain -uno | grep behind; then
		echo "Differences from main branch found, updating script."
		echo "Terminating python script session."
		screen -XS $session quit
		UOI
		echo "Finished updating the script."
		screen -dmS $session python3 app.py
		echo "Script is now running in session \'sensorInput\'."
	else
		echo "No differences found, no action taken."
		screen -list 2>/dev/null | grep -q $session
		if [ $? != 0 ]; then
			echo "The script is not running, rebooting the script."
			screen -dmS $session python3 app.py
			echo "Script is now running in session \'sensorInput\'."
		fi
	fi
}

while true; do
	run &
	sleep 60m
done
