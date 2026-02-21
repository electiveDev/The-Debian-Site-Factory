import os
import re
import shutil
from datetime import datetime
from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Directory where sites will be stored
SITES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../sites')

# Ensure the sites directory exists
if not os.path.exists(SITES_DIR):
    os.makedirs(SITES_DIR)

# --- Hilfsfunktionen für Rollback & Logging ---

def create_backup(file_path, project_path):
    """Erstellt eine Kopie der Datei im .backups Ordner vor Änderungen."""
    if os.path.exists(file_path):
        # Backup Ordner im Projekt erstellen
        backup_dir = os.path.join(project_path, '.backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Zeitstempel für Versionierung
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_name = f"{filename}_{timestamp}.bak"
        
        try:
            shutil.copy2(file_path, os.path.join(backup_dir, backup_name))
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    return False

def append_log(project_path, message):
    """Schreibt Aktionen in das Projekt-Log."""
    log_file = os.path.join(project_path, 'deployment.log')
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} {message}\n")
    except Exception as e:
        print(f"Logging failed: {e}")

# --- Routen ---

@app.route('/')
def dashboard():
    # List all directories in SITES_DIR
    sites = [d for d in os.listdir(SITES_DIR) if os.path.isdir(os.path.join(SITES_DIR, d))]
    # Filter out 'sites' if it exists
    sites = [s for s in sites if s != 'sites']
    return render_template('dashboard.html', sites=sites)

@app.route('/delete/<project_id>', methods=['POST'])
def delete_project(project_id):
    # Validation
    if not project_id or not re.match(r'^[a-z0-9-]+$', project_id):
        flash('Invalid Project ID.')
        return redirect(url_for('dashboard'))

    project_path = os.path.join(SITES_DIR, project_id)

    if os.path.exists(project_path):
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

    project_path = os.path.join(SITES_DIR, project_id)
    if not os.path.exists(project_path):
        flash('Project not found.')
        return redirect(url_for('dashboard'))

    # Bestimmen, welche Datei bearbeitet werden soll (Default: index.html)
    relative_file_path = request.args.get('file', 'index.html')
    
    # Path Traversal Schutz (wichtig auch lokal)
    if '..' in relative_file_path or relative_file_path.startswith('/'):
        flash('Ungültiger Dateipfad.')
        return redirect(url_for('edit_project', project_id=project_id))

    full_file_path = os.path.join(project_path, relative_file_path)

    # POST: Datei Speichern
    if request.method == 'POST':
        new_content = request.form.get('file_content')
        
        try:
            # 1. Rollback erstellen
            create_backup(full_file_path, project_path)
            
            # 2. Verzeichnisse erstellen (falls Datei in neuem Unterordner liegt)
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
            
            # 3. Datei schreiben
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # 4. Loggen
            append_log(project_path, f"Datei bearbeitet/erstellt: {relative_file_path}")
            
            flash(f'Gespeichert: {relative_file_path} (Backup erstellt)')
            # Redirect um POST-Resubmission zu verhindern
            return redirect(url_for('edit_project', project_id=project_id, file=relative_file_path))
            
        except Exception as e:
            flash(f'Fehler beim Speichern: {str(e)}')

    # GET: Dateiliste und Inhalt laden
    
    # Dateibaum scannen
    file_list = []
    for root, dirs, files in os.walk(project_path):
        if '.backups' in root: continue # Backups ausblenden
        for file in files:
            # Relativen Pfad berechnen
            rel_path = os.path.relpath(os.path.join(root, file), project_path)
            file_list.append(rel_path)
    
    file_list.sort()

    # Dateiinhalt lesen
    file_content = ""
    is_binary = False
    
    if os.path.exists(full_file_path):
        try:
            # Versuch, als Text zu lesen
            with open(full_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            is_binary = True
            file_content = "[Binärdatei - Vorschau nicht verfügbar]"
    
    return render_template('edit.html', 
                           project_id=project_id, 
                           file_content=file_content, 
                           files=file_list, 
                           current_file=relative_file_path,
                           is_binary=is_binary)

@app.route('/create')
def create():
    return render_template('creator.html')

@app.route('/deploy', methods=['POST'])
def deploy():
    project_id = request.form.get('project_id')
    html_content = request.form.get('html_content')
    assets = request.files.getlist('assets')

    # Validation
    if not project_id or not re.match(r'^[a-z0-9-]+$', project_id):
        flash('Invalid Project ID. Use only lowercase letters, numbers, and hyphens.')
        return redirect(url_for('create'))

    if len(project_id) > 50:
         flash('Project ID too long (max 50 chars).')
         return redirect(url_for('create'))

    project_path = os.path.join(SITES_DIR, project_id)
    if os.path.exists(project_path):
        flash('Project ID already exists.')
        return redirect(url_for('create'))

    # Create project directory
    try:
        os.makedirs(project_path)

        # Save index.html
        with open(os.path.join(project_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Save assets
        for asset in assets:
            if asset.filename:
                # Use secure_filename to prevent directory traversal attacks
                filename = secure_filename(asset.filename)
                asset_path = os.path.join(project_path, filename)
                asset.save(asset_path)
        
        # Initial Log
        append_log(project_path, "Projekt initial erstellt.")

        flash(f'Project "{project_id}" deployed successfully!')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error deploying project: {str(e)}')
        return redirect(url_for('create'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
