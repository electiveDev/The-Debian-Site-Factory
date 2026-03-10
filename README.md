# The Debian Site Factory

A small Flask-based dashboard for creating, editing, and serving static sites on a Debian host.

## What this project does

- creates a project folder with an `index.html`
- uploads extra assets such as CSS, JS, and images
- serves projects through nginx under `/sites/<project-id>/`
- provides a simple browser editor with automatic file backups

## Quick start

```bash
sudo ./setup.sh
```

The setup script installs nginx + Python dependencies, deploys the app to `/opt/site-factory`, stores sites in `/var/www/sites`, and creates a systemd service called `site-factory`.

## Runtime configuration

The application reads these environment variables:

- `SITE_FACTORY_SECRET_KEY` – Flask session secret
- `SITE_FACTORY_SITES_DIR` – absolute path to the managed sites directory
- `PORT` – optional development port override

The provided setup script writes `/etc/site-factory.env` automatically and starts gunicorn behind nginx.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manager/app.py
```

Then open `http://127.0.0.1:5000`.

## Notes

- Project IDs are limited to lowercase letters, numbers, and hyphens.
- The editor blocks paths that would escape the project directory.
- Backups are stored inside each project under `.backups/` before edits overwrite an existing file.
