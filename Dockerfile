# Use an official Python runtime as a parent image
FROM python:3.13-alpine

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["python", "moes_thermostat_2_mqtt_bridge.py"]
