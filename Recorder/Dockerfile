# Use the official Alpine Linux image as the base
FROM alpine:latest

# Install necessary packages
RUN apk add --no-cache ffmpeg bash curl

# Create the directory for recordings
RUN mkdir -p /Recordings

# Copy the script into the container
COPY record.sh /record.sh

# Make the script executable
RUN chmod +x /record.sh

# Set up a cron job to run the script at midnight every day
RUN apk add --no-cache busybox-suid && \
    echo "0 0 * * * /record.sh" >> /etc/crontabs/root

# Start the cron daemon
CMD ["crond", "-f"]

# Content of the record.sh script