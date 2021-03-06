#!/usr/bin/env python
# -*- coding: utf-8 -*-


import asyncio
import websockets
import json
import requests
import pyaudio
import time
import audioop
import sys

# Variables to use for recording audio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 16000

p = pyaudio.PyAudio()

# This is the language model to use to transcribe the audio
model = "en-US_BroadbandModel"

# These are the urls we will be using to communicate with Watson
default_url = "https://stream.watsonplatform.net/speech-to-text/api"
token_url = "https://stream.watsonplatform.net/authorization/api/v1/token?" \
            "url=https://stream.watsonplatform.net/speech-to-text/api"
url = "wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize?model=en-US_BroadbandModel"

# BlueMix app credentials
username = "176eb11cccd-d2f3378e3bd3"   # Your Bluemix App username
password = "wuTof2Xh1"   # Your Bluemix App password

# Send a request to get an authorization key
r = requests.get(token_url, auth=(username, password))
auth_token = r.text
print("Token", auth_token)
token_header = {"X-Watson-Authorization-Token": auth_token}

# Params to use for Watson API
params = {
    "word_confidence": True,
    "content_type": "audio/l16;rate=16000;channels=2",
    "action": "start",
    "interim_results": True
}

# Opens the stream to start recording from the default microphone
for i in range(0, p.get_device_count()):
    print(i, p.get_device_info_by_index(i))

device_index = int(input('Device index: '))                                    

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK,
                input_device_index=device_index
                )



async def send_audio(ws):
    # Starts recording of microphone
    print("* READY *")
    a_list = []
    start = time.time()
    while True:
        try:
            data = stream.read(CHUNK, exception_on_overflow = False)
            await ws.send(data)
        except KeyboardInterrupt:
            print("stopping")
            await ws.send(json.dumps({'action': 'stop'}))
            return False

    # Stop the stream and terminate the recording
    stream.stop_stream()
    stream.close()
    p.terminate()


async def speech_to_text():
    async with websockets.connect(url, extra_headers=token_header) as conn:
        # Send request to watson and waits for the listening response
        send = await conn.send(json.dumps(params))
        rec = await conn.recv()
        print(rec)
        asyncio.ensure_future(send_audio(conn))

        # Keeps receiving transcript until we have the final transcript
        while True:
            try:
                rec = await conn.recv()
                parsed = json.loads(rec)
                if len(parsed["results"]) > 0:
                    transcript = parsed["results"][0]["alternatives"][0]["transcript"]
                    print(transcript)
                    # print(parsed)
                    if "results" in parsed:
                        if len(parsed["results"]) > 0:
                            if "final" in parsed["results"][0]:
                                if parsed["results"][0]["final"]:
                                    # conn.close()
                                    # return False
                                    pass
                else:
                    print(parsed)
            except KeyError:
                conn.close()
                return False

# Starts the application loop
loop = asyncio.get_event_loop()
loop.run_until_complete(speech_to_text())
loop.close()
