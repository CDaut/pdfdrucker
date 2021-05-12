FROM python:3.9

ENV PYTHONUNBUFFERED 1
RUN mkdir /server
WORKDIR /server
ADD ./requirements.txt /server/
RUN pip3 install -r requirements.txt
ADD ./ /server
ENV FLASK_ENV development
