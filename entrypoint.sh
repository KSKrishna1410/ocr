#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database is ready!"

# Set SFTP environment variables if they exist
if [ -f "${SFTP_HOST}" ]; then
    export SFTP_HOST=$(cat ${SFTP_HOST})
fi
if [ -f "${SFTP_PORT}" ]; then
    export SFTP_PORT=$(cat ${SFTP_PORT})
fi
if [ -f "${SFTP_USERNAME}" ]; then
    export SFTP_USERNAME=$(cat ${SFTP_USERNAME})
fi
if [ -f "${SFTP_PASSWORD}" ]; then
    export SFTP_PASSWORD=$(cat ${SFTP_PASSWORD})
fi
if [ -f "${REMOTE_DIR}" ]; then
    export REMOTE_DIR=$(cat ${REMOTE_DIR})
fi

# Start the application
exec "$@"