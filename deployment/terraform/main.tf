# Terraform configuration for GCP deployment
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "documentai.googleapis.com",
    "translate.googleapis.com",
    "language.googleapis.com",
    "secretmanager.googleapis.com"
  ])

  service = each.value
  project = var.project_id

  disable_dependent_services = true
}

# Cloud Storage bucket for document storage
resource "google_storage_bucket" "document_storage" {
  name     = "${var.project_id}-docai-documents-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud SQL instance (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  name             = "docai-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"  # Smallest instance for students
    
    disk_size = 10
    disk_type = "PD_SSD"
    
    backup_configuration {
      enabled = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"  # For development only
      }
    }
  }

  deletion_protection = false  # For easy cleanup

  depends_on = [google_project_service.required_apis]
}

# Database
resource "google_sql_database" "database" {
  name     = "docai_db"
  instance = google_sql_database_instance.postgres.name
}

# Database user
resource "google_sql_user" "user" {
  name     = "docai_user"
  instance = google_sql_database_instance.postgres.name
  password = "secure_password_123"  # Change this!
}

# Secret Manager for API keys
resource "google_secret_manager_secret" "api_keys" {
  secret_id = "docai-api-keys"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Run service
resource "google_cloud_run_service" "docai_platform" {
  name     = "docai-platform"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/docai-platform:latest"
        
        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "DATABASE_URL"
          value = "postgresql://${google_sql_user.user.name}:${google_sql_user.user.password}@${google_sql_database_instance.postgres.connection_name}/${google_sql_database.database.name}"
        }

        env {
          name  = "STORAGE_BUCKET"
          value = google_storage_bucket.document_storage.name
        }
      }

      container_concurrency = 100
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgres.connection_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.required_apis]
}

# IAM policy for Cloud Run (allow unauthenticated access)
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.docai_platform.name
  location = google_cloud_run_service.docai_platform.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "cloud_run_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.docai_platform.status[0].url
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "storage_bucket_name" {
  description = "Cloud Storage bucket name"
  value       = google_storage_bucket.document_storage.name
}