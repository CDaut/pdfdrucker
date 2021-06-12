# pdfdrucker

Neuer PDF-Drucker für das ABH/RSH. Gut kommentiert, endlich mal funktionierend und vor allem nicht in php.

## Installation

Du benötigst docker und docker-compose. Dann nur noch ``docker-compose up`` im repository root und es fahren zwei
container hoch.

- Unter ``127.0.0.1:8000`` ist das PDF Drucker web interface verfügbar. Da musst du die PDF Datei hochladen und auf
  Drucken klicken.
- Unter ``127.0.0.1:8080`` läuft das web-interface des CUPS Servers. Da kann man ggf. Druckaufträge anschauen falls
  nötig
- Mit  ``docker exec -i -t pdfdrucker_<web/cups>_1 /bin/bash`` bekommt man eine interaktive tty in den container.
  Praktisch zum debuggen ansonsten nutzlos.

## secrets.yml

Im /webserver Verzeichnis muss eine Datei namens secrets.yml mit dem folgenden Inhalt angelegt werden:

```yaml
username: <pdf printer username>
db_password: <database user password>
sftp_password: <sftp password>
mail_password: <mail server password>
```

## config Optionen

- **maxpdfsize** Maximale Seitenzahl, die ein PDF Dokument haben kann, bevor es abgelehnt wird
- **spooler_directory** Verzeichnis in das die PDFs kopiert werden, die tatsächlich gedruckt werden sollen
- **temporary_storage** Verzeichnis in das alle PDFs gespeichert werden
- **status_fetch_sleep_interval: float** Zeit in Sekunden, die zwischen jedem abfragen des Job Status' gewartet wird
- **check_for_new_job_interval: float** Zeit in Sekunden, die gewartet wird, bevor die printerqueue nach neuen jobs
  durchsucht wird
- **db_address** Adresse der Datenbank für die Nutzerauthentifizierung
- **db_name** Name der Datenbank für die Nutzerauthentifizierung
- **sftp_address** Adresse des sftp Servers auf dem die einzelnen print queue Ordner liegen
- **remote_dir** Pfad zum Ordner in dem sich alle print queues befinden
- **version** Version des Programmes, angezeigt auf der Hauptseite unten
- **queue_alert_threshold** Wenn mehr als so viele printjobs in der queue sind, wird eine E-Mail benachrichtigung an die
  unten genannte E-Mail-Adresse gesendet.
- **to_address** Die E-Mail Adresse, die benachrichtigt wird
- **from_address** Die E-Mail Adresse von der aus dieses Programm alle Benachrichtigungen verschickt
- **smtp_port** Der Port des Ausgangsmailservers (nur SMTP wird unterstützt)
- **smtp_server_address** Die Adresse des SMTP Ausgangsmailservers