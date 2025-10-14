# Use a lightweight base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/Recordings /app/Output

# Copy the necessary files into the container
COPY record.sh /app/record.sh
COPY requirements.txt /app/requirements.txt
COPY run.py /app/run.py
COPY Assembler /app/Assembler
COPY Ingestor /app/Ingestor

# Install necessary packages and make scripts executable
RUN apt-get update && apt-get install -y cron supervisor ffmpeg && \
    chmod +x /app/record.sh /app/run.py
RUN pip install --no-cache-dir -r /app/requirements.txt

# Add a cron job to run `run.py` daily at midnight
RUN echo "0 0 * * * /usr/bin/python3 /app/run.py" > /etc/cron.d/runpy-cron

# Apply the cron job
RUN crontab /etc/cron.d/runpy-cron

# Copy the supervisord configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Run the ingestor on container start
#RUN python3 /app/run.py

RUN echo "=============================="
RUN echo "Container setup complete!"
RUN echo "=============================="

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
