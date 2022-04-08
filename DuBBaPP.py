

#cxxxxxxxxx<ALGHUTI><HATEM><03><05><2022><><xxxxxxxxxxx>
#<XXXXXXXXXXXXXXDONTXXXTREADXXXONXXXMEXXXXXXXXXXXXXXXXX}>
#c><p><y><h><o><n><[P><Y><T>H<O><N]><p><y><h><o><n><><>>


#
#M
#W#
#EO#
#L#C#
#C##L#
#O###E#
#M####W#
import os
import sys
import json
import html
import fire
import uuid
import time
import shutil
import ffmpeg
import tempfile
import questionary
from pathlib import Path
from pydub import AudioSegment
from dotenv import load_dotenv
from google.cloud import storage
from google.cloud import texttospeech
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v2 as translate
from moviepy.video.tools.subtitles import SubtitlesClip, TextClip
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
#c>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#{XXKEYXXXXXLOADINGXXX[CONFIG]XXXINXXX[ENV]XXXXNOXXXPEEKINGXXXXXXXXXXXXXXX 
load_dotenv()
#cxxxxxxxxxxxx<STORAGE><BUCKET><POINT><API><JSON><FILE><xxxxxxxxxxxxxxxxxx
#c>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#IMPORT FROM ACTIONS

from actions.pipeline import (
    decode_audio,
    get_transcripts_json,
    parse_sentence_with_speaker,
    translate_text,
    speak,
    speakUnderDuration,
    toSrt,
    stitch_audio
)

import speech_recognition as sr
import moviepy.editor as mp

def main(
        outputDir= Path("/Volumes/GoogleDrive/My Drive/Cloud_Downloads/app/accounts/downLoad/audioDir/outputDir"),
        videoFile= Path(f"/Volumes/GoogleDrive/My Drive/Cloud_Downloads/app/accounts/upLoad/inFile/videoFile.mp4"), 
        #Path(f"/Volumes/GoogleDrive/My Drive/Cloud_Downloads/app/accounts/downLoad/audioDir/outputDir"), 
        srcLang= "ar-PS", targetLangs=[],
        storageBucket=None, phraseHints=[], dubSrc=False,
        speakerCount=1, voices="en-AU-Standard-A", srt=False,
        newDir=False, genAudio=True, noTranslate=False):
    """Translate and dub a movie.

    Args:
        videoFile (String): File to dub
        outputDir (String): Directory to write output files
        srcLang (String): Language code to translate from (i.e. "fi")
        targetLangs (list, optional): Languages to translate too, i.e. ["en", "fr"]
        storageBucket (String, optional): GCS bucket for temporary file storage. Defaults to None.
        phraseHints (list, optional): "Hints" for words likely to appear in audio. Defaults to [].
        dubSrc (bool, optional): Whether to generate dubs in the source language. Defaults to False.
        speakerCount (int, optional): How many speakers in the video. Defaults to 1.
        voices (dict, optional): Which voices to use for dubbing, i.e. {"en": "en-AU-Standard-A"}. Defaults to {}.
        srt (bool, optional): Path of SRT transcript file, if it exists. Defaults to False.
        newDir (bool, optional): Whether to start dubbing from scratch or use files in outputDir. Defaults to False.
        genAudio (bool, optional): Generate new audio, even if it's already been generated. Defaults to False.
        noTranslate (bool, optional): Don't translate. Defaults to False.

    Raises:
        void : Writes dubbed video and intermediate files to outputDir
    """

    baseName = os.path.split(videoFile)[-1].split('.')[0]
    if newDir:
        shutil.rmtree(outputDir)

    if not os.path.exists(outputDir):
        os.mkdir(outputDir)

    outputFiles = os.listdir(outputDir)

    if not f"{baseName}.wav" in outputFiles:
        print("Extracting audio from video")
        fn = os.path.join(outputDir, baseName + ".wav")
        decode_audio(videoFile, fn)
        print(f"Wrote {fn}")
            
        print("Transcribing audio")
        print("Uploading to the cloud...") 
        storage_client= storage.Client.from_service_account_json(r"/Volumes/GoogleDrive/My Drive/Cloud_Downloads/ml030522-a4be5268534b.json")
        
        #3- Upload the file named "1.mp3" file from "My Drive" to Google Storage as "Copy.mp3"   
        bucket = storage_client.bucket("ml-project-1")
        
        tmpFile = os.path.join("tmp", str(uuid.uuid4()) + ".wav")
        blob = bucket.blob(tmpFile)
        # Temporary upload audio file to the cloud
        blob.upload_from_filename(os.path.join(
            outputDir, baseName + ".wav"), content_type="audio/wav")    

        print("Transcribing...")
        transcripts = get_transcripts_json(os.path.join(
            "gs://", storageBucket, tmpFile), srcLang="ar-PS",
            phraseHints=phraseHints,
            speakerCount=speakerCount)
        json.dump(transcripts, open(os.path.join(
            outputDir, "transcript.json"), "w"))
        
        sentences = parse_sentence_with_speaker(transcripts, srcLang="ar-PS")
        fn = os.path.join(outputDir, baseName + ".json")
        with open(fn, "w") as f:
            json.dump(sentences, f)
        print(f"Wrote {fn}")
        print("Deleting cloud file...")
        blob.delete()
    srtPath = os.path.join(outputDir, "subtitles.srt") if srt else None
    if srt:
        transcripts = json.load(
            open(os.path.join(outputDir, "transcript.json")))
        subtitles = toSrt(transcripts)
        with open(srtPath, "w") as f:
            f.write(subtitles)
        print(
            f"Write srt subtitles to {os.path.join(outputDir, 'subtitles.srt')}")

    sentences = json.load(open(os.path.join(outputDir, baseName + ".json")))
    sentence = []

    if not noTranslate:
        for lang in targetLangs:
            print(f"Translating to {en}")
            for sentence in sentences:
                sentence[lang] = translate_text(
                    sentence[srcLang], lang, srcLang)

        # Write the translations to json
        fn = os.path.join(outputDir, baseName + ".json")
        with open(fn, "w") as f:
            json.dump(sentences, f)

    audioDir = os.path.join(outputDir, "audioClips")
    if not "audioClips" in outputFiles:
        os.mkdir(audioDir)
        
    #audioDir = Path("/Volumes/GoogleDrive/My Drive/Cloud_Downloads/app/accounts/downLoad/audioDir/outputDir/0.wav")    #os.path.join(outputDir, "audioClips")
    #if not "audioClips" in outputFiles:
    #    os.mkdir(audioDir)

    # whether or not to also dub the source language
    if dubSrc:
        targetLangs += [srcLang]

    for lang in targetLangs:
        languageDir = os.path.join(audioDir, lang)
        if os.path.exists(languageDir):
            if not genAudio:
                continue
            shutil.rmtree(languageDir)
        os.mkdir(languageDir)
        print(f"Synthesizing audio for {lang}")
        for i, sentence in enumerate(sentences):
            voiceName = voices[lang] if lang in voices else None
            audio = speakUnderDuration(
                sentence[lang], lang, sentence['end_time'] -
                sentence['start_time'],
                voiceName=voiceName)
            with open(os.path.join(languageDir, f"{i}.mp3"), 'wb') as f:
                f.write(audio)

    dubbedDir = os.path.join(outputDir, "dubbedVideos")

    if not "dubbedVideos" in outputFiles:
        os.mkdir(dubbedDir)

    for lang in targetLangs:
        lang= "en"
        print(f"Dubbing audio for {lang}")
        outFile = os.path.join(dubbedDir, lang + ".mp4")
        stitch_audio(sentences, os.path.join(
            audioDir, lang), videoFile, outFile, srtPath=srtPath)

    print("Done")

if __name__ == "__main__":
    fire.Fire(main)

