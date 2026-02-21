# Use a full Python image for stability
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DLIB_NO_GUI_SUPPORT=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libgl1 \
    libglib2.0-0 \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and build tools
# Pin setuptools <71 because face_recognition_models uses `pkg_resources`
# which was removed from setuptools 71+
RUN pip install --no-cache-dir --upgrade pip "setuptools<71" wheel

# 1. Install dlib (This is the slow one, we cache it here)
RUN pip install --no-cache-dir dlib==19.24.6

# 2. Install face_recognition_models and face_recognition TOGETHER 
# This ensures the wrapper and its data are synced. 
# We use the exactly recommended git source for the models.
RUN pip install --no-cache-dir git+https://github.com/ageitgey/face_recognition_models && \
    pip install --no-cache-dir face_recognition

# 3. Copy requirements and install the rest
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
