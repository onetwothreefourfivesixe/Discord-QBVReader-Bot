# Use an official Python runtime as a parent image based on Alpine
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install system dependencies, including ffmpeg and necessary development tools
RUN apk add --no-cache \
    ffmpeg \
    espeak \
    build-base \
    python3-dev \
    libffi-dev \
    musl-dev

# Install Python packages and dependencies
RUN pip install --no-cache-dir setuptools \
    numpy==1.25.0 \
    aeneas==1.7.3

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run main.py when the container launches
CMD ["python", "main.py"]