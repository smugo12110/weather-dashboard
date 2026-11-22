# 📚 Documentation Website Deployment Guide

**Deploy the EA Escrow Platform documentation to the web in 10 minutes.**

---

## 📋 Overview

We've created a professional, self-contained documentation website that includes:
- ✅ Interactive navigation
- ✅ Daily operations checklist
- ✅ Alert response runbooks
- ✅ Monitoring setup guides
- ✅ API documentation
- ✅ Deployment guides
- ✅ Mobile responsive
- ✅ Dark/light theme support

**File**: `docs/index.html` (complete standalone website)

---

## 🚀 Option 1: Deploy to AWS S3 + CloudFront (5 minutes)

### Step 1: Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://escrow-docs

# Enable public access
aws s3api put-bucket-policy --bucket escrow-docs \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::escrow-docs/*"
    }]
  }'

# Enable static website hosting
aws s3api put-bucket-website --bucket escrow-docs \
  --website-configuration '{
    "IndexDocument": {"Suffix": "index.html"},
    "ErrorDocument": {"Key": "index.html"}
  }'
```

### Step 2: Upload Files

```bash
# Upload all documentation files
aws s3 sync ./docs/ s3://escrow-docs/ \
  --include "*.html" \
  --include "*.css" \
  --include "*.js" \
  --exclude ".git*"

# Also upload markdown files for reference
aws s3 sync ./ s3://escrow-docs/markdown/ \
  --include "*.md" \
  --exclude ".git*" \
  --exclude "node_modules/*"
```

### Step 3: Get Website URL

```bash
# Your documentation is now available at:
# http://escrow-docs.s3.amazonaws.com/
# or
# http://escrow-docs.s3-website-us-east-1.amazonaws.com/
```

### Step 4: (Optional) Use CloudFront for HTTPS

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name escrow-docs.s3.amazonaws.com \
  --default-root-object index.html

# Get your CloudFront URL (e.g., d123456.cloudfront.net)
# Add to your domain via DNS CNAME
```

---

## 🌍 Option 2: Deploy Alongside API Server (10 minutes)

Deploy documentation on the same server as your API.

### Step 1: SSH into EC2 Instance

```bash
ssh -i your-key.pem ubuntu@api.eascrow.io
```

### Step 2: Create Documentation Directory

```bash
# Create directory
sudo mkdir -p /var/www/docs
cd /var/www/docs

# Copy documentation
cp ~/escrow-mvp/docs/index.html .
```

### Step 3: Update Nginx Configuration

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-enabled/escrow

# Add documentation location block:
sudo tee -a /etc/nginx/sites-enabled/escrow << 'EOF'

# Documentation website
location /docs {
    alias /var/www/docs/;
    index index.html;
    try_files $uri $uri/ /docs/index.html;
}

# Redirect root to docs
location / {
    return 301 /docs;
}
EOF

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 4: Verify

```bash
# Documentation is now available at:
# https://api.eascrow.io/docs/
```

---

## 💻 Option 3: Run as Separate Node.js Server (10 minutes)

### Step 1: Install Dependencies

```bash
cd ~/escrow-mvp/docs

# Create package.json
cat > package.json << 'EOF'
{
  "name": "escrow-docs",
  "version": "1.0.0",
  "description": "EA Escrow Platform Documentation",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "PORT=3000 node server.js"
  },
  "keywords": ["escrow", "documentation"],
  "author": "",
  "license": "MIT"
}
EOF
```

### Step 2: Start the Server

```bash
# Locally for testing
node server.js
# Accessible at: http://localhost:3000

# Or with PM2
pm2 start server.js --name "escrow-docs" -- --port 3001
```

### Step 3: Configure Reverse Proxy (if on same server)

```bash
# Add to Nginx:
sudo tee -a /etc/nginx/sites-enabled/escrow << 'EOF'

# Documentation server
upstream escrow_docs {
    server localhost:3001;
}

location /docs {
    proxy_pass http://escrow_docs;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
EOF

sudo systemctl reload nginx
```

### Step 4: Verify

```bash
# Documentation available at:
# https://api.eascrow.io/docs/
```

---

## 🐳 Option 4: Docker Deployment (15 minutes)

### Step 1: Create Dockerfile

```dockerfile
# docs/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY server.js .
COPY index.html .

EXPOSE 3000

CMD ["node", "server.js"]
```

### Step 2: Build Docker Image

```bash
cd ~/escrow-mvp/docs

docker build -t escrow-docs:latest .
```

### Step 3: Run Container

```bash
# Run locally
docker run -p 3000:3000 escrow-docs:latest

# Or with Docker Compose
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  docs:
    image: escrow-docs:latest
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
    restart: always
EOF

docker-compose up -d
```

### Step 4: Deploy to AWS ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name escrow-docs

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag escrow-docs:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/escrow-docs:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/escrow-docs:latest
```

---

## 📱 Option 5: Deploy to Vercel (5 minutes)

### Step 1: Prepare for Vercel

```bash
# Create vercel.json
cat > escrow-mvp/docs/vercel.json << 'EOF'
{
  "public": true,
  "redirects": [
    {
      "source": "/:path*",
      "destination": "/index.html"
    }
  ]
}
EOF
```

### Step 2: Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd ~/escrow-mvp/docs
vercel

# Follow the prompts
# Your docs will be live at: escrow-docs.vercel.app
```

### Step 3: Add Custom Domain

```bash
# Point your domain to Vercel
# Add CNAME record: docs.eascrow.io → your-vercel-app.vercel.app
```

---

## ✅ Recommended Deployment

**For production, we recommend:**

| Use Case | Recommendation | Cost | Setup Time |
|----------|----------------|------|-----------|
| Simple static hosting | S3 + CloudFront | $5-10/month | 5 min |
| With existing API | Nginx on same server | Free | 10 min |
| Separate docs server | Node.js + PM2 | $15/month | 15 min |
| Container/Kubernetes | Docker + ECR | $15-50/month | 15 min |
| Fast global delivery | Vercel | Free-$20/month | 5 min |

**We recommend: S3 + CloudFront** for:
- ✅ Highest performance
- ✅ Global CDN
- ✅ HTTPS included
- ✅ Very low cost ($5/month)
- ✅ Auto-scales

---

## 📊 Post-Deployment Checklist

After deploying, verify:

- [ ] Home page loads at https://docs.eascrow.io/
- [ ] Navigation tabs work
- [ ] All sections display correctly
- [ ] Links work (internal navigation)
- [ ] Mobile responsive (test on phone)
- [ ] Code blocks display properly
- [ ] Tables are readable
- [ ] Images load (if any)
- [ ] Page speed acceptable
- [ ] HTTPS certificate valid

---

## 🔄 Keep Documentation Updated

### Every Time You Update Docs

```bash
# If using S3:
aws s3 sync ./docs/ s3://escrow-docs/ \
  --include "*.html" \
  --exclude ".git*"

# If using Nginx:
cp ./docs/index.html /var/www/docs/

# If using Node.js server:
# Restart: pm2 restart escrow-docs
```

### Automated Updates (GitHub Actions)

```yaml
# .github/workflows/deploy-docs.yml
name: Deploy Docs

on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to S3
        run: |
          aws s3 sync ./docs/ s3://escrow-docs/ \
            --include "*.html" \
            --exclude ".git*"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## 🚨 Troubleshooting

### Issue: Website shows 404

**Solution:**
```bash
# Verify files uploaded
aws s3 ls s3://escrow-docs/

# Ensure index.html exists
# Check bucket policies
```

### Issue: Styles not loading

**Solution:**
```bash
# Check MIME types in S3
aws s3api head-object --bucket escrow-docs --key index.html

# Verify Content-Type is text/html
```

### Issue: HTTPS/SSL errors

**Solution:**
```bash
# If using CloudFront, ensure:
# - SSL certificate is generated
# - It covers your domain
# - HTTPS redirect is enabled

# For Nginx:
curl -v https://api.eascrow.io/docs/
```

### Issue: Performance is slow

**Solution:**
```bash
# Enable caching
# S3: Enable CloudFront caching
# Nginx: Add cache-control headers

# Check page load time
time curl https://docs.eascrow.io/ > /dev/null
```

---

## 🎯 Next Steps After Deployment

1. **Update README.md**
   ```markdown
   ## Documentation
   
   Full documentation available at: https://docs.eascrow.io/
   ```

2. **Share with Team**
   - Email link to team
   - Post in Slack
   - Add to onboarding guide

3. **Monitor Access**
   ```bash
   # CloudWatch Logs for S3
   aws logs tail /aws/s3/escrow-docs --follow
   
   # Server logs for Nginx/Node
   tail -f /var/log/nginx/access.log
   ```

4. **Get Feedback**
   - Ask team what's missing
   - Update documentation based on feedback
   - Re-deploy with improvements

---

## 📞 Support

If documentation website goes down:

1. Check service status
2. Review deployment logs
3. Redeploy latest version
4. Email team: ops@eascrow.io

---

## 📈 Monitoring

### Add CloudWatch Monitoring

```bash
# Monitor S3 access
aws s3api put-bucket-logging \
  --bucket escrow-docs \
  --bucket-logging-status file://logging.json

# Monitor CloudFront
aws cloudfront get-distribution-config --id YOUR_DIST_ID
```

### Add Uptime Monitoring

```bash
# Use StatusCake or similar
# Monitor: https://docs.eascrow.io/

# Set alerts for:
# - Response time > 2s
# - Status code != 200
# - Any downtime
```

---

## ✨ Customization

### Add Your Logo

```html
<!-- In index.html -->
<header>
  <img src="/logo.png" alt="Logo" height="40">
  <h1>EA Escrow Platform</h1>
</header>
```

### Change Colors

```css
/* In index.html CSS */
--primary: #667eea;  /* Purple */
--secondary: #764ba2; /* Darker purple */

/* Change to your brand */
--primary: #your-color;
--secondary: #your-color-darker;
```

### Add Analytics

```html
<!-- Add to index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_ID');
</script>
```

---

## 🎉 Done!

Your documentation website is live and accessible to your entire team.

**Next:** 
- Share the URL with your team
- Bookmark in browsers
- Add to README.md
- Keep updated as platform evolves

---

**Questions?** Check the documentation website itself!

🚀 Keep learning. Keep shipping. Keep documenting. 📚
