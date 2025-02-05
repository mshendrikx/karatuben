# Base image: Use a lightweight Python 3 image
FROM python:3.11-bullseye

# Set working directory
WORKDIR /app

RUN mkdir songs

RUN apt-get update && apt-get upgrade
RUN apt-get install  -y 

# Copy project files
COPY . .

# Install dependencies from requirements.txt
RUN pip3 install -r requirements.txt

# Specify the command to run when the container starts
CMD ["python3", "app.py"]  
# Replace "app.py" with your main script