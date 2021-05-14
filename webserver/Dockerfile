FROM python:3.9

ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get -y upgrade
RUN mkdir /server
WORKDIR /server
ADD ./requirements.txt /server/
RUN pip3 install -r requirements.txt
ADD ./ /server
RUN mkdir /tmp/printjobs/
RUN mkdir /tmp/allpdfs/
RUN apt install -y cups cups-client
ENV FLASK_ENV development

RUN echo "ServerName cups:631" > /etc/cups/client.conf