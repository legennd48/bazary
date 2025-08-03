#!/bin/bash

# =============================================================================
# EC2 Server Setup Script for Bazary Django Project
# =============================================================================
# This script sets up an EC2 instance for deploying the Bazary Django application
# Run this script on your fresh EC2 instance after connecting via SSH
#
# Usage: chmod +x setup-ec2-server.sh && ./setup-ec2-server.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Run as ec2-user or ubuntu."
fi

log "Starting EC2 server setup for Bazary Django project..."

# =============================================================================
# 1. System Update and Basic Tools
# =============================================================================
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

log "Installing essential system tools..."
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    vim \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# =============================================================================
# 2. Docker Installation
# =============================================================================
log "Installing Docker..."

# Remove any old Docker installations
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group
sudo usermod -aG docker $USER

log "Docker installed successfully"

# =============================================================================
# 3. Docker Compose Installation (standalone)
# =============================================================================
log "Installing Docker Compose..."

# Get latest version
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

log "Docker Compose installed successfully"

# =============================================================================
# 4. Node.js Installation (for frontend assets if needed)
# =============================================================================
log "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

log "Node.js $(node --version) and npm $(npm --version) installed"

# =============================================================================
# 5. Nginx Installation and Configuration
# =============================================================================
log "Installing and configuring Nginx..."
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Create basic Nginx configuration for Bazary
sudo tee /etc/nginx/sites-available/bazary > /dev/null <<EOF
server {
    listen 80;
    server_name _;  # Replace with your domain

    client_max_body_size 20M;

    # Serve static files
    location /static/ {
        alias /var/www/bazary/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files
    location /media/ {
        alias /var/www/bazary/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Proxy to Django application
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/bazary /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

log "Nginx installed and configured"

# =============================================================================
# 6. SSL Certificate Setup (Let's Encrypt)
# =============================================================================
log "Installing Certbot for SSL certificates..."
sudo apt install -y certbot python3-certbot-nginx

warn "SSL setup: Run 'sudo certbot --nginx -d yourdomain.com' after setting up your domain"

# =============================================================================
# 7. Firewall Configuration
# =============================================================================
log "Configuring UFW firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw allow 8000/tcp  # Django development server
sudo ufw allow 5432/tcp  # PostgreSQL (if needed externally)
sudo ufw allow 6379/tcp  # Redis (if needed externally)
sudo ufw --force enable

log "Firewall configured"

# =============================================================================
# 8. Project Directory Setup
# =============================================================================
log "Creating project directories..."

# Create directory structure
sudo mkdir -p /var/www/bazary-prod
sudo mkdir -p /var/www/bazary-dev
sudo mkdir -p /var/log/bazary
sudo mkdir -p /var/backups/bazary

# Set proper ownership
sudo chown -R $USER:$USER /var/www/
sudo chown -R $USER:$USER /var/log/bazary
sudo chown -R $USER:$USER /var/backups/bazary

log "Project directories created"

# =============================================================================
# 9. Environment Files Setup
# =============================================================================
log "Setting up environment files..."

# Create production environment template
cat > /var/www/bazary-prod/.env.production.template <<EOF
# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ec2-ip

# Database
DATABASE_URL=postgres://bazary_user:your-password@localhost:5432/bazary_prod

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (configure with your email service)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for production media files)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket

# Monitoring
SENTRY_DSN=your-sentry-dsn
EOF

# Create development environment template
cat > /var/www/bazary-dev/.env.development.template <<EOF
# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=dev-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-ec2-ip

# Database
DATABASE_URL=postgres://bazary_user:dev-password@localhost:5432/bazary_dev

# Redis
REDIS_URL=redis://localhost:6379/1
EOF

log "Environment templates created"

# =============================================================================
# 10. Deployment Scripts Setup
# =============================================================================
log "Creating deployment scripts..."

# Create deployment script for production
cat > /var/www/deploy-production.sh <<'EOF'
#!/bin/bash
set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting production deployment..."

cd /var/www/bazary-prod

# Pull latest code
git pull origin main

# Copy environment file
cp .env.production .env

# Build and start containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Restart Nginx
sudo systemctl reload nginx

log "Production deployment completed successfully"
EOF

# Create deployment script for development
cat > /var/www/deploy-development.sh <<'EOF'
#!/bin/bash
set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting development deployment..."

cd /var/www/bazary-dev

# Pull latest code
git pull origin develop

# Copy environment file
cp .env.development .env

# Build and start containers
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec -T web python manage.py migrate

log "Development deployment completed successfully"
EOF

# Make scripts executable
chmod +x /var/www/deploy-production.sh
chmod +x /var/www/deploy-development.sh

log "Deployment scripts created"

# =============================================================================
# 11. System Services and Monitoring
# =============================================================================
log "Setting up system monitoring..."

# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create log rotation configuration
sudo tee /etc/logrotate.d/bazary > /dev/null <<EOF
/var/log/bazary/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
}
EOF

log "System monitoring configured"

# =============================================================================
# 12. SSH Key Setup for GitHub (for CI/CD)
# =============================================================================
log "Setting up SSH key for GitHub access..."

# Generate SSH key if it doesn't exist
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 4096 -C "ec2-server-$(hostname)" -f ~/.ssh/id_rsa -N ""
    log "SSH key generated at ~/.ssh/id_rsa.pub"
    echo "Add this public key to your GitHub repository's Deploy Keys:"
    cat ~/.ssh/id_rsa.pub
else
    log "SSH key already exists"
fi

# =============================================================================
# Final Setup Instructions
# =============================================================================
log "EC2 server setup completed successfully!"

echo -e "\n${BLUE}==============================================================================${NC}"
echo -e "${BLUE}                            SETUP COMPLETE${NC}"
echo -e "${BLUE}==============================================================================${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Log out and log back in to apply Docker group permissions"
echo "2. Add the SSH public key to your GitHub repository's Deploy Keys"
echo "3. Clone your repository to /var/www/bazary-prod and /var/www/bazary-dev"
echo "4. Configure your .env files based on the templates created"
echo "5. Set up your domain name and run: sudo certbot --nginx -d yourdomain.com"
echo "6. Test your deployment scripts"

echo -e "\n${YELLOW}Important Files Created:${NC}"
echo "- /etc/nginx/sites-available/bazary (Nginx configuration)"
echo "- /var/www/deploy-production.sh (Production deployment script)"
echo "- /var/www/deploy-development.sh (Development deployment script)"
echo "- /var/www/bazary-prod/.env.production.template"
echo "- /var/www/bazary-dev/.env.development.template"

echo -e "\n${YELLOW}SSH Public Key (add to GitHub Deploy Keys):${NC}"
cat ~/.ssh/id_rsa.pub

echo -e "\n${GREEN}Server is ready for CI/CD pipeline integration!${NC}"
