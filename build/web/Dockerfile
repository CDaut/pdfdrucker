FROM python:3.9

ENV PYTHONUNBUFFERED 1
ENV FLASK_ENV development

ENV CUPS_PRINTER_NAME="ABH"
ENV CUPS_PRINTER_MODEL_OPTION="-o Model=C368"
ENV CUPS_COPY_OPTION="-o Collate=true -n"
ENV CUPS_DUPLEX_OPTION="-o KMDuplex=2Sided"
ENV CUPS_SIMPLEX_OPTION="-o KMDuplex=1Sided"
ENV CUPS_COLOR_OPTION="-o SelectColor=Color"
ENV CUPS_GREYSCALE_OPTION="-o SelectColor=Grayscale"

RUN apt-get update \
  && apt-get install --no-install-recommends -y cups-client smbclient libcupsfilters1

RUN mkdir /etc/cups \
  && echo "ServerName cups:631" > /etc/cups/client.conf

RUN mkdir /server
RUN mkdir /tmp/printjobs/
RUN mkdir /tmp/allpdfs/

WORKDIR /server

COPY ./src/requirements.txt /server/
RUN pip3 install -r requirements.txt

COPY ./src /server

CMD flask run --host=0.0.0.0 --port=8000