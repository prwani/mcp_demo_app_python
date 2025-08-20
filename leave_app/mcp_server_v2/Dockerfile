FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY startup.sh .

# Make startup script executable
RUN chmod +x startup.sh

# Set environment variables
ENV LEAVE_API_URL="http://localhost:8001"
ENV PORT=8003

# Expose port
EXPOSE 8003

# Run the application
CMD ["./startup.sh"]
