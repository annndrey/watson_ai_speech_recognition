#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import base64
import configparser
import json
import threading
import time
import datetime
import os
import pyaudio
import websocket
from websocket._abnf import ABNF
import logging
import pprint
pp = pprint.PrettyPrinter(indent=4)

if not os.path.exists("OUT"):
    os.makedirs("OUT")
logfile = os.path.abspath(os.path.join("OUT", datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S.txt")))
print(logfile)
#logger = logging.getLogger('messages')
#logger.setLevel(logging.INFO)
#handler = logging.FileHandler(logfile)
#logger.addHandler(handler)


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
FINALS = []
WORK = True
p = pyaudio.PyAudio()

def wait_to_stop():
    global WORK
    input("press enter to stop")
    WORK = False

def read_audio(ws, timeout, device):
    RATE = int(p.get_device_info_by_index(int(device))['defaultSampleRate'])
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=int(device)
                    )

    print("* recording")
    rec = timeout or RECORD_SECONDS

    while WORK:
        data = stream.read(CHUNK, exception_on_overflow = False)
        ws.send(data, ABNF.OPCODE_BINARY)
    
    stream.stop_stream()
    stream.close()

    print("* done recording")
    data = {"action": "stop"}
    ws.send(json.dumps(data).encode('utf8'))
    time.sleep(1)
    ws.close()
    p.terminate()


def on_message(self, msg):
    data = json.loads(msg)
    if "results" in data:
        print("results recieved")
        print('opening file')
        with open(logfile, 'a') as f:
            print("file opened")
            if 'speaker_labels' in data.keys():
                outline = "{0}-{1} Speaker {2}: {3}{4}".format(data['speaker_labels'][0]['from'], data['speaker_labels'][0]['to'], data['speaker_labels'][0]['speaker'], data['results'][0]['alternatives'][0]['transcript'], os.linesep)
                if outline not in FINALS:
                    FINALS.append(outline)
                    f.write(outline)
                    print(outline)
                    

def on_error(self, error):
    print(error)

def on_close(ws):

    print('*stopping')


def on_open(ws):
    args = ws.args
    data = {
        "action": "start",
        "content-type": "audio/l16;rate=%d" % RATE,
        #"continuous": True,
        "interim_results": True,
        "word_confidence": True,
        "timestamps": True,
        "max_alternatives": 3,
        "speaker_labels": True
    }

    ws.send(json.dumps(data).encode('utf8'))
    threading.Thread(target=read_audio,
                     args=(ws, args.timeout, args.device)).start()
    threading.Thread(target=wait_to_stop).start()

def get_auth():
    config = configparser.RawConfigParser()
    config.read('speech.cfg')
    user = config.get('auth', 'username')
    password = config.get('auth', 'password')
    return (user, password)


def parse_args():
    for i in range(0, p.get_device_count()):
        print(i, p.get_device_info_by_index(i)['name'])

    device_index = int(input('Device index: '))                                    


    parser = argparse.ArgumentParser(
        description='Transcribe Watson text in real time')
    parser.add_argument('-t', '--timeout', type=int, default=5)
    parser.add_argument('-d', '--device', default=device_index)
    parser.add_argument('-r', '--rate', default=p.get_device_info_by_index(device_index)['defaultSampleRate'])
    args = parser.parse_args()
    return args


def main():
    # Connect to websocket interfaces
    headers = {}
    userpass = ":".join(get_auth())
    headers["Authorization"] = "Basic " + base64.b64encode(
        userpass.encode()).decode()
    url = ("wss://stream.watsonplatform.net//speech-to-text/api/v1/recognize"
           "?model=en-US_BroadbandModel")

    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(url,
                                header=headers,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.args = parse_args()
    ws.run_forever()


if __name__ == "__main__":
    main()
