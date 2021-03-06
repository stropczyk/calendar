FROM python:3.8-slim-buster
COPY . ./app
WORKDIR /app

# Install dependencies:
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run the application:
RUN ls
RUN pip list

EXPOSE 5000
ENTRYPOINT [ "python3", "run.py" ]

# Run container on port 5000:5000 - flask works on port 5000
# sudo docker run --name [container's name] -p 5000:5000 [image name]

