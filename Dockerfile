FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    sgp4 \
    numpy \
    matplotlib \
    plotly
    
# Install PyTorch separately from its official index (CPU version)
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Create output directory
RUN mkdir -p outputs

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
