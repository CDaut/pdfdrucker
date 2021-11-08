FROM debian:bullseye

ENV CUPS_PRINTER_NAME="ABH"
ENV CUPS_PRINTER_PATH="file:///print/out.ps"
ENV CUPS_PPD_PATH="/home/print/PPDs/KOC759U.ppd"

# Install Packages (basic tools, cups, basic drivers, HP drivers)
RUN apt-get update \
&& apt-get install -y \
  sudo \
  whois \
  usbutils \
  cups \
  cups-client \
  cups-bsd \
  cups-filters \
  foomatic-db-compressed-ppds \
  printer-driver-all \
  openprinting-ppds \
  hpijs-ppds \
  hp-ppd \
  hplip \
  smbclient \
  printer-driver-cups-pdf

# Add user and disable sudo password checking
RUN useradd \
    --groups=sudo,lp,lpadmin \
    --create-home \
    --home-dir=/home/print \
    --shell=/bin/bash \
    --password=$(mkpasswd print) \
    print \
  && sed -i '/%sudo[[:space:]]/ s/ALL[[:space:]]*$/NOPASSWD:ALL/' /etc/sudoers

# Configure the service's to be reachable
RUN /usr/sbin/cupsd \
  && while [ ! -f /var/run/cups/cupsd.pid ]; do sleep 1; done \
  && cupsctl WebInterface=yes \
  && cupsctl --remote-admin --remote-any --share-printers \
  && kill $(cat /var/run/cups/cupsd.pid)

# Copy PPDs
COPY ./PPDs /home/print/PPDs

# Copy entypoint script
COPY ./entrypoint.sh /entrypoint.sh

# Patch the default configuration file to only enable encryption if requested
RUN sed -e '0,/^</s//DefaultEncryption IfRequested\n&/' -i /etc/cups/cupsd.conf

# Patch the default configuration file to enable the FileDevice
RUN sed -e 's/#FileDevice No/FileDevice Yes/' -i /etc/cups/cups-files.conf

CMD ["/entrypoint.sh"]