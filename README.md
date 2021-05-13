# pdfdrucker
Neuer PDF-Drucker für das ABH/RSH. Gut kommentiert, endlich mal funktionierend und vor allem nicht in php.

## Installation
Du benötigst docker und docker-compose. 
Dann nur noch ``docker-compose up`` im repository root und es fahren zwei container hoch. 
- Unter ``127.0.0.1:8000`` ist das PDF Drucker web interface verfügbar. Da musst du die PDF 
Datei hochladen und auf Drucken klicken.
- Unter ``127.0.0.1:8080`` läuft das web-interface des CUPS Servers. Da kann man ggf. Druckaufträge
anschauen falls nötig
- Mit  ``docker exec -i -t pdfdrucker_<web/cups>_1 /bin/bash`` bekommt man eine interaktive
tty in den container. Praktisch zum debuggen ansonsten nutzlos.