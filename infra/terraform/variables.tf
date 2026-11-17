# Inputs. Set your values in terraform.tfvars (copy terraform.tfvars.example).

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix for resource names (lowercase letters, digits, hyphens)."
  type        = string
  default     = "placementhub"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.project_name))
    error_message = "Use 3-20 lowercase letters, digits or hyphens."
  }
}

variable "instance_type" {
  description = "EC2 size: t3.micro (default, 1 GB RAM) or t3.small (2 GB, smoother demos)."
  type        = string
  default     = "t3.micro"

  validation {
    condition     = contains(["t3.micro", "t3.small", "t2.micro"], var.instance_type)
    error_message = "Only free-plan friendly types are allowed: t3.micro, t3.small, t2.micro."
  }
}

variable "root_volume_gb" {
  description = "Disk size in GB (Free Tier includes up to 30 GB of EBS)."
  type        = number
  default     = 20
}

variable "ssh_public_key" {
  description = "Contents of your SSH PUBLIC key (e.g. ~/.ssh/placementhub.pub)."
  type        = string
}

variable "ssh_allowed_cidrs" {
  description = "Who may reach SSH (port 22). 0.0.0.0/0 is needed for GitHub-hosted CD runners; login is key-only."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "repo_url" {
  description = "Public Git URL of this repository, cloned onto the server."
  type        = string
}

variable "repo_branch" {
  description = "Branch to deploy."
  type        = string
  default     = "main"
}

variable "image_prefix" {
  description = "Container image prefix in GHCR, e.g. ghcr.io/<github-user>/placementhub."
  type        = string
}

variable "alert_email" {
  description = "Email address that receives AWS Budget alerts."
  type        = string
}

variable "budget_limit_usd" {
  description = "Monthly budget that triggers alert emails."
  type        = string
  default     = "5"
}

# ---- Telegram bot (optional: leave the token empty to run without the bot) ----

variable "telegram_bot_token" {
  description = "Bot token from @BotFather. Stored in SSM Parameter Store as a SecureString."
  type        = string
  default     = ""
  sensitive   = true
}

variable "source_chat_ids" {
  description = "Comma-separated Telegram chat ids the bot reads placement messages from."
  type        = string
  default     = ""
}

variable "forum_chat_id" {
  description = "Telegram forum group id for reposted job cards (optional)."
  type        = string
  default     = ""
}

variable "topic_ids" {
  description = "Forum topic ids per category (optional)."
  type = object({
    fulltime   = string
    internship = string
    hackathon  = string
    other      = string
  })
  default = {
    fulltime   = ""
    internship = ""
    hackathon  = ""
    other      = ""
  }
}
