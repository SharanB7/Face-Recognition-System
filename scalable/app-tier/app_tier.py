import boto3
import subprocess

# AWS credentials
awsAccessKeyId = '<AWS Access Key Id>'
awsSecretAccessKey = '<AWS Secret Access Key>'

# Queue URLs and bucket names
requestQueueUrl = 'https://sqs.us-east-1.amazonaws.com/<Request Queue URL>'
responseQueueUrl = 'https://sqs.us-east-1.amazonaws.com/<Response Queue URL>'
inputBucket = '<Input Bucket Name>'
outputBucket = '<Output Bucket Name>'

def uploadFileToS3(filePath, bucket, fileName):
    # Uploading a file to S3 bucket.
    s3Client.upload_file(filePath, bucket, fileName)

def putObjectInS3(key, bucket, body):
    # Uploading an object to S3 bucket.
    s3Client.put_object(Key = key, Bucket = bucket, Body = body)

def processImage(filePath):
    # Processing image using face recognition script.
    faceRecognition = subprocess.run(['python3', '/app_tier/face_recognition.py', filePath], capture_output = True, text = True)
    return faceRecognition.stdout

def sendMessageToSqs(queueUrl, messageBody):
    # Sending a message to SQS queue.
    sqsClient.send_message(QueueUrl = queueUrl, MessageBody = messageBody)

def deleteMessageFromSqs(queueUrl, receiptHandle):
    # Deleting a message from SQS queue.
    sqsClient.delete_message(QueueUrl = queueUrl, ReceiptHandle = receiptHandle)

def receiveMessagesFromSqs():
    # Receive messages from SQS and process them.
    while True:
        response = sqsClient.receive_message(
            QueueUrl=requestQueueUrl,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,
        )

        messages = response.get('Messages', [])
        for message in messages:
            fileName = message['Body']
            filePathSuffix = '0/' if len(fileName) == 12 else '/'
            filePath = f"/dataset/face_images_100{filePathSuffix}{fileName}"

            # Uploading file to input bucket
            uploadFileToS3(filePath, inputBucket, fileName)

            # Deleting message from request queue
            deleteMessageFromSqs(requestQueueUrl, message['ReceiptHandle'])
            
            # Processing the image
            result = processImage(filePath)

            # Uploading result to output bucket
            key = fileName.split('.')[0]
            putObjectInS3(key, outputBucket, result)

            # Storing result in response queue
            messageBody = f"{key}:{result}"
            sendMessageToSqs(responseQueueUrl, messageBody)

if __name__ == "__main__":
    # Creating S3 and SQS clients
    s3Client = boto3.client('s3', region_name = 'us-east-1', aws_access_key_id = awsAccessKeyId, aws_secret_access_key = awsSecretAccessKey)
    sqsClient = boto3.client('sqs', region_name = 'us-east-1', aws_access_key_id = awsAccessKeyId, aws_secret_access_key = awsSecretAccessKey)

    # Start receiving messages from SQS
    receiveMessagesFromSqs()
