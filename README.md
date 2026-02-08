# The Debian Site Factory

Die Debian Site Factory ist ein leichtgewichtiges Tool zum Bereitstellen und Verwalten von statischen Websites auf Debian/Ubuntu-Servern. Es nutzt **Nginx** für die Bereitstellung statischer Inhalte und einen **Flask-basierten Manager** für die einfache Erstellung und Bereitstellung von Websites.

## Installation

Diese Anleitung geht davon aus, dass Sie die Anwendung auf einem frischen Debian- oder Ubuntu-Server einrichten.

### Voraussetzungen

- Ein Server mit **Debian** oder **Ubuntu**.
- **Root-Zugriff** (oder ein Benutzer mit `sudo`-Rechten).
- `git` installiert (optional, um das Repo zu klonen).

### Schritt-für-Schritt-Anleitung

1.  **Repository klonen**
    Beginnen Sie, indem Sie das Projekt auf Ihren Server klonen:
    ```bash
    git clone https://github.com/your-username/The-Debian-Site-Factory.git
    cd The-Debian-Site-Factory
    ```

2.  **Setup-Skript ausführen**
    Das Projekt enthält ein automatisiertes Setup-Skript (`setup.sh`), das alle Abhängigkeiten und Konfigurationen übernimmt. Führen Sie es mit Root-Rechten aus:
    ```bash
    sudo ./setup.sh
    ```

    **Was macht das Setup-Skript?**
    -   Installiert notwendige Systempakete: `nginx`, `python3`, `python3-pip`, `python3-venv`.
    -   Erstellt die Projektverzeichnisstruktur unter `/opt/site-factory`.
    -   Richtet eine Python-Virtual-Environment ein und installiert Flask und Gunicorn.
    -   Konfiguriert Nginx, um das Dashboard und die statischen Websites bereitzustellen.
    -   Erstellt und startet einen Systemd-Dienst (`site-factory`), um den Manager am Laufen zu halten.

3.  **Zugriff auf das Dashboard**
    Sobald das Skript abgeschlossen ist, zeigt es die IP-Adresse Ihres Servers an. Öffnen Sie Ihren Webbrowser und navigieren Sie zu:
    ```
    http://<ihre-server-ip>
    ```
    Sie sollten das **Site Factory Manager** Dashboard sehen.

## Nutzung

### Eine neue Website erstellen

1.  Navigieren Sie zum Dashboard unter `http://<ihre-server-ip>`.
2.  Klicken Sie auf **"Create New Site"** (oder navigieren Sie zu `/create`).
3.  Geben Sie eine **Project ID** ein (dies wird Teil der URL sein, z. B. `meine-seite`).
4.  Fügen Sie Ihren HTML-Inhalt ein und laden Sie notwendige Assets hoch (CSS, JS, Bilder).
5.  Klicken Sie auf **"Deploy"**.

### Anzeigen Ihrer Websites

Bereitgestellte Websites werden als statische Dateien von Nginx bereitgestellt. Sie können sie unter folgendem Link aufrufen:

```
http://<ihre-server-ip>/sites/<project-id>/
```

Wenn Ihre Project ID zum Beispiel `mein-portfolio` ist, lautet die URL `http://<ihre-server-ip>/sites/mein-portfolio/`.

## Konfigurationsdetails

-   **App-Verzeichnis:** `/opt/site-factory/manager`
-   **Statische Websites:** `/var/www/sites` (symlinked zu `/opt/site-factory/sites`)
-   **Nginx-Konfiguration:** `/etc/nginx/sites-available/site-factory`
-   **Systemd-Dienst:** `site-factory.service`
