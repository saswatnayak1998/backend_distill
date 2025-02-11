FROM python:3.10-slim-buster

WORKDIR /backend

# Install dependencies

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the correct port
EXPOSE 8080

# Start FastAPI using Uvicorn
CMD ["python3","main.py"]