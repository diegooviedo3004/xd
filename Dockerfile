# Use Python 3.9 slim as the base image for a smaller footprint
FROM python:3.9-slim

# Install ffmpeg (includes ffprobe)
RUN apt-get update && apt-get install -y ffmpeg

# Copy all project files into the container
COPY . /app

# Set the working directory
WORKDIR /app

# Install Python dependencies from requirements.txt
RUN pip install -r requirements.txt

# Expose port 5000 for the Flask app
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
