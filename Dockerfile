FROM python:3.9-slim

WORKDIR /app

# Copy only the necessary files
COPY requirements.txt .
COPY run_storm.py .
COPY storm/ ./storm/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make the script executable
RUN chmod +x run_storm.py

# Set the entrypoint to the run script
ENTRYPOINT ["./run_storm.py"]

# Default command (can be overridden)
CMD ["--help"] 