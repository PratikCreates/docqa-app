# 🚀 GCP Deployment Guide for Students

This guide will help you deploy your Document Intelligence Platform to Google Cloud Platform using your $300 credits efficiently.

## 📋 Prerequisites

### 1. GCP Account Setup
- [ ] Create a GCP account at [console.cloud.google.com](https://console.cloud.google.com)
- [ ] Activate your $300 free credits
- [ ] Create a new project (e.g., "docai-platform-dev")
- [ ] Enable billing for your project

### 2. Local Setup
- [ ] Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [ ] Install [Docker](https://docs.docker.com/get-docker/) (optional)
- [ ] Install [Terraform](https://terraform.io/downloads) (optional)

## 🎯 Deployment Options

### Option 1: Quick Deploy (Recommended for Students)
**Time**: 15-30 minutes  
**Cost**: ~$5-15/month  
**Complexity**: Beginner

```bash
# Make the script executable
chmod +x deployment/deploy.sh

# Run the deployment
./deployment/deploy.sh
```

### Option 2: Manual Step-by-Step
**Time**: 1-2 hours  
**Cost**: ~$10-25/month  
**Complexity**: Intermediate

### Option 3: Terraform Infrastructure as Code
**Time**: 2-3 hours  
**Cost**: ~$15-35/month  
**Complexity**: Advanced

## 🚀 Quick Deploy Instructions

### Step 1: Authenticate with GCP
```bash
# Login to your GCP account
gcloud auth login

# Set your project (replace with your project ID)
gcloud config set project your-project-id

# Set default region
gcloud config set run/region us-central1
```

### Step 2: Run the Deployment Script
```bash
# Navigate to your project directory
cd /path/to/your/project

# Run the deployment script
./deployment/deploy.sh
```

The script will:
- ✅ Enable required GCP APIs
- ✅ Create a Cloud Storage bucket
- ✅ Build your Docker container
- ✅ Deploy to Cloud Run
- ✅ Set up basic monitoring

### Step 3: Test Your Deployment
```bash
# Get your service URL
gcloud run services describe docai-platform --region=us-central1 --format="value(status.url)"

# Test the health endpoint
curl https://your-service-url/health

# View API documentation
# Open https://your-service-url/docs in your browser
```

## 📊 Manual Step-by-Step Deployment

### Step 1: Enable APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable documentai.googleapis.com
```

### Step 2: Create Storage Bucket
```bash
# Create bucket for document storage
gsutil mb -l us-central1 gs://your-project-id-documents

# Enable versioning
gsutil versioning set on gs://your-project-id-documents
```

### Step 3: Build and Deploy
```bash
# Build the container
gcloud builds submit --tag gcr.io/your-project-id/docai-platform

# Deploy to Cloud Run
gcloud run deploy docai-platform \
  --image gcr.io/your-project-id/docai-platform \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### Step 4: Set Up Database (Optional)
```bash
# Create Cloud SQL instance
gcloud sql instances create docai-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database and user
gcloud sql databases create docai_db --instance=docai-postgres
gcloud sql users create docai_user --instance=docai-postgres --password=your-password
```

## 🏗️ Terraform Deployment

### Step 1: Initialize Terraform
```bash
cd deployment/terraform
terraform init
```

### Step 2: Plan Deployment
```bash
terraform plan -var="project_id=your-project-id"
```

### Step 3: Apply Configuration
```bash
terraform apply -var="project_id=your-project-id"
```

## 💰 Cost Optimization Tips

### 1. Use Smallest Instances
- Cloud Run: Start with 1 CPU, 1GB RAM
- Cloud SQL: Use db-f1-micro (shared CPU)
- Storage: Use Standard class, not Premium

### 2. Set Up Budget Alerts
```bash
# Create a budget alert at $20/month
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="DocAI Budget" \
  --budget-amount=20USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90
```

### 3. Monitor Usage
- Check [GCP Console](https://console.cloud.google.com/billing)
- Set up Cloud Monitoring alerts
- Use Cloud Run's automatic scaling

### 4. Clean Up Resources
```bash
# Delete Cloud Run service
gcloud run services delete docai-platform --region=us-central1

# Delete Cloud SQL instance
gcloud sql instances delete docai-postgres

# Delete storage bucket
gsutil rm -r gs://your-project-id-documents
```

## 🔧 Configuration

### Environment Variables
Set these in Cloud Run:
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host/db
STORAGE_BUCKET=your-bucket-name
NEBIUS_API_KEY=your-api-key
```

### Secret Management
```bash
# Store API keys in Secret Manager
gcloud secrets create nebius-api-key --data-file=api-key.txt
gcloud secrets create openai-api-key --data-file=openai-key.txt
```

## 📈 Monitoring & Logging

### Set Up Monitoring
```bash
# Enable monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime check
gcloud alpha monitoring uptime create \
  --display-name="DocAI Health Check" \
  --http-check-path="/health" \
  --hostname="your-service-url"
```

### View Logs
```bash
# View Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Follow logs in real-time
gcloud logs tail "resource.type=cloud_run_revision"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Build Fails
```bash
# Check build logs
gcloud builds log [BUILD_ID]

# Common fixes:
# - Check Dockerfile syntax
# - Verify requirements.txt
# - Ensure all files are committed
```

#### 2. Service Won't Start
```bash
# Check service logs
gcloud run services logs read docai-platform --region=us-central1

# Common fixes:
# - Check environment variables
# - Verify port configuration (8080)
# - Check health endpoint
```

#### 3. Database Connection Issues
```bash
# Test database connection
gcloud sql connect docai-postgres --user=docai_user

# Common fixes:
# - Check authorized networks
# - Verify credentials
# - Enable Cloud SQL Admin API
```

## 📚 Learning Resources

### GCP Documentation
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)

### Tutorials
- [Deploy FastAPI to Cloud Run](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service)
- [Cloud SQL with Cloud Run](https://cloud.google.com/sql/docs/postgres/connect-run)
- [Document AI Tutorial](https://cloud.google.com/document-ai/docs/quickstart)

## 🎓 Student Benefits

### Free Tier Resources
- Cloud Run: 2 million requests/month
- Cloud Storage: 5GB/month
- Cloud Build: 120 build-minutes/day
- Document AI: 1,000 pages/month

### Educational Discounts
- Apply for [Google for Education](https://edu.google.com/)
- Join [Google Developer Student Clubs](https://developers.google.com/community/gdsc)
- Use [Qwiklabs](https://www.qwiklabs.com/) for hands-on practice

## 📞 Support

### Getting Help
- [Stack Overflow](https://stackoverflow.com/questions/tagged/google-cloud-platform)
- [GCP Community](https://cloud.google.com/community)
- [Reddit r/googlecloud](https://reddit.com/r/googlecloud)

### Cost Monitoring
- Set up billing alerts
- Use [GCP Pricing Calculator](https://cloud.google.com/products/calculator)
- Monitor usage in [GCP Console](https://console.cloud.google.com/billing)

---

## 🎉 Next Steps After Deployment

1. **Test all endpoints** using the API documentation
2. **Set up custom domain** (optional)
3. **Configure CI/CD** with GitHub Actions
4. **Add monitoring dashboards**
5. **Implement backup strategies**
6. **Scale based on usage**

Remember: Start small, monitor costs, and scale as needed. Your $300 credits should last 6-12 months with careful usage!