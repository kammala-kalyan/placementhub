# Shared values and lookups used by the other files.

locals {
  name = var.project_name

  # Elasticsearch must fit in the instance's RAM next to everything else.
  small_instance = contains(["t3.micro", "t2.micro"], var.instance_type)
  es_heap        = local.small_instance ? "256m" : "512m"
  es_mem_limit   = local.small_instance ? "512m" : "1g"

  token_param_name = "/${var.project_name}/telegram_bot_token"
  # The token itself is secret, but "is it set?" is not.
  has_bot_token = nonsensitive(var.telegram_bot_token != "")
}

# Who am I? (used to build ARNs)
data "aws_caller_identity" "current" {}

# The default VPC that every AWS account already has: no NAT gateway,
# no extra networking cost.
data "aws_vpc" "default" {
  default = true
}

# Latest Amazon Linux 2023 image, published by AWS in a public SSM parameter.
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
