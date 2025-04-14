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
        paddleocr && \
        python3 -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='en', rec_algorithm='CRNN', det_db_box_thresh=0.5)" \
        pdf2image \
        fuzzywuzzy \
        pandas \
        pillow \
        tabula-py \
        fastapi \
        uvicorn \
        python-multipart \
        python-dotenv \
        paramiko

# Copy project files
COPY . .

RUN echo "source /app/ppenv/bin/activate" >> /root/.bashrc
#RUN "uvicorn main_api:app --port 8888"
# Default command to run the FastAPI app
CMD ["/app/ppenv/bin/uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8888", "--log-level", "info"]
CMD ["tail", "-f", "/dev/null"]
