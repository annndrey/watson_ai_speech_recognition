#!/usr/bin/env python
# -*- coding: utf-8 -*-


from ws4py.client.threadedclient import WebSocketClient
import base64, json, ssl, subprocess, threading, time
import requests
import audioop
import pyaudio

# before run install https://www.vb-audio.com/Cable/index.htm driver 
# http://software.muzychenko.net/eng/vac.htm audiorepeater
# start two audiorepeaters redirecting sound from mic and speakers 
# to virtual cable
# start script to record sound from virtual cable
# https://gist.github.com/mabdrabo/8678538

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

pa = pyaudio.PyAudio()

class SpeechToTextClient(WebSocketClient):
    def __init__(self):
        ws_url = "wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize?model=en-US_BroadbandModel"

        token_url = token_url = "https://stream.watsonplatform.net/authorization/api/v1/token?" \
            "url=https://stream.watsonplatform.net/speech-to-text/api"
        username = "176eb13"   # Your Bluemix App username
        password = "wuTof21"   # Your Bluemix App password
        r = requests.get(token_url, auth=(username, password))
        auth_token = r.text
        token_header = ("X-Watson-Authorization-Token", auth_token)


        self.listening = False

        try:
            WebSocketClient.__init__(self, ws_url,
                headers=[token_header,])
            self.connect()
        except: print("Failed to open WebSocket.")

    def opened(self):
        self.send('{"action": "start", "content-type": "audio/l16;rate=16000"}')
        self.stream_audio_thread = threading.Thread(target=self.stream_audio)
        self.stream_audio_thread.start()

    def received_message(self, message):
        message = json.loads(str(message))
        if "state" in message:
            if message["state"] == "listening":
                self.listening = True
        print("Message received: " + str(message))

    def stream_audio(self):
        while not self.listening:
            time.sleep(0.1)
        # reccmd = ["arecord", "-f", "S16_LE", "-r", "16000", "-t", "raw"]
        # p = subprocess.Popen(reccmd, stdout=subprocess.PIPE)
            
        # TODO > change to pyaudio
        #for i in range(0, pa.get_device_count()):
        #    print(i, pa.get_device_info_by_index(i)['name'])
        # device_index = int(input('Device index: '))                                    
        pa = pyaudio.PyAudio()
        device_index = 3
        stream = pa.open(format=FORMAT,                                                 
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=device_index)

        #
        #for i in range(0, pa.get_device_count()):
        #    print(i, pa.get_device_info_by_index(i)['name'])
        
        while self.listening:
            # replace with pyaudio read from Virtual Cable device
            # VB-Audio Point
            data  = stream.read(CHUNK, exception_on_overflow = False)                                                 
            #data = p.stdout.read(1024)
            try: 
                self.send(bytearray(data), binary=True)
                # print(audioop.max(data, 2))
            except ssl.SSLError: 
                print("Error")

        pa.terminate()
        #p.kill()

    def close(self):
        self.listening = False
        self.stream_audio_thread.join()
        WebSocketClient.close(self)

try:
    stt_client = SpeechToTextClient()
    input()
finally:
    stt_client.close()

