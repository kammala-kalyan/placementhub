# ---------------------------------------------------------------------------
# Terraform STATE
# ---------------------------------------------------------------------------
# Terraform remembers what it created in a state file (terraform.tfstate).
# By default it is stored locally, next to this code. That is fine for one
# person learning, but:
#   - it is lost if your laptop dies, and Terraform "forgets" the resources;
#   - teammates cannot share it;
#   - it contains secrets in plain text (e.g. the bot token) - never commit it
#     (it is in .gitignore).
#
# Production setup: a REMOTE BACKEND in S3 with locking.
#   1. Create a separate, versioned, encrypted S3 bucket by hand (once), e.g.
#      aws s3api create-bucket --bucket <unique-name>-tfstate --region ap-south-1 \
#        --create-bucket-configuration LocationConstraint=ap-south-1
#      aws s3api put-bucket-versioning --bucket <unique-name>-tfstate \
#        --versioning-configuration Status=Enabled
#   2. Uncomment the block below, set the bucket name, and run:
#      terraform init -migrate-state
#   `use_lockfile = true` (Terraform 1.10+) stores a lock object in S3 so two
#   people cannot run `apply` at the same time. Older setups used DynamoDB.
#
# The state bucket is NOT managed by this code on purpose: if it were,
# `terraform destroy` would delete the place where the state lives.
# ---------------------------------------------------------------------------

# terraform {
#   backend "s3" {
#     bucket       = "<unique-name>-tfstate"
#     key          = "placementhub/terraform.tfstate"
#     region       = "ap-south-1"
#     encrypt      = true
#     use_lockfile = true
#   }
# }
