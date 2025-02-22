import boto3
import os
import math
import json
import subprocess

s3Client = boto3.client('s3')
lambdaClient = boto3.client('lambda')

inputBucket = '<Input Bucket Name>'
stage1Bucket = '<Stage 1 Bucket Name>'

def processVideo(event):
    try:
        fileKey = event['Records'][0]['s3']['object']['key']
        tempFilePath = f'/tmp/{os.path.basename(fileKey)}'
        s3Client.download_file(inputBucket, fileKey, tempFilePath)
        outfile = video_splitting_cmdline(tempFilePath)
        uploadFrameToS3(outfile)
        invokeFaceRecognitionFunction(outfile)
    except Exception as e:
        print(f'Error downloading files: {e}')

def video_splitting_cmdline(videoFilename):
    filename = os.path.basename(videoFilename)
    outfile = os.path.splitext(filename)[0] + ".jpg"

    split_cmd = '/opt/ffmpeg -i ' + videoFilename + ' -vframes 1 ' + '/tmp/' + outfile
    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = '/opt/ffmpeg -i ' + videoFilename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    print(outfile)
    return outfile

def uploadFrameToS3(frame):
    framePath = '/tmp/' + frame
    try:
        s3Client.upload_file(framePath, stage1Bucket, frame)
        print(f'Uploaded {frame} to Stage-1 Bucket')
    except Exception as e:
        print(f'Error uploading {frame}: {e}')
        
def invokeFaceRecognitionFunction(fileName):
    lambdaClient.invoke(FunctionName="face-recognition", InvocationType='Event', Payload=json.dumps({'bucket_name':stage1Bucket, 'image_file_name':fileName}))

def lambda_handler(event, context):
    processVideo(event)