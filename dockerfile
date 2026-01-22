FROM python:3.10-slim

# Set working directory
WORKDIR /growlab

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-venv \
        build-essential \
        wget \
        git \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv

# Activate venv and upgrade pip
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements .

# Install Python dependencies inside venv
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8989

# Command to run FastAPI with hot reload inside the venv
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8989", "--reload"]
