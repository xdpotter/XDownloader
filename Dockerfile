# Dockerfile

# Use a lean official Python image
FROM python:3.11-slim

# Install dependencies needed for yt-dlp and FFmpeg for audio/video processing
# FFmpeg is CRITICAL for merging video/audio streams and MP3 conversion
RUN apt-get update && \
    apt-get install -y ffmpeg libssl-dev libffi-dev build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Expose the port Flask runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]