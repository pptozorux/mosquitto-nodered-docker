# Start with a minimal base image
FROM debian:latest

# Set environment variables
ENV TZ=Europe/Paris

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ntp tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy custom NTP configuration file
COPY ntp.conf /etc/ntp.conf

# Expose NTP port
EXPOSE 123/udp

# Start the NTP service
CMD ["ntpd", "-n", "-g"]
