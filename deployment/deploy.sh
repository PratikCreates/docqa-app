#!/bin/bash

# Document Intelligence Platform - GCP Deployment Script
# For students - cost-optimized deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="docai-platform"

# Functions
print_step() {
    echo -e "${BLUE}==== $1 ====${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if gcloud is installed
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first:"
        echo "https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    print_success "gcloud CLI is installed"
}

# Get project ID
get_project_id() {
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${YELLOW}Enter your GCP Project ID:${NC}"
        read -r PROJECT_ID
    fi
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "Project ID is required"
        exit 1
    fi
    
    print_success "Using project: $PROJECT_ID"
}

# Set up gcloud
setup_gcloud() {
    print_step "Setting up gcloud configuration"
    
    gcloud config set project "$PROJECT_ID"
    gcloud config set run/region "$REGION"
    
    print_success "gcloud configured"
}

# Enable required APIs
enable_apis() {
    print_step "Enabling required APIs"
    
    apis=(
        "run.googleapis.com"
        "cloudbuild.googleapis.com"
        "containerregistry.googleapis.com"
        "sqladmin.googleapis.com"
        "storage.googleapis.com"
        "documentai.googleapis.com"
        "secretmanager.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        echo "Enabling $api..."
        gcloud services enable "$api" --quiet
    done
    
    print_success "APIs enabled"
}

# Build and deploy with Cloud Build
build_and_deploy() {
    print_step "Building and deploying application"
    
    # Submit build
    gcloud builds submit \
        --config=deployment/cloudbuild.yaml \
        --substitutions=_SERVICE_NAME="$SERVICE_NAME" \
        .
    
    print_success "Application deployed"
}

# Create Cloud SQL instance (optional)
setup_database() {
    print_step "Setting up Cloud SQL database"
    
    echo -e "${YELLOW}Do you want to create a Cloud SQL instance? (y/n)${NC}"
    read -r create_db
    
    if [[ $create_db == "y" || $create_db == "Y" ]]; then
        print_warning "Creating Cloud SQL instance (this will cost ~$10-15/month)"
        
        # Create instance
        gcloud sql instances create docai-postgres \
            --database-version=POSTGRES_15 \
            --tier=db-f1-micro \
            --region="$REGION" \
            --storage-size=10GB \
            --storage-type=SSD \
            --backup-start-time=03:00 \
            --enable-bin-log \
            --authorized-networks=0.0.0.0/0 \
            --quiet || true
        
        # Create database
        gcloud sql databases create docai_db \
            --instance=docai-postgres \
            --quiet || true
        
        # Create user
        gcloud sql users create docai_user \
            --instance=docai-postgres \
            --password=secure_password_123 \
            --quiet || true
        
        print_success "Database created"
    else
        print_warning "Skipping database creation - using SQLite for now"
    fi
}

# Create storage bucket
setup_storage() {
    print_step "Setting up Cloud Storage"
    
    bucket_name="${PROJECT_ID}-docai-documents"
    
    gsutil mb -l "$REGION" "gs://$bucket_name" || true
    gsutil versioning set on "gs://$bucket_name"
    
    print_success "Storage bucket created: $bucket_name"
}

# Get service URL
get_service_url() {
    print_step "Getting service URL"
    
    url=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(status.url)")
    
    print_success "Service deployed at: $url"
    echo -e "${GREEN}🚀 Your Document Intelligence Platform is live!${NC}"
    echo -e "${BLUE}API Documentation: $url/docs${NC}"
    echo -e "${BLUE}Health Check: $url/health${NC}"
}

# Estimate costs
show_cost_estimate() {
    print_step "Cost Estimate (Monthly)"
    
    echo -e "${YELLOW}Estimated monthly costs:${NC}"
    echo "• Cloud Run (2 CPU, 2GB RAM): ~$5-15"
    echo "• Cloud SQL (db-f1-micro): ~$10-15"
    echo "• Cloud Storage (10GB): ~$0.20"
    echo "• Cloud Build (100 builds): ~$1"
    echo "• Document AI (1000 pages): ~$1.50"
    echo "• Total: ~$17-32/month"
    echo ""
    echo -e "${GREEN}With $300 credits, this will run for 9-17 months!${NC}"
}

# Main deployment flow
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          Document Intelligence Platform - GCP Deploy         ║"
    echo "║                    Student-Friendly Version                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_gcloud
    get_project_id
    setup_gcloud
    show_cost_estimate
    
    echo -e "${YELLOW}Continue with deployment? (y/n)${NC}"
    read -r continue_deploy
    
    if [[ $continue_deploy != "y" && $continue_deploy != "Y" ]]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    enable_apis
    setup_storage
    setup_database
    build_and_deploy
    get_service_url
    
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Deployment Complete! 🎉                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Test your API at the URL above"
    echo "2. Set up your API keys in Secret Manager"
    echo "3. Configure your domain (optional)"
    echo "4. Set up monitoring and alerts"
    echo ""
    echo -e "${YELLOW}Remember to monitor your usage to stay within budget!${NC}"
}

# Run main function
main "$@"