import boto3
import os
import subprocess
import math
from face_recognition_code import face_recognition_function

s3Client = boto3.client('s3')

stage1Bucket = '<Stage 1 Bucket Name>'
outputBucket = '<Output Bucket Name>'
dataBucket = '<Data Bucket Name>'

def processPhoto(event):
    try:
        fileName = event['image_file_name']
        bucketName = event['bucket_name']
        tempFilePath = f'/tmp/{os.path.basename(fileName)}'
        s3Client.download_file(bucketName, fileName, tempFilePath)
        s3Client.download_file(dataBucket, 'data.pt', '/tmp/data.pt')
        result =  face_recognition_function(tempFilePath)
        if result:
            outputFile = f'{os.path.splitext(fileName)[0]}.txt'
            outputPath = f'/tmp/{outputFile}'
            try:
                s3Client.upload_file(outputPath, outputBucket, outputFile)
            except Exception as e:
                print(f'Error uploading files: {e}')
    except Exception as e:
        print(f'Error downloading files: {e}')

def handler(event, context):
    processPhoto(event)