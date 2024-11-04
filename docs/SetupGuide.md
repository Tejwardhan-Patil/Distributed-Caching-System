# Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.x, Java 11, and C++ compilers available
- Kubernetes and Terraform (optional for cloud deployment)

## Step-by-Step Instructions

1. **Clone the Repository**

   ```bash
   git clone https://github.com/repo.git
   cd distributed-cache
   ```

2. **Build the Components**

   - Build the C++ and Java components:
  
     ```bash
     ./scripts/Build.sh
     ```

3. **Run the System Locally**

   Using Docker Compose:

   ```bash
   docker-compose up
   ```

4. **Configure Environment Variables**

   Update `config.dev.yaml` for the development environment. Adjust settings for cache size, eviction policies, and network ports.

5. **Start Cache API**

   Run the Python-based API:

   ```bash
   python3 -m api.API
   ```
