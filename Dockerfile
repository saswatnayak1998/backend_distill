# Use an x86-64 base image (forces emulation on ARM machines)
FROM --platform=linux/amd64 python:3.10-slim-buster

WORKDIR /backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libssl-dev \
    python3-dev \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# ✅ Install the latest CMake manually
RUN curl -fsSL https://github.com/Kitware/CMake/releases/download/v3.27.7/cmake-3.27.7-linux-x86_64.tar.gz | tar -xzC /usr/local --strip-components=1

# ✅ Install Rust and set up environment for x86-64
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN rustup target add x86_64-unknown-linux-gnu
RUN rustup install stable && rustup default stable

# Verify Rust installation
RUN rustc --version && cargo --version

# ✅ Remove Docker dependencies (DO NOT install Docker inside Cloud Run)
# ENV DOCKER_HOST="unix:///var/run/docker.sock"

# ✅ Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# ✅ Copy application code
COPY . .

# ✅ Cloud Run requires listening on PORT
EXPOSE 8080
ENV PORT=8080

CMD ["python3", "main.py"]
