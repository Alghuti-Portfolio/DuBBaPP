
from pathlib import Path


#!/usr/bin/env python
from google.cloud import storage 

#1- Point API to JSON file. 
storage_client= storage.Client.from_service_account_json(r"/Volumes/GoogleDrive/My Drive/Cloud_Downloads/ml030522-a4be5268534b.json")
bucket_name= "NEW_BUCKET_NAME"

#2- Create a new Bucket in Storage. 
bucket= storage_client.create_bucket("NEW_BUCKET_NAME")

print("Bucket Created")

#3- Upload the file named "1.mp3" file from "My Drive" to Google Storage as "Copy.mp3"   
bucket = storage_client.bucket("NEW_BUCKET_NAME")
blob= bucket.blob("UPLOAD_NAME")
blob.upload_from_filename("/source/location")

print("File Uploaded")

#4- Download the "copy.mp3" to the "Cloud_Downloads" desktop folder.
bucket = storage_client.bucket("NEW_BUCKET_NAME")
blob= bucket.blob("UPLOAD_NAME")
blob.download_to_filename(f"/download/to/+UPLOAD_NAME")

print("File Downloaded")