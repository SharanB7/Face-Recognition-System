from flask import Flask, request
import pandas as pd
import boto3
import time
import threading

iaas = Flask(__name__)

# AWS Credentials
awsAccessKeyId = '<AWS Access Key Id>'
awsSecretAccessKey = '<AWS Secret Access Key>'

# Creating S3 and SQS clients
ec2Client = boto3.client('ec2', region_name = 'us-east-1', aws_access_key_id = awsAccessKeyId, aws_secret_access_key = awsSecretAccessKey)
sqsClient = boto3.client('sqs', region_name = 'us-east-1', aws_access_key_id = awsAccessKeyId, aws_secret_access_key = awsSecretAccessKey)

# Queue URLs
requestQueueUrl = 'https://sqs.us-east-1.amazonaws.com/<Request Queue URL>'
responseQueueUrl = 'https://sqs.us-east-1.amazonaws.com/<Response Queue URL>'

# Instance Configuration
appTierAmiId = '<App Tier AMI ID>'
instanceType = 't2.micro'
maxActiveInstances = 20
startupScript = """#!/bin/bash
    cd /app-tier/
    source py3/bin/activate
    python3 app_tier.py
    """

# Global Variables
requestCount = 0
responseCount = 0
images = {}
inProgress = True
terminateAutoScaleThread = False
terminateHandleResponsesThread = False
filters = [{'Name': 'instance-state-name', 'Values': ['running', 'pending']},
            {'Name': 'tag:face-recognition', 'Values': ['app-tier']}]

def sendMessageToSqs(queueUrl, messageBody):
    # Sending a message to SQS queue.
    sqsClient.send_message(QueueUrl = queueUrl, MessageBody = messageBody)

def waitForImage(images, filename):
    # Wait for the image to be processed.
    while filename not in images:
        time.sleep(1)

def faceRecognition():
    global requestCount, inProgress

    # Validate the presence of input image
    if 'inputFile' not in request.files:
        return 'File not provided', 400

    file = request.files['inputFile']

    # Update request queue
    requestCount += 1
    inProgress = True
    sendMessageToSqs(requestQueueUrl, file.filename)

    # Begin threads for auto scaling and handling responses
    autoScaling()
    handlingResponses()

    # Wait for image processing
    imageName = file.filename.split('.')[0]
    waitForImage(images, imageName)

    # Return the output after face recognition
    return f"{images[imageName]}"

@iaas.route("/", methods=["POST"])
def processImage():
    return faceRecognition()

def getQueueLength(queueUrl):
    # Fetching the number of messages in the given queue
    queueInfo = sqsClient.get_queue_attributes(
        QueueUrl = queueUrl,
        AttributeNames = ['ApproximateNumberOfMessages']
    )
    return int(queueInfo['Attributes']['ApproximateNumberOfMessages'])

def getActiveInstanceCount():
    # Fetching the number of App Tier instances in Running or Pending state
    global filters
    instanceInfo = ec2Client.describe_instances(Filters = filters)
    activeInstanceCount = sum(len(reservation['Instances']) for reservation in instanceInfo.get('Reservations', []))
    return activeInstanceCount

def scaleUpInstances(desiredCount, currentCount):
    # Scales up instances if the current count is less than desired count.
    global inProgress, appTierAmiId, instanceType, startupScript
    if inProgress:
        newInstancesCount = desiredCount - currentCount
        if newInstancesCount > 0:
            for _ in range(newInstancesCount):
                instanceName = f"app-tier-instance-{currentCount + 1}"
                ec2Client.run_instances(
                    ImageId = appTierAmiId,
                    MinCount = 1,
                    MaxCount = 1,
                    InstanceType = instanceType,
                    UserData = startupScript,
                    KeyName = 'my_key_pair',
                    TagSpecifications = [{'ResourceType': 'instance',
                                        'Tags': [{'Key': 'Name', 'Value': instanceName},
                                                 {'Key': 'face-recognition', 'Value': 'app-tier'}]}]
                )
                currentCount += 1

def scaleDownInstances(desiredCount, currentCount):
    # Scales down instances if the current count is more than desired count and all responses are processed.
    global responseCount, requestCount, terminateAutoScaleThread, terminateHandleResponsesThread, filters, inProgress
    if responseCount == requestCount:
        instances = ec2Client.describe_instances(Filters = filters, MaxResults = 100)
        sortedInstances = sorted(
            [(instance['InstanceId'], instance['Tags']) for reservation in instances.get('Reservations', [])
             for instance in reservation['Instances']],
            key = lambda x: [tag['Value'] for tag in x[1] if tag['Key'] == 'Name'][0]
        )
        excessInstances = [instanceId for instanceId, _ in sortedInstances[-(currentCount - desiredCount):]]
        if excessInstances:
            ec2Client.terminate_instances(InstanceIds = excessInstances)
        images.clear()
        time.sleep(10)
        inProgress = False
        terminateAutoScaleThread = True
        terminateHandleResponsesThread = True

def scalingInstances(desiredCount):
    # Scales instances based on desired count and current state.
    currentCount = getActiveInstanceCount()

    if currentCount < desiredCount:
        scaleUpInstances(desiredCount, currentCount)
    elif currentCount > desiredCount:
        scaleDownInstances(desiredCount, currentCount)

def autoScale():
    # Automatically scales instances based on queue length.
    global terminateAutoScaleThread, requestQueueUrl, maxActiveInstances
    while not terminateAutoScaleThread:
        queueLength = getQueueLength(requestQueueUrl)
        desiredInstances = min(maxActiveInstances, queueLength)
        scalingInstances(desiredInstances)
        time.sleep(3)

def handleResponses():
    # Handles responses from the response queue.
    global responseCount, terminateHandleResponsesThread, responseQueueUrl
    while not terminateHandleResponsesThread:
        response = sqsClient.receive_message(
            QueueUrl = responseQueueUrl,
            MaxNumberOfMessages = 1,
            WaitTimeSeconds = 1,
        )

        messages = response.get('Messages', [])
        for message in messages:
            modelResult = message['Body']
            responseCount += 1
            imageName = modelResult.split(':')[0]
            images[imageName] = modelResult
            sqsClient.delete_message(QueueUrl = responseQueueUrl, ReceiptHandle = message['ReceiptHandle'])

        time.sleep(1)

def autoScaling():
    # Starts the auto scaling thread if it's not already running.
    global terminateAutoScaleThread
    for thread in threading.enumerate():
        if thread.name == 'autoScaleThread' and thread.is_alive():
            return
        
    autoScaleThread = threading.Thread(name = 'autoScaleThread', target = autoScale)
    terminateAutoScaleThread = False
    autoScaleThread.start()

def handlingResponses():
    # Starts the response handling thread if it's not already running.
    global terminateHandleResponsesThread
    for thread in threading.enumerate():
        if thread.name == 'handleResponsesThread' and thread.is_alive():
            return

    responseThread = threading.Thread(name = 'handleResponsesThread', target = handleResponses)
    terminateHandleResponsesThread = False
    responseThread.start()

if __name__ == "__main__":
    iaas.run(host = '0.0.0.0', port = 8000, threaded = True)