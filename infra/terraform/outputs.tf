# Printed after `terraform apply` (and any time with `terraform output`).

output "public_ip" {
  description = "Public IP of the server (changes if the instance is replaced)."
  value       = aws_instance.app.public_ip
}

output "web_url" {
  description = "Web UI."
  value       = "http://${aws_instance.app.public_ip}"
}

output "api_docs_url" {
  description = "Interactive API docs."
  value       = "http://${aws_instance.app.public_ip}/docs"
}

output "health_url" {
  description = "Health check (ok / degraded / down)."
  value       = "http://${aws_instance.app.public_ip}/api/health"
}

output "ssh_command" {
  description = "SSH into the server."
  value       = "ssh -i ~/.ssh/placementhub ec2-user@${aws_instance.app.public_ip}"
}

output "instance_id" {
  value = aws_instance.app.id
}

output "s3_bucket" {
  description = "Bucket for backups and resumes."
  value       = aws_s3_bucket.backups.bucket
}

output "bot_token_parameter" {
  description = "SSM parameter holding the bot token (empty if no token was given)."
  value       = local.has_bot_token ? local.token_param_name : ""
}

output "cost_reminder" {
  value = "Run `terraform destroy` when the demo is over. A running instance and its public IPv4 address cost money once Free Tier credits are used up."
}
