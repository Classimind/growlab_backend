FROM python:3.10-slim

# Set working directory
WORKDIR /growlab

# Copy requirements
COPY requirements .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy project files
COPY . .

# Expose port
EXPOSE 8989

# Command to run FastAPI with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8989", "--reload"]
