#!/usr/bin/env python
# -*- coding: utf-8 -*-

from watson_developer_cloud import SpeechToTextV1
from os.path import join, dirname, abspath, splitext
import json
import glob
import os 
import pprint

pp = pprint.PrettyPrinter(indent=4)
# get your own credentials

settings = {
    "url": "https://stream.watsonplatform.net/speech-to-text/api",
    "username": "username",
    "password": "password"
    }

speech_to_text = SpeechToTextV1(
    username=settings['username'],
    password=settings['password']
    )

INPUT_DIR = 'IN'
OUT_DIR = 'OUT'
EXTENSION = "*.wav"

MIMETYPE = 'audio/%s' % EXTENSION.split('.')[1]
summaryfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_DIR, "summary.txt")

with open(summaryfile, 'w') as summary:
    for ind, file in enumerate(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), INPUT_DIR, EXTENSION))):
        with open(file, 'rb') as audio_file:
            print("Processing " + file)
            fname = os.path.splitext(os.path.basename(file))[0]+".json"
            outfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_DIR, fname)
            speech_recognition_results = speech_to_text.recognize(
                audio=audio_file,
                content_type=MIMETYPE,
                speaker_labels = True
                )
            # pp.pprint(speech_recognition_results['results'])
            timestamps = [y for x in speech_recognition_results['results'] for y in x['alternatives'][0]['timestamps']]

            speakers = {}
            for s in speech_recognition_results['speaker_labels']:
                speakers[s['from']] = "Speaker %s" % s['speaker']


            summary.write("{fname}: {sep}".format(fname=os.path.basename(file), sep=os.linesep))

            phrases = []

            for t in timestamps:
                current_speaker = speakers[t[1]]
                word = t[0]
                phrases.append([current_speaker, word])
            
            previous_speaker = None

            for p in phrases:
                if p[0] != previous_speaker:
                    summary.write(os.linesep)
                    summary.write("{speaker}: {phrase} ".format(speaker=p[0], phrase=p[1]))
                    previous_speaker = p[0]
                else:
                    summary.write(" {phrase}".format(phrase=p[1]))

            

            linesep = os.linesep
            text = linesep.join([s['transcript'] for s in speech_recognition_results['results'][0]['alternatives']])
            
            summary.write("{text}{sep}".format(text=text, sep=os.linesep))
            summary.write("*"*80+os.linesep)
            with open(outfile, 'w') as outf:
                json.dump(speech_recognition_results,  outf, indent=4, sort_keys=True)
                
