# Use a slim Python image to keep size down
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Skip GUI components in dlib to speed up compile
ENV DLIB_NO_GUI_SUPPORT=1

# Install system dependencies required for building dlib
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

# Upgrade pip and build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install all dependencies EXCEPT dlib+face_recognition first (fast packages)
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    cloudinary \
    "pymongo[srv]" \
    python-dotenv \
    python-telegram-bot \
    pydantic-settings \
    pillow \
    numpy \
    requests \
    watchdog \
    pyftpdlib \
    python-multipart \
    httpx \
    certifi

# Install dlib last (this step compiles C++ and takes 20-30 minutes)
# Build with 4 parallel jobs to use all available CPUs
RUN pip install --no-cache-dir dlib face_recognition

# Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
