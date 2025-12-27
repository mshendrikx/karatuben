# Base image: Use a lightweight Python 3 image
FROM python:3.11-bullseye

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN mkdir songs logs downloads

# Copy project files
COPY . .

# Specify the command to run when the container starts
CMD ["python3", "app.py"]  
# Replace "app.py" with your main script