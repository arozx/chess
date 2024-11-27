# Use smaller python image
FROM python:3.11-slim

# Create a non-root
RUN useradd -m chess
USER chess

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5556 available to the world
EXPOSE 5556

# Run the app when the container launches
CMD ["python3", "-m", "online.network_server"]