# AudioSegment can be used in place of Pydub

import os
from os import path
from urllib import response
import fire
from dotenv import load_dotenv
from pydub import AudioSegment
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech 
from google.cloud import translate_v2 as translate
from google.cloud import storage
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip, TextClip
#from vid_wav import inFile
#from translate_basicCode import tranlation
import json
import requests
import tempfile
import shutil
import ffmpeg
import time
import sys
import uuid

from pydub import AudioSegment
import html
import moviepy.editor as mp
import speech_recognition as sr


os.environ['GOOGLE_APPLICATION_CREDENTIALS']=""


# Insert Local Video File Path
inFile = mp.VideoFileClip("/Users/RiceUniversityFinTech./Desktop/DUBB/VideoFileClip.mp4")

# Insert Local Audio File Path
inFile.audio.write_audiofile("/Users/RiceUniversityFinTech./Desktop/DUBB/test2.wav")


# initialize the recognizer
r = sr.Recognizer()

# open the file
with sr.AudioFile("/Users/RiceUniversityFinTech./Desktop/DUBB/test2.wav") as outFile:
    # listen for the data (load audio to memory)
    audio_data = r.record(outFile)
    # recognize (convert from speech to text)
    text = r.recognize_google(audio_data, language = "ar-PS")
    #translatedText = translate(text)
    #print(translatedText)
with open("text", "w") as json_file:
    json.dump(text, json_file)

##############
