import os
import re
import secrets
import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
SITES_DIR = Path(os.environ.get('SITE_FACTORY_SITES_DIR', BASE_DIR.parent / 'sites')).resolve()
SECRET_KEY = os.environ.get('SITE_FACTORY_SECRET_KEY')

app = Flask(__name__)
app.secret_key = SECRET_KEY or secrets.token_hex(32)

# Ensure the sites directory exists
SITES_DIR.mkdir(parents=True, exist_ok=True)


# --- Hilfsfunktionen für Rollback & Logging ---

def create_backup(file_path, project_path):
    """Erstellt eine Kopie der Datei im .backups Ordner vor Änderungen."""
    if file_path.exists():
        backup_dir = project_path / '.backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = file_path.name
        backup_name = f"{filename}_{timestamp}.bak"

        try:
            shutil.copy2(file_path, backup_dir / backup_name)
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    return False


def append_log(project_path, message):
    """Schreibt Aktionen in das Projekt-Log."""
    log_file = project_path / 'deployment.log'
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    try:
        with log_file.open('a', encoding='utf-8') as f:
            f.write(f"{timestamp} {message}\n")
    except Exception as e:
        print(f"Logging failed: {e}")


def get_project_path(project_id):
    return (SITES_DIR / project_id).resolve()


def resolve_project_file(project_path, relative_file_path):
    candidate = (project_path / relative_file_path).resolve()
    if project_path not in candidate.parents and candidate != project_path:
        raise ValueError('Invalid file path.')
    return candidate


# --- Routen ---

@app.route('/')
def dashboard():
    sites = sorted(
        d.name for d in SITES_DIR.iterdir()
        if d.is_dir() and d.name != 'sites'
    )
    return render_template('dashboard.html', sites=sites)


@app.route('/delete/<project_id>', methods=['POST'])
def delete_project(project_id):
    if not project_id or not re.match(r'^[a-z0-9-]+$', project_id):
        flash('Invalid Project ID.')
        return redirect(url_for('dashboard'))

    project_path = get_project_path(project_id)

    if project_path.exists():
        try:
            shutil.rmtree(project_path)
            flash(f'Project "{project_id}" deleted successfully.')
        except Exception as e:
            flash(f'Error deleting project: {str(e)}')
    else:
        flash('Project not found.')

    return redirect(url_for('dashboard'))


@app.route('/edit/<project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if not project_id or not re.match(r'^[a-z0-9-]+$', project_id):
        flash('Invalid Project ID.')
        return redirect(url_for('dashboard'))

    project_path = get_project_path(project_id)
    if not project_path.exists():
        flash('Project not found.')
        return redirect(url_for('dashboard'))

    relative_file_path = request.args.get('file', 'index.html').strip()

    try:
        full_file_path = resolve_project_file(project_path, relative_file_path)
    except ValueError:
        flash('Invalid file path.')
        return redirect(url_for('edit_project', project_id=project_id))

    if request.method == 'POST':
        new_content = request.form.get('file_content', '')

        try:
            create_backup(full_file_path, project_path)
            full_file_path.parent.mkdir(parents=True, exist_ok=True)

            with full_file_path.open('w', encoding='utf-8') as f:
                f.write(new_content)

            append_log(project_path, f"Edited or created file: {relative_file_path}")

            flash(f'Saved: {relative_file_path}')
            return redirect(url_for('edit_project', project_id=project_id, file=relative_file_path))

        except Exception as e:
            flash(f'Error while saving: {str(e)}')

    file_list = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d != '.backups']
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), project_path)
            file_list.append(rel_path)

    file_list.sort()

    file_content = ""
    is_binary = False

    if full_file_path.exists():
        try:
            with full_file_path.open('r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            is_binary = True
            file_content = "[Binary file - preview unavailable]"

    return render_template(
        'edit.html',
        project_id=project_id,
        file_content=file_content,
        files=file_list,
        current_file=relative_file_path,
        is_binary=is_binary,
    )


@app.route('/create')
def create():
    return render_template('creator.html')


@app.route('/deploy', methods=['POST'])
def deploy():
    project_id = request.form.get('project_id')
    html_content = request.form.get('html_content', '')
    assets = request.files.getlist('assets')

    if not project_id or not re.match(r'^[a-z0-9-]+$', project_id):
        flash('Invalid Project ID. Use only lowercase letters, numbers, and hyphens.')
        return redirect(url_for('create'))

    if len(project_id) > 50:
        flash('Project ID too long (max 50 chars).')
        return redirect(url_for('create'))

    project_path = get_project_path(project_id)
    if project_path.exists():
        flash('Project ID already exists.')
        return redirect(url_for('create'))

    try:
        project_path.mkdir(parents=True)

        with (project_path / 'index.html').open('w', encoding='utf-8') as f:
            f.write(html_content)

        for asset in assets:
            if asset.filename:
                filename = secure_filename(asset.filename)
                if not filename:
                    continue
                asset_path = project_path / filename
                asset.save(asset_path)

        append_log(project_path, 'Project created.')

        flash(f'Project "{project_id}" deployed successfully!')
        return redirect(url_for('dashboard'))

    except Exception as e:
        shutil.rmtree(project_path, ignore_errors=True)
        flash(f'Error deploying project: {str(e)}')
        return redirect(url_for('create'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))