# Serverless-Face-Recognition-System

## Project Overview
This project is a scalable, serverless cloud application for face recognition, leveraging Amazon Web Services (AWS) to build an efficient, event-driven pipeline. The system processes video uploads, splits them into frames, and performs face recognition using a pre-trained deep learning model. The architecture ensures that the application scales seamlessly and handles input concurrently without server management.

### Key Features
- **Serverless Architecture**: Uses AWS Lambda functions for processing video frames and running face recognition.
- **Automated Trigger**: S3 event triggers to automatically start processing when a video is uploaded.
- **Deep Learning Model**: Integrates a pre-trained ResNet-34 model for face recognition, using PyTorch for inference.
- **Data Storage**: Utilizes Amazon S3 buckets for storing input videos, processed frames, and recognition results.
- **Efficient Processing**: The system processes frames using FFmpeg and detects faces using OpenCV.

### Components
- **Video Splitting Function**:
  - `lambda_video_splitting.py` is an AWS Lambda function triggered by new video uploads. It splits videos into frames using FFmpeg and stores them in an intermediate S3 bucket. **(Placed in `video-splitting/`)**
- **Face Recognition Function**:
  - `lambda_face_recognition.py` is a Lambda function that processes frames from the stage-1 S3 bucket, detects faces using OpenCV, and recognizes them using a ResNet-34 model. It outputs the recognized names to a text file stored in the output bucket. **(Placed in `face-recognition/`)**
- **Supporting Files**:
  - `face_recognition_Dockerfile`: Docker configuration for the face-recognition Lambda deployment. **(Placed in `face-recognition/`)**
  - `face_recognition_requirements.txt`: Lists Python packages required for the face-recognition function, including `boto3`, `imutils`, `Pillow`, `opencv-python-headless`, and `facenet-pytorch`. **(Placed in `face-recognition/`)**