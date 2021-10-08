APP=/grotrian-sensor

if [ -d "$APP" ]
then
    cd grotrian-sensor
    git pull
else
    git clone https://github.com/AlexanderADM/grotrian-sensor.git
    cd grotrian-sensor
fi

pip3 install -r requirements.txt
python3 app.py