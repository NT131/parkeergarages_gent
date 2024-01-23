# Paths to individual configuration files and the local clone of the GitHub repository
nginx_conf="/etc/nginx/sites-available/dashapp" # /path/to/nginx/conf
gunicorn_service="/etc/systemd/system/gunicorn_parkings_ghent.service" # /path/to/gunicorn/service
GITHUB_REPO_DIR=/home/nielstack/projects/erpohk/visualisations/parkings_ghent/gunicorn_and_nginx_files #"/path/to/local/github/repo"

# Copy or sync each specific configuration file to the GitHub repository
rsync -av --exclude='.git/' "$nginx_conf" "$GITHUB_REPO_DIR/"
rsync -av --exclude='.git/' "$gunicorn_service" "$GITHUB_REPO_DIR/"

