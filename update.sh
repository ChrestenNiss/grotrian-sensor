function UOI () {
	git clone https://github.com/AlexanderADM/grotrian-sensor.git
	shopt -s dotglob
	mv -u grotrian-sensor/* ./
	rm -fr grotrian-sensor
	git pull --force
	git checkout .
	pip3 install -r requirements.txt
}

function run () {
	if [ ! -f "app.py" ]; then
		echo "Python app not found, running update/install function."
		sudo apt install tmux
		UOI
		tmux new -d -s sensorInput 'python3 app.py'
	elif [[ "$(git status --porcelain --untracked-files=no)" ]]; then
		echo "Differences from main branch found, updating script."
		tmux kill-session -t sensorInput
		UOI
		tmux new -d -s sensorInput 'python3 app.py'
	else
		echo "No differences found, no action taken."
	fi
}

while true; do run & sleep 60; done
