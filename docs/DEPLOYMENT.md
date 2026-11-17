# Deploying PlacementHub to AWS (Free plan)

Everything here stays inside the AWS Free plan when you follow the cost rules:
one small EC2 instance, an S3 bucket, an SSM parameter and a budget alert.
No NAT gateway, no load balancer, no RDS, no managed OpenSearch, no Elastic IP.

> **Always run `terraform destroy` when your demo is over.** See [Clean up](#7-clean-up-do-not-skip).

---

## 1. One-time AWS account setup

1. **Create the account** at <https://aws.amazon.com/free> and choose the
   **Free plan**. New accounts get Free Tier credits; the Free plan does not
   charge your card until you upgrade, and it closes the account if credits
   run out instead of billing you.
2. **Secure the root user**: Account menu → *Security credentials* → assign
   **MFA** (an authenticator app). Use the root user only for billing.
3. **Billing alerts**: *Billing and Cost Management* → *Billing preferences* →
   turn on **Free Tier usage alerts** and enter your email.
   (Terraform also creates a $5 AWS Budget with email alerts.)
4. **Create an IAM user for daily work** (never use root for Terraform):
   - *IAM* → *Users* → *Create user*, name `terraform-admin`.
   - Attach policy **AdministratorAccess** (simple for a personal learning
     account; in a company you would grant only the services you need).
   - Enable **MFA** for this user too.
   - *Security credentials* → *Create access key* → *Command Line Interface*.
     Copy the key ID and secret **once**; never put them in Git or chat.
5. **Install the AWS CLI** (Windows): `winget install Amazon.AWSCLI`, then:

   ```powershell
   aws configure
   # AWS Access Key ID:     <from step 4>
   # AWS Secret Access Key: <from step 4>
   # Default region name:   ap-south-1
   # Default output format: json
   aws sts get-caller-identity      # should print your account and terraform-admin
   ```

6. **Install Terraform**: `winget install Hashicorp.Terraform`, then `terraform version`.

## 2. SSH key for deployments

```powershell
ssh-keygen -t ed25519 -f $HOME\.ssh\placementhub -C "placementhub-deploy"
Get-Content $HOME\.ssh\placementhub.pub      # this PUBLIC key goes into terraform.tfvars
```

The private key (`placementhub`, no extension) stays on your laptop and in
the `EC2_SSH_KEY` GitHub secret for CD. Never commit it.

## 3. Push the code and let CD build images (recommended first)

Push the repository to GitHub (public repo). The CD workflow builds the
images and pushes them to GitHub Container Registry (GHCR). If images are not
available yet, the server builds them itself on first boot (slower on t3.micro).

## 4. Configure and apply Terraform

```powershell
cd infra\terraform
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars        # fill in: ssh_public_key, repo_url, image_prefix, alert_email, bot token (optional)

terraform init                  # downloads the AWS provider
terraform plan                  # dry run: shows exactly what will be created
terraform apply                 # type "yes" to create everything
```

Expected: `Apply complete! Resources: 17 added` (the exact count is 16 without
a bot token) and outputs such as:

```
web_url      = "http://13.233.x.x"
health_url   = "http://13.233.x.x/api/health"
ssh_command  = "ssh -i ~/.ssh/placementhub ec2-user@13.233.x.x"
s3_bucket    = "placementhub-backups-1a2b3c4d"
```

### What `plan` and `apply` do
- `plan` compares your code with the **state** (what Terraform created
  before) and with real AWS, then lists the changes. Nothing changes yet.
- `apply` performs exactly those changes and updates the state.
- Running `apply` again with no code changes does nothing: Terraform is
  **declarative** (you describe the end result, not the steps).

## 5. Verify

The first boot installs Docker, creates swap and starts the stack: wait
**5–10 minutes** (longer if the server has to build the images).

```powershell
curl.exe http://<public_ip>/api/health          # {"status":"ok",...}
ssh -i $HOME\.ssh\placementhub ec2-user@<public_ip>
sudo tail -f /var/log/placementhub-setup.log    # first-boot log
cd /opt/placementhub && docker compose ps       # all services healthy
python3 -m scripts.seed --api http://127.0.0.1:8000   # load the 50 sample messages
```

Open `http://<public_ip>` in a browser and search.

## 6. Logs and monitoring

- **Container logs**: `docker compose logs -f api` (JSON lines, rotated at 10 MB x 3).
- **Metrics**: `curl http://127.0.0.1:8000/metrics` on the server (blocked from
  the internet by nginx on purpose).
- **CloudWatch Logs (optional)**: Docker can ship logs straight to CloudWatch
  with the `awslogs` logging driver:

  ```yaml
  logging:
    driver: awslogs
    options:
      awslogs-region: ap-south-1
      awslogs-group: /placementhub/api
      awslogs-create-group: "true"
  ```

  The instance role would also need `logs:CreateLogGroup`, `logs:CreateLogStream`
  and `logs:PutLogEvents`. CloudWatch Logs has a free allowance (5 GB/month);
  this project keeps local rotated logs by default to stay at zero cost.

## 7. Clean up (do not skip)

```powershell
cd infra\terraform
terraform destroy               # type "yes"
```

This deletes the instance, disk, security group, IAM role, SSM parameter,
budget and the S3 bucket (including backups, because `force_destroy = true`).
Check the EC2 console afterwards: no running instances in **ap-south-1**.

### Why it matters
- A running instance uses Free Tier hours/credits around the clock.
- AWS charges for every **public IPv4 address** (about $3.6/month) once the
  free allowance is used up.
- `t3` instances are set to `cpu_credits = "standard"`, so they never bill for
  extra CPU bursts.

## 8. Terraform state

`terraform.tfstate` is Terraform's memory of what it created. It is local by
default, excluded from Git, and contains secrets (the bot token) in plain
text. For teams, store it in a versioned, encrypted S3 bucket with locking:
see the commented example in [`infra/terraform/backend.tf`](../infra/terraform/backend.tf).
If the state is lost, Terraform no longer knows about the resources; you would
have to `terraform import` them or delete them by hand.
