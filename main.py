#!/usr/bin/python
import time
import os
import random
import os
from creds import *
import requests
import json
import re
from memcache import Client
from subprocess import call



recorded = False
start_button_pin_value_file = '/sys/class/gpio/gpio409/value'
with open(start_button_pin_value_file, "r") as f:
	last_start_button_pin_value = f.read()
audio = ""


#Memcache Setup
servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)

def gettoken():
	token = mc.get("access_token")
	refresh = refresh_token
	if token:
		return token
	elif refresh:
		payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "refresh_token" : refresh, "grant_type" : "refresh_token", }
		url = "https://api.amazon.com/auth/o2/token"
		r = requests.post(url, data = payload)
		resp = json.loads(r.text)
		mc.set("access_token", resp['access_token'], 3570)
		return resp['access_token']
	else:
		return False

def alexa():
	url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
	headers = {'Authorization' : 'Bearer %s' % gettoken()}
	d = {
   		"messageHeader": {
       		"deviceContext": [
           		{
               		"name": "playbackState",
               		"namespace": "AudioPlayer",
               		"payload": {
                   		"streamId": "",
        			   	"offsetInMilliseconds": "0",
                   		"playerActivity": "IDLE"
               		}
           		}
       		]
		},
   		"messageBody": {
       		"profile": "alexa-close-talk",
       		"locale": "en-us",
       		"format": "audio/L16; rate=16000; channels=1"
   		}
	}
	with open('recording.wav') as inf:
		files = [
				('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
				('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
			]	
		r = requests.post(url, headers=headers, files=files)
	for v in r.headers:
		print(v + ": " + r.headers[v])
	boundary = ''
	for v in r.headers['Content-Type'].split(";"):
		if re.match('.*boundary.*', v):
			boundary =  v.split("=")[1]
	data = r.content.split(boundary)
	for d in data:
		if (len(d) >= 1024):
			audio = d.split('\r\n\r\n')[1].rstrip('--')
	with open("response.mp3", 'wb') as f:
		f.write(audio)
	call(['mpg123', '-q', '1sec.mp3', 'response.mp3'])


token = gettoken()
call(['mpg123', '-q', '1sec.mp3', 'hello.mp3'])
while True:
	with open(start_button_pin_value_file, "r") as f:
		start_button_pin_value = f.read().strip('\n')
	if start_button_pin_value != last_start_button_pin_value:
		last_start_button_pin_value = start_button_pin_value
		if start_button_pin_value == '1' and recorded == True:
			alexa()
		elif start_button_pin_value == '0':
			# Button is pressed, so record
			call(['play', 'beep.wav'])
			call(['rec', '--clobber', '-r', '16k', '-b', '16', '-c', '1', '-e', 'signed-integer', 'recording.wav', 'silence', '1', '0.2', '1%', '1', '2.2', '2%'])
			recorded = True
