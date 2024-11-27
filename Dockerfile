# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application's port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
#CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]