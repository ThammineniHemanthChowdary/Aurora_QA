# ---------------------------------------
# Aurora QA Service - Hugging Face Deployment
# Author: Hemanth Chowdary
# ---------------------------------------

# Use lightweight Python base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose port 7860 (Hugging Face expects this)
ENV PORT=7860
EXPOSE 7860

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
