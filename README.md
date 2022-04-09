# DuBBaPP
CapStone Project @ Rice University's FinTech Program

This project uses Google Cloud Services. Pydub library is used to pull the audio from the 
video clip below and saves it as a wav. The app also uploads the audio file in a tmp folder (see below) so that it can be used with the text-to-speech api - named speech-to-text client. 

**Screen Shot of tmp folder created in Google Cloud Storage**
![Screen Shot 2022-04-08 at 1 19 36 PM](https://user-images.githubusercontent.com/103196346/162516521-ef77684e-b8f3-4f27-8ba5-91b57512e13a.png)

![Screen Shot 2022-04-08 at 1 20 15 PM](https://user-images.githubusercontent.com/103196346/162516562-099e3295-6d4b-4e36-8526-583cfc949e26.png)

**The video clip has been pull from a Turkish Series Called "Magnificent Century", and limited to 1:30 for this project.**  

https://user-images.githubusercontent.com/103196346/162507951-9334ea59-e973-4355-913c-5ceb2ba248e6.mp4


After completing the setup requirments below, you should be able to run:

        python dubber.py videoFile.mp4 outputDirectory "ar" --targetLangs '["en", "tr"]'

to produce a new movie file dubbed in the languages specified in `targetLang`. 


## Installation Guide

A. Create a new Google Cloud Project.

B. Enable these Google Cloud APIs:

- Cloud Storage
- Speech-to-Text
- Text-to-Speech
- Translation


## Technologies and Libraries

> Python,
> HTML,
> JSON,
> Pandas,
> Fire,
> AudioSegment,
> Moviepy,
> Pydub,
> Google-Speech-to-Text-API,
> Google-Translte-API,
> Google-Text-to-Speech,
> Google-Cloud-Storage,
> TensorFlow 

---

**Below are the steps that will be implemented:** 

**Step 1:** Pull the audio out of the video, then use the #speech-to-text api to transcribe them.  

**Step 2:** Translate the transcripts using the #translation api into desired language. 

**Step 3:** Speak the translated transcripts using the #text-to-speech api.  

**Step 4:** Enable above mentioned Google cloud api’s  

**Step 5:** install Pydub Library in order to extract audio from video and save it as a wav  

**Step 6:**
- Upload file into cloud to be used in the speech-to-text api  
- Call the cloud - Speech to Text Client 

**Step 7:** Configure API & Specify the language code - which is what language you are transcribing from.  
- Enable automatic punctuation 
- Enable word time off sets give the exact word and time the speaker said them 
- Diarization_config tells the API to filters out noise or multiple speakers  
- See output transcript json() file

**Example of what that looks like**
![Screen Shot 2022-04-08 at 3 08 35 PM](https://user-images.githubusercontent.com/103196346/162519496-d318e9a6-4c55-4e01-99ff-ec404e49b7a5.png)

**Enhanced Models** using neural network Ai program **NOTE:** the data extracted from this sample is not large enough for use in a Linear Regression or any ML model used to enhance translation.  

**Step 8:** Feeding Translation Api 
- chunk the transcript output to feed it into the translation api 
- Identify variables related to sentence structure  
- Check for gaps for when speaker started and stopped speaking  
![Screen Shot 2022-04-08 at 2 46 02 PM](https://user-images.githubusercontent.com/103196346/162516308-686f355a-45d1-46c9-92dd-0e30adc4af27.png)

**Step 9:** Call Translation Api   


**Step 10:** Call speech-to-text to speak translated words  
- Configure api to use different computer voices and speaking rate to speed up or slow down to match the rate of the speaker in the video.   

**Step 11:** Correct Error 
**Common Error’s** 
- Speech-to-text api can make a mistake in the translation  
- Translation from translation api may be inaccurate  

**Step 12:**
- Develop a Custom Dictionary/ Glossary for correcting Errors  
- Increase accuracy of speech to text by using feature called “phrasehints” 
- Specify words or phrases that are more likely to appear in the video - especially for uncommon words or proper nouns.  
- Develop glossary.csv to specify the way we want certain terms or phrases to be translated #spotfixes. This will enable for the api to better recognize the words.





