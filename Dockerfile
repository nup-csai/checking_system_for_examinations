FROM python:3.9

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y git docker.io
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Start Docker daemon
CMD ["dockerd"]

# Run checker-main.py in the background
CMD ["python", "checker-main.py"]