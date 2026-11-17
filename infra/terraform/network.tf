# Security group = a firewall around the EC2 instance.
# Only two ports are open; Elasticsearch, Redis and the API are reachable
# only from inside the server.

resource "aws_security_group" "app" {
  name        = "${local.name}-sg"
  description = "PlacementHub: HTTP from anywhere, SSH (key-only) for deploys"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.app.id
  description       = "Web UI and API through nginx"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  for_each = toset(var.ssh_allowed_cidrs)

  security_group_id = aws_security_group.app.id
  description       = "SSH for deployments (password login disabled on Amazon Linux)"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.app.id
  description       = "Outbound: Telegram API, GHCR, package updates"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}
