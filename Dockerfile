# Use official Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (Docker caches this layer — faster rebuilds)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Create pdf directory if it doesn't exist
RUN mkdir -p pdf

# Expose Flask port
EXPOSE 3000

# Set project root on the path so all module imports resolve correctly
ENV PYTHONPATH=/app

# Run the app
CMD ["python", "app/Elucidate.py"]