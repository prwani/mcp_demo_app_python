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
ENV TIMESHEET_API_URL="http://localhost:8002"
ENV PORT=8004

# Expose port
EXPOSE 8004

# Run the application
CMD ["./startup.sh"]
