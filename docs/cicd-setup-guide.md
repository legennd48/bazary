# CI/CD Pipeline Setup Guide

This guide walks you through setting up the complete CI/CD pipeline for the Bazary project, including GitHub secrets and server configuration.

## 📋 Prerequisites

1. **EC2 Server**: Set up using the `scripts/setup-ec2-server.sh` script
2. **GitHub Repository**: With admin access to configure secrets
3. **Docker Hub Account**: For storing Docker images
4. **Domain Name** (optional): For production deployment

---

## 🔧 Step 1: Run the EC2 Setup Script

After creating your EC2 instance and connecting via SSH:

```bash
# Transfer the setup script to your EC2 server
scp -i your-key.pem scripts/setup-ec2-server.sh ec2-user@your-ec2-ip:~/

# Connect to your server
ssh -i your-key.pem ec2-user@your-ec2-ip

# Run the setup script
chmod +x setup-ec2-server.sh
./setup-ec2-server.sh

# Log out and back in to apply Docker group permissions
exit
ssh -i your-key.pem ec2-user@your-ec2-ip
```

---

## 🔑 Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

### Required Secrets:

#### Docker Hub Configuration
```
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-token
```

#### Server Connection (both dev and prod can use same server)
```
# Development Server
DEV_SERVER_HOST=your-ec2-public-ip
DEV_SERVER_USER=ec2-user  # or ubuntu for Ubuntu instances
DEV_SERVER_SSH_KEY=your-private-ssh-key-content
DEV_SERVER_PORT=22

# Production Server
PROD_SERVER_HOST=your-ec2-public-ip
PROD_SERVER_USER=ec2-user  # or ubuntu for Ubuntu instances  
PROD_SERVER_SSH_KEY=your-private-ssh-key-content
PROD_SERVER_PORT=22
PROD_SERVER_URL=http://your-domain-or-ip
```

#### Database and Application Secrets
```
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-secure-redis-password
SECRET_KEY=your-django-secret-key
```

#### Optional: Notifications
```
SLACK_WEBHOOK=your-slack-webhook-url
```

---

## 🚀 Step 3: Prepare Your Server Repositories

### For Development Environment:
```bash
# On your EC2 server
cd /var/www/
git clone https://github.com/your-username/bazary.git bazary-dev
cd bazary-dev
git checkout develop

# Copy and configure environment file
cp .env.development.template .env.development
# Edit the file with your actual values
nano .env.development
```

### For Production Environment:
```bash
# On your EC2 server
cd /var/www/
git clone https://github.com/your-username/bazary.git bazary-prod
cd bazary-prod
git checkout main

# Copy and configure environment file
cp .env.production.template .env.production
# Edit the file with your actual values
nano .env.production
```

---

## 📝 Step 4: Configure Environment Files

### Development Environment (.env.development):
```env
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-ec2-ip

DATABASE_URL=postgres://bazary_user:dev-password@db:5432/bazary_dev
REDIS_URL=redis://redis:6379/1
```

### Production Environment (.env.production):
```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your-super-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ec2-ip

DATABASE_URL=postgres://bazary_user:secure-password@db:5432/bazary_prod
REDIS_URL=redis://:redis-password@redis:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Optional: AWS S3 for media files
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
```

---

## 🔄 Step 5: Test the Pipeline

### Manual Test First:
```bash
# On your EC2 server, test development deployment
cd /var/www/bazary-dev
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

# Test production deployment
cd /var/www/bazary-prod
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Trigger CI/CD:
1. **Push to develop branch**: Triggers development deployment
2. **Push to main branch**: Triggers production deployment

---

## 🔍 Step 6: Monitor and Troubleshoot

### Check Pipeline Status:
- Go to your GitHub repository → Actions tab
- Monitor each job: code-quality, test, build, deploy

### Server Monitoring:
```bash
# Check running containers
docker ps

# Check logs
docker-compose logs -f web

# Check Nginx status
sudo systemctl status nginx

# Check system resources
htop
```

### Common Issues and Solutions:

#### 1. SSH Connection Fails
- Ensure your SSH key is properly formatted in GitHub secrets
- Check that the EC2 security group allows SSH (port 22)
- Verify the server hostname/IP is correct

#### 2. Docker Build Fails
- Check Docker Hub credentials in GitHub secrets
- Ensure the Dockerfile builds successfully locally

#### 3. Database Connection Issues
- Verify environment variables are set correctly
- Check that PostgreSQL container is running and healthy

#### 4. Nginx Configuration Issues
- Test nginx configuration: `sudo nginx -t`
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`

---

## 🎯 What Happens When You Push Code

### Push to `develop` branch:
1. **Code Quality**: Runs security checks, linting, formatting
2. **Testing**: Runs unit, integration, and API tests
3. **Build**: Creates Docker image and pushes to Docker Hub
4. **Deploy to Dev**: Deploys to development environment on EC2
5. **Health Check**: Verifies the deployment is working

### Push to `main` branch:
1. **All the above steps**
2. **Deploy to Production**: Deploys to production environment
3. **Database Backup**: Creates automatic backup before deployment
4. **Monitoring**: Runs post-deployment health checks
5. **Notifications**: Sends success/failure notifications

---

## 🔧 Advanced Configuration

### SSL Certificate (Production):
```bash
# After setting up your domain
sudo certbot --nginx -d yourdomain.com
```

### Custom Domain Setup:
1. Point your domain to your EC2 IP
2. Update `ALLOWED_HOSTS` in production settings
3. Update GitHub secrets with your domain URL

### Multiple Projects on Same Server:
- Use different ports (8000, 8001, 8002, etc.)
- Update Nginx configuration for each project
- Separate Docker networks for each project

---

## 📚 Next Steps

1. **Monitoring**: Set up application monitoring (Sentry, New Relic)
2. **Logging**: Configure centralized logging
3. **Backup Strategy**: Implement automated database backups
4. **Scaling**: Consider load balancing for high traffic
5. **Security**: Regular security updates and vulnerability scanning

---

Your CI/CD pipeline is now ready! Every push to `develop` or `main` will automatically test, build, and deploy your application. 🚀
