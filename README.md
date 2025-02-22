# Face-Recognition-System

## Project Overview

This repository contains two implementations of a cloud-based face recognition system:

Scalable Face Recognition System - A multi-tier architecture leveraging AWS EC2, S3, and SQS for scalable inference.

Serverless Face Recognition System - A fully serverless solution using AWS Lambda, S3, OpenCV, and PyTorch for event-driven face recognition.

Each implementation is designed to process image/video inputs and perform face recognition efficiently based on different cloud architectures.

## 1. Scalable Face Recognition System

### Description

A multi-tier cloud application for face recognition that dynamically scales using EC2 instances.

### Key Features

- Multi-Tier Architecture: Separates web, app, and data tiers for better modularity and scalability.

- Auto-Scaling: Dynamically scales up to 20 EC2 instances based on request volume.

- Deep Learning Model: Uses PyTorch for face recognition inference.

- Persistent Storage: Stores input images and recognition results in S3 buckets.

- Web Interaction: Web API using Flask to handle incoming image processing requests.

### Components

- Web Tier (`web_tier.py`): Handles incoming HTTP requests, manages SQS queues, and auto-scales EC2 instances.

- App Tier (`app_tier.py` & `face_recognition.py`): Runs on EC2 instances to process images using a PyTorch-based model.

- Data Tier: Uses S3 for storing input images and recognition results.

For detailed setup and usage, refer to `scalable/README.md`.

## 2. Serverless Face Recognition System

### Description

A serverless architecture for face recognition that processes video uploads and extracts faces using AWS Lambda.

### Key Features

- Fully Serverless: Uses AWS Lambda functions to process video frames and perform face recognition.

- Event-Driven Processing: Automatically triggers when a video is uploaded to an S3 bucket.

- Deep Learning Model: Uses a ResNet-34 model with PyTorch for face recognition.

- Efficient Video Processing: Splits videos into frames using FFmpeg and detects faces with OpenCV.

### Components

- Video Splitting Function (`lambda_video_splitting.py`): AWS Lambda function that splits videos into frames.

- Face Recognition Function (`lambda_face_recognition.py`): AWS Lambda function that processes frames and identifies faces.

### Supporting Files:

- `face_recognition_Dockerfile`: Docker config for deploying face recognition Lambda function.

- `face_recognition_requirements.txt`: Required Python packages.

For detailed setup and usage, refer to `serverless/README.md`.