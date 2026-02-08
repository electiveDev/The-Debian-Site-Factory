import os
import re
import shutil
from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Directory where sites will be stored
SITES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../sites')

# Ensure the sites directory exists
if not os.path.exists(SITES_DIR):
    os.makedirs(SITES_DIR)

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
        with open(os.path.join(project_path, 'index.html'), 'w') as f:
            f.write(html_content)

        # Save assets
        for asset in assets:
            if asset.filename:
                # Use secure_filename to prevent directory traversal attacks
                filename = secure_filename(asset.filename)
                asset_path = os.path.join(project_path, filename)
                asset.save(asset_path)

        flash(f'Project "{project_id}" deployed successfully!')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error deploying project: {str(e)}')
        return redirect(url_for('create'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
