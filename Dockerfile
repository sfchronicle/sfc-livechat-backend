FROM python:3
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 WORKDIR /code
 ADD . /code/
 RUN pip3 install -r requirements.txt
 RUN apt-get update && apt-get install -y exiftool
 RUN chmod 777 startup.sh
 EXPOSE 8000

 CMD ./startup.sh
