# The single server that runs the whole Docker Compose stack.

resource "aws_key_pair" "deployer" {
  key_name   = "${local.name}-key"
  public_key = var.ssh_public_key
}

resource "aws_instance" "app" {
  ami                         = data.aws_ssm_parameter.al2023_ami.insecure_value
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.deployer.key_name
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  associate_public_ip_address = true

  # First-boot script: swap, Docker, clone the repo, start the stack.
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    aws_region          = var.aws_region
    repo_url            = var.repo_url
    repo_branch         = var.repo_branch
    image_prefix        = var.image_prefix
    es_heap             = local.es_heap
    es_mem_limit        = local.es_mem_limit
    s3_bucket           = aws_s3_bucket.backups.bucket
    has_bot_token       = local.has_bot_token
    token_param_name    = local.token_param_name
    source_chat_ids     = var.source_chat_ids
    forum_chat_id       = var.forum_chat_id
    topic_fulltime_id   = var.topic_ids.fulltime
    topic_internship_id = var.topic_ids.internship
    topic_hackathon_id  = var.topic_ids.hackathon
    topic_other_id      = var.topic_ids.other
  })
  user_data_replace_on_change = true

  root_block_device {
    volume_size           = var.root_volume_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  # IMDSv2 only (blocks a common credential-stealing attack).
  # Hop limit 2 lets containers reach the metadata service for role credentials.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  # "standard" = never pay for extra CPU bursts. The t3 default ("unlimited")
  # can add charges if the CPU stays busy.
  credit_specification {
    cpu_credits = "standard"
  }

  tags = {
    Name = "${local.name}-server"
  }

  lifecycle {
    # A newer Amazon Linux image must not silently replace a running server.
    ignore_changes = [ami]
  }

  depends_on = [aws_ssm_parameter.bot_token]
}
