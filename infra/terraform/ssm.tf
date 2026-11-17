# The Telegram bot token lives in SSM Parameter Store as a SecureString
# (encrypted with KMS). The server reads it at boot using its IAM role, so
# the token never appears in user_data, the AMI, Git or the console.
# Standard-tier parameters are free.
#
# Note: Terraform state still contains the value. Keep the state private
# (local file or an encrypted S3 backend), never in Git.

resource "aws_ssm_parameter" "bot_token" {
  count = local.has_bot_token ? 1 : 0

  name        = local.token_param_name
  description = "Telegram bot token for PlacementHub"
  type        = "SecureString"
  value       = var.telegram_bot_token
}
