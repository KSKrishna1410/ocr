FROM python:3.10-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates

# Add your further install logic below (e.g., tesseract, pip packages, etc.)

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    build-essential \
    python3-dev \
    python3-venv \
    tesseract-ocr \
    poppler-utils \
    default-jre \
    curl \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /app/ppenv

# Install Python dependencies inside venv
RUN . /app/ppenv/bin/activate && \
    pip install --upgrade pip && \
#    pip install -r requirements.txt	
    pip install \
	paddlepaddle \
        paddleocr \
        pdf2image \
        fuzzywuzzy \
        pandas \
        pillow \
        tabula-py

# Copy project files
COPY . .

RUN echo "source /app/ppenv/bin/activate" >> /root/.bashrc
RUN uvicorn main_api:app

CMD ["tail", "-f", "/dev/null"]
