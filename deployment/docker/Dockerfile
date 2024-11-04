# Use a base image with Python, Java, and build tools for C++
FROM ubuntu:20.04

# Set environment variables to suppress prompts and install updates
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and tools (Python, Java, C++, Git)
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    openjdk-11-jdk \
    g++ \
    cmake \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files to the container
COPY . /app

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Build C++ components (CacheStorage and DistributedCache)
RUN mkdir -p build && cd build \
    && cmake .. \
    && make

# Set environment variables for Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Compile Java components
RUN javac -d /app/build $(find /app -name "*.java")

# Expose necessary ports (for API or services)
EXPOSE 8080 5000

# Define the default command to run the system
CMD ["python3", "/app/management/cache_api/API.py"]