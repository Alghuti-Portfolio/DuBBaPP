
from pydub import AudioSegment
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
from google.cloud import storage
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip, TextClip
import os
import shutil
import ffmpeg
import time
import json
import sys
import tempfile
import uuid
from dotenv import load_dotenv
import fire
import html

# Load config in .env file
load_dotenv()


def decode_audio(inFile, outFile):
    """Converts a video file to a wav file.

    Args:
        inFile (String): i.e. my/great/movie.mp4
        outFile (String): i.e. my/great/movie.wav
    """
    if not outFile[-4:] != "wav":
        outFile += ".wav"
    AudioSegment.from_file(inFile).set_channels(
        1).export(outFile, format="wav")


def get_transcripts_json(gcsPath, langCode= "ar", phraseHints=[], speakerCount=1, enhancedModel=None):
    """Transcribes audio files.

    Args:
        gcsPath (String): path to file in cloud storage (i.e. "gs://audio/clip.mp4")
        langCode (String): language code (i.e. "en-US", see https://cloud.google.com/speech-to-text/docs/languages)
        phraseHints (String[]): list of words that are unusual but likely to appear in the audio file.
        speakerCount (int, optional): Number of speakers in the audio. Only works on English. Defaults to None.
        enhancedModel (String, optional): Option to use an enhanced speech model, i.e. "video"

    Returns:
        list | Operation.error
    """

    # Helper function for simplifying Google speech client response
    def _jsonify(result):
        json = []
        for section in result.results:
            data = {
                "transcript": section.alternatives[0].transcript,
                "words": []
            }
            for word in section.alternatives[0].words:
                data["words"].append({
                    "word": word.word,
                    "start_time": word.start_time.total_seconds(),
                    "end_time": word.end_time.total_seconds(),
                    "speaker_tag": word.speaker_tag
                })
            json.append(data)
        return json

    #client = speech.SpeechClient()  

    client= speech.SpeechClient.from_service_account_json(r"/Users/RiceUniversityFinTech./Downloads/file.json")
    audio = speech.RecognitionAudio(uri=gcsPath)

    diarize = speakerCount if speakerCount > 1 else False
    print(f"Diarizing: {diarize}")
    diarizationConfig = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=speakerCount if speakerCount > 1 else False,
    )

    # In English only, we can use the optimized video model
    if langCode == "en":
        enhancedModel = "video"

    config = speech.RecognitionConfig(
        language_code="ar-PS" if langCode == "en" else langCode,
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,
        speech_contexts=[{
            "phrases": phraseHints,
            "boost": 15
        }],
        diarization_config=diarizationConfig,
        profanity_filter=True,
        use_enhanced=True if enhancedModel else False,
        model="video" if enhancedModel else None

    )
    res = client.long_running_recognize(config=config, audio=audio).result()

    return _jsonify(res)

def parse_sentence_with_speaker(json, lang):
    """Takes json from get_transcripts_json and breaks it into sentences
    spoken by a single person. Sentences deliniated by a >= 1 second pause/

    Args:
        json (string[]): [{"transcript": "lalala", "words": [{"word": "la", "start_time": 20, "end_time": 21, "speaker_tag: 2}]}]
        lang (string): language code, i.e. "en"
    Returns:
        string[]: [{"sentence": "lalala", "speaker": 1, "start_time": 20, "end_time": 21}]
    """

    # Special case for parsing japanese words
    def get_word(word, lang):
        if lang == "ar":
            return word.split('|')[0]
        return word

    sentences = []
    sentence = {}
    for result in json:
        for i, word in enumerate(result['words']):
            wordText = get_word(word['word'], lang)
            if not sentence:
                sentence = {
                    lang: [wordText],
                    'speaker': word['speaker_tag'],
                    'start_time': word['start_time'],
                    'end_time': word['end_time']
                }
            # If we have a new speaker, save the sentence and create a new one:
            elif word['speaker_tag'] != sentence['speaker']:
                sentence[lang] = ' '.join(sentence[lang])
                sentences.append(sentence)
                sentence = {
                    lang: [wordText],
                    'speaker': word['speaker_tag'],
                    'start_time': word['start_time'],
                    'end_time': word['end_time']
                }
            else:
                sentence[lang].append(wordText)
                sentence['end_time'] = word['end_time']

            # If there's greater than one second gap, assume this is a new sentence
            if i+1 < len(result['words']) and word['end_time'] < result['words'][i+1]['start_time']:
                sentence[lang] = ' '.join(sentence[lang])
                sentences.append(sentence)
                sentence = {}
        if sentence:
            sentence[lang] = ' '.join(sentence[lang])
            sentences.append(sentence)
            sentence = {}

    return sentences


def translate_text(input, targetLang= "en", sourceLang=None):
    """Translates from sourceLang to targetLang. If sourceLang is empty,
    it will be auto-detected.

    Args:
        sentence (String): Sentence to translate
        targetLang (String): i.e. "en"
        sourceLang (String, optional): i.e. "es" Defaults to None.

    Returns:
        String: translated text
    """

    translate_client = translate.Client.from_service_account_json(r"/Users/RiceUniversityFinTech./Downloads/ml030522-ec029d5d1a65.json")
    result = translate_client.translate(
        input, target_language=targetLang, source_language=sourceLang)

    return html.unescape(result['translatedText'])


def speak(text, languageCode= "en", voiceName=None, speakingRate=1):
    """Converts text to audio

    Args:
        text (String): Text to be spoken
        languageCode (String): Language (i.e. "en")
        voiceName: (String, optional): See https://cloud.google.com/text-to-speech/docs/voices
        speakingRate: (int, optional): speed up or slow down speaking
    Returns:
        bytes : Audio in wav format
    """

    # Instantiates a client
    client = texttospeech.TextToSpeechClient.from_service_account_json(r"/Users/RiceUniversityFinTech./Downloads/ml030522-1a8ff2f42945.json")
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    if not voiceName:
        voice = texttospeech.VoiceSelectionParams(
            language_code=languageCode, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
    else:
        voice = texttospeech.VoiceSelectionParams(
            language_code=languageCode, name=voiceName
        )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speakingRate
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content


def speakUnderDuration(text, languageCode, durationSecs, voiceName=None):
    """Speak text within a certain time limit.
    If audio already fits within duratinSecs, no changes will be made.

    Args:
        text (String): Text to be spoken
        languageCode (String): language code, i.e. "en"
        durationSecs (int): Time limit in seconds
        voiceName (String, optional): See https://cloud.google.com/text-to-speech/docs/voices

    Returns:
        bytes : Audio in wav format
    """
    baseAudio = speak(text, languageCode, voiceName=voiceName)
    assert len(baseAudio)
    f = tempfile.NamedTemporaryFile(mode="w+b")
    f.write(baseAudio)
    f.flush()
    baseDuration = AudioSegment.from_mp3(f.name).duration_seconds
    f.close()
    ratio = baseDuration / durationSecs

    # if the audio fits, return it
    if ratio <= 1:
        return baseAudio

    # If the base audio is too long to fit in the segment...

    # round to one decimal point and go a little faster to be safe,
    ratio = round(ratio, 1)
    if ratio > 4:
        ratio = 4
    return speak(text, languageCode, voiceName=voiceName, speakingRate=ratio)


def toSrt(transcripts, charsPerLine=60):
    """Converts transcripts to SRT an SRT file. Only intended to work
    with English.

    Args:
        transcripts ({}): Transcripts returned from Speech API
        charsPerLine (int): max number of chars to write per line

    Returns:
        String srt data
    """

    """
    SRT files have this format:

    [Section of subtitles number]

    [Time the subtitle is displayed begins] –> [Time the subtitle is displayed ends]

    [Subtitle]

    Timestamps are in the format:

    [hours]: [minutes]: [seconds], [milliseconds]

    Note: about 60 characters comfortably fit on one line
    for resolution 1920x1080 with font size 40 pt.
    """

    def _srtTime(seconds):
        millisecs = seconds * 1000
        seconds, millisecs = divmod(millisecs, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "%d:%d:%d,%d" % (hours, minutes, seconds, millisecs)

    def _toSrt(words, startTime, endTime, index):
        return f"{index}\n" + _srtTime(startTime) + " --> " + _srtTime(endTime) + f"\n{words}"

    startTime = None
    sentence = ""
    srt = []
    index = 1
    for word in [word for x in transcripts for word in x['words']]:
        if not startTime:
            startTime = word['start_time']

        sentence += " " + word['word']

        if len(sentence) > charsPerLine:
            srt.append(_toSrt(sentence, startTime, word['end_time'], index))
            index += 1
            sentence = ""
            startTime = None

    if len(sentence):
        srt.append(_toSrt(sentence, startTime, word['end_time'], index))

    return '\n\n'.join(srt)


def stitch_audio(sentences, audioDir, movieFile, outFile, srtPath=None, overlayGain=-30):
    """Combines sentences, audio clips, and video file into the ultimate dubbed video

    Args:
        sentences (list): Output of parse_sentence_with_speaker
        audioDir (String): Directory containing generated audio files to stitch together
        movieFile (String): Path to movie file to dub.
        outFile (String): Where to write dubbed movie.
        srtPath (String, optional): Path to transcript/srt file, if desired.
        overlayGain (int, optional): How quiet to make source audio when overlaying dubs. 
            Defaults to -30.

    Returns:
       void : Writes movie file to outFile path
    """

    # Files in the audioDir should be labeled 0.wav, 1.wav, etc.
    audioFiles = os.listdir(audioDir)
    audioFiles.sort(key=lambda x: int(x.split('.')[0]))

    # Grab the computer-generated audio file
    segments = [AudioSegment.from_mp3(
        os.path.join(audioDir, x)) for x in audioFiles]
    # Also, grab the original audio
    dubbed = AudioSegment.from_file(movieFile)

    # Place each computer-generated audio at the correct timestamp
    for sentence, segment in zip(sentences, segments):
        dubbed = dubbed.overlay(
            segment, position=sentence['start_time'] * 1000, gain_during_overlay=overlayGain)
    # Write the final audio to a temporary output file
    audioFile = tempfile.NamedTemporaryFile()
    dubbed.export(audioFile)
    audioFile.flush()

    # Add the new audio to the video and save it
    clip = VideoFileClip(movieFile)
    audio = AudioFileClip(audioFile.name)
    clip = clip.set_audio(audio)

    # Add transcripts, if supplied
    if srtPath:
        width, height = clip.size[0] * 0.75, clip.size[1] * 0.20
        def generator(txt): return TextClip(txt, font='Georgia-Regular',
                                            size=[width, height], color='black', method="caption")
        subtitles = SubtitlesClip(
            srtPath, generator).set_pos(("center", "bottom"))
        clip = CompositeVideoClip([clip, subtitles])

    clip.write_videofile(outFile, codec='libx264', audio_codec='aac')
    audioFile.close()

