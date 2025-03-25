FROM alpine:latest

# Install required dependencies
RUN apk add --no-cache python3 python3-dev gcc g++ make build-base

# Verify installation
RUN gcc --version && g++ --version && make --version && python3 --version \
echo "All development tools and Python are installed correctly."

# Set the working directory
WORKDIR /app

# Copy project files from GitLab
COPY . .

# Default command
CMD ["/bin/sh"]
