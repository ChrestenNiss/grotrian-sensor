import subprocess,time,signal

starttime = time.time()
while True:
    process = subprocess.Popen("install.sh")
    time.sleep(3600.0 - ((time.time() - starttime) % 3600.0))
    process.send_signal(signal.SIGNINT)

