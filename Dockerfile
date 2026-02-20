# Use a slim Python image to keep size down
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for building dlib and face_recognition
# cmake and build-essential are critical here
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Upgrade pip and build tools to avoid build issues
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies
# Using --no-cache-dir to save space
# This step compiles dlib, which is memory intensive
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the application
# Use the port environment variable required by Render
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
