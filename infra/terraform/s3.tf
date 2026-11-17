# S3 bucket for raw message backups (and uploaded resumes in Phase 9).

# Bucket names are global across all AWS accounts, so add a random suffix.
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "backups" {
  bucket = "${local.name}-backups-${random_id.bucket_suffix.hex}"

  # Lets `terraform destroy` delete the bucket even when it holds objects.
  # Convenient for a demo project; in production you would keep this false.
  force_destroy = true
}

# Keep old versions of every object, so an overwrite or delete can be undone.
resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block every form of public access, whatever any future policy says.
resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Disable ACLs entirely; access is controlled only by IAM.
resource "aws_s3_bucket_ownership_controls" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Automatic clean-up keeps storage (and cost) small.
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"
    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "expire-backups"
    status = "Enabled"

    filter {
      prefix = "backups/"
    }

    expiration {
      days = 90
    }
  }

  # Resumes are personal data: keep them only briefly.
  rule {
    id     = "expire-resumes"
    status = "Enabled"

    filter {
      prefix = "resumes/"
    }

    expiration {
      days = 30
    }
  }

  depends_on = [aws_s3_bucket_versioning.backups]
}
