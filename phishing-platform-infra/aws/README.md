# AWS Deployment Guide — Phishing Awareness App

> **Deprecated:** This guide describes a legacy EC2 deployment. Current production uses AWS Lambda + API Gateway + Terraform.
> See [documentation/operator/DEPLOYMENT.md](../documentation/operator/DEPLOYMENT.md).

Deploy the Flask phishing awareness app on **AWS Free Tier** using EC2, Docker, and Nginx.

## Architecture

```
Internet → EC2 t2.micro (port 80)
             → Nginx (reverse proxy)
               → Gunicorn (2 workers, port 8000)
                 → Flask app
                   → SQLite (/data/app.db on Docker volume)
```

## Prerequisites

- AWS account (Free Tier eligible)
- AWS CLI v2 installed and configured ([Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- Git installed locally
- A terminal (bash, PowerShell, or similar)

## 1. Free Tier Limits

| Resource | Free Tier Allowance |
|----------|-------------------|
| EC2 t2.micro | 750 hours/month (12 months) |
| EBS storage | 30 GB gp2/gp3 |
| Data transfer | 100 GB/month outbound |
| Elastic IP | Free while associated to a running instance |

**This deployment uses**: 1 t2.micro + 20 GB gp3 + SQLite (no RDS). Cost: **$0/month** within Free Tier.

## 2. IAM Setup

### Create an IAM User (Console)

1. Go to **IAM → Users → Create user**
2. Username: `phishing-deploy`
3. Attach policies directly:
   - `AmazonEC2FullAccess`
   - `AmazonVPCFullAccess`
4. Create the user, then go to **Security credentials → Create access key**
5. Choose "Command Line Interface (CLI)", download the CSV

### Enable MFA (Recommended)

1. Go to **IAM → Users → phishing-deploy → Security credentials**
2. Click **Assign MFA device** and follow the steps with an authenticator app

### Configure AWS CLI

```bash
aws configure
# AWS Access Key ID: <from CSV>
# AWS Secret Access Key: <from CSV>
# Default region: eu-west-3        (Paris — or your preferred region)
# Default output format: json
```

Verify:

```bash
aws sts get-caller-identity
```

## 3. VPC & Networking

Use the **default VPC** — every AWS account has one per region with:
- Internet Gateway already attached
- Public subnets with auto-assign public IP
- Route table configured for internet access

Verify your default VPC exists:

```bash
aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" --output text
```

## 4. Security Group

Create a security group that allows SSH (from your IP only) and HTTP from anywhere.

### Find Your Public IP

```bash
curl -s https://checkip.amazonaws.com
```

### Create the Security Group

```bash
# Get default VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" --output text)

# Create security group
SG_ID=$(aws ec2 create-security-group \
    --group-name phishing-app-sg \
    --description "Phishing awareness app - SSH + HTTP" \
    --vpc-id "$VPC_ID" \
    --query "GroupId" --output text)

echo "Security Group ID: $SG_ID"

# Allow SSH from your IP only (replace YOUR_IP)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port 22 \
    --cidr "YOUR_IP/32"

# Allow HTTP from anywhere
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port 80 \
    --cidr "0.0.0.0/0"

# Allow HTTPS from anywhere (for future SSL)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port 443 \
    --cidr "0.0.0.0/0"
```

> **Console alternative**: EC2 → Security Groups → Create security group, then add the 3 inbound rules manually.

## 5. Key Pair

Create an SSH key pair to connect to your instance.

```bash
aws ec2 create-key-pair \
    --key-name phishing-app-key \
    --key-type ed25519 \
    --query "KeyMaterial" --output text > phishing-app-key.pem

# Restrict permissions (Linux/macOS)
chmod 400 phishing-app-key.pem

# On Windows PowerShell:
# icacls phishing-app-key.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

> **Console alternative**: EC2 → Key Pairs → Create key pair (ED25519, .pem format). Download automatically.

## 6. Launch EC2 Instance

### Find the Latest Amazon Linux 2023 AMI

```bash
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023*-x86_64" \
              "Name=state,Values=available" \
    --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" \
    --output text)

echo "AMI ID: $AMI_ID"
```

### Launch the Instance

```bash
# Get a subnet ID from the default VPC
SUBNET_ID=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "Subnets[0].SubnetId" --output text)

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type t2.micro \
    --key-name phishing-app-key \
    --security-group-ids "$SG_ID" \
    --subnet-id "$SUBNET_ID" \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
    --user-data file://aws/user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=phishing-app}]' \
    --query "Instances[0].InstanceId" --output text)

echo "Instance ID: $INSTANCE_ID"
```

### Wait for the Instance to Start

```bash
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# Get the public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query "Reservations[0].Instances[0].PublicIpAddress" --output text)

echo "Public IP: $PUBLIC_IP"
```

> **Console alternative**: EC2 → Launch instance → Select Amazon Linux 2023, t2.micro, your key pair, your security group. Under Advanced details, paste the contents of `aws/user-data.sh` into the User data field.

## 7. Connect via SSH

Wait ~2 minutes for user-data to finish installing Docker, then:

```bash
ssh -i phishing-app-key.pem ec2-user@$PUBLIC_IP
```

Verify Docker is running:

```bash
docker --version
docker compose version
```

If `docker` gives a permission error, log out and back in (the group change needs a new session):

```bash
exit
ssh -i phishing-app-key.pem ec2-user@$PUBLIC_IP
```

## 8. Deploy the Application

### Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/master-Project-Phishing.git
cd master-Project-Phishing
```

### Configure Environment

```bash
# Copy the example env file
cp env.example .env

# Generate a random SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s/change-me-to-a-random-string/$SECRET_KEY/" .env

# Verify
cat .env
```

### Build and Start

```bash
docker compose up -d --build
```

This builds the Flask image, starts Gunicorn, and starts Nginx. First build takes ~1-2 minutes.

### Seed the Database

```bash
docker compose exec web python seed.py
```

### Verify

```bash
# Check containers are running
docker compose ps

# Check logs
docker compose logs web
docker compose logs nginx
```

Open `http://<PUBLIC_IP>` in your browser. Login with `admin` / `admin123`.

## 9. Elastic IP (Optional — Recommended)

Without an Elastic IP, the public IP changes every time you stop/start the instance.

```bash
# Allocate an Elastic IP
ALLOC_ID=$(aws ec2 allocate-address \
    --query "AllocationId" --output text)

# Associate it with your instance
aws ec2 associate-address \
    --instance-id "$INSTANCE_ID" \
    --allocation-id "$ALLOC_ID"

# Get the Elastic IP
ELASTIC_IP=$(aws ec2 describe-addresses \
    --allocation-ids "$ALLOC_ID" \
    --query "Addresses[0].PublicIp" --output text)

echo "Elastic IP: $ELASTIC_IP"
```

> Elastic IPs are **free while associated** to a running instance. You are charged if the instance is stopped or the IP is unassociated.

## 10. Domain + SSL (Optional)

If you have a domain name, you can add HTTPS with Let's Encrypt.

### Point Your Domain

Add an **A record** in your DNS provider pointing to your Elastic IP.

### Install Certbot on EC2

```bash
sudo dnf install -y certbot python3-certbot-nginx

sudo certbot --nginx -d yourdomain.com
```

Certbot will automatically modify the Nginx config to handle HTTPS.

> For Docker-based SSL, you can mount the certbot certificates into the Nginx container and update `nginx.conf` to listen on port 443.

## 11. Maintenance

### Update the Application

```bash
cd master-Project-Phishing
git pull
docker compose up -d --build
```

### Backup SQLite Database

```bash
# Copy from Docker volume to host
docker compose exec web cp /data/app.db /data/app.db.backup
docker cp $(docker compose ps -q web):/data/app.db.backup ./app.db.backup

# Download to your local machine (from your local terminal)
scp -i phishing-app-key.pem ec2-user@$PUBLIC_IP:~/master-Project-Phishing/app.db.backup .
```

### View Logs

```bash
docker compose logs -f          # All services
docker compose logs -f web      # Flask only
docker compose logs -f nginx    # Nginx only
```

### Restart Services

```bash
docker compose restart          # Restart all
docker compose restart web      # Restart Flask only
```

### Stop / Start

```bash
docker compose down             # Stop and remove containers (data persists in volume)
docker compose up -d            # Start again
```

## 12. Troubleshooting

| Problem | Solution |
|---------|----------|
| `docker: permission denied` | Log out and SSH back in, or run `newgrp docker` |
| Port 80 not reachable | Check Security Group allows HTTP (port 80) from 0.0.0.0/0 |
| `502 Bad Gateway` from Nginx | Check `docker compose logs web` — Gunicorn may have crashed |
| Database is empty after deploy | Run `docker compose exec web python seed.py` |
| Instance stops unexpectedly | Check if you exceeded Free Tier hours (750h/month) |
| `user-data.sh` didn't run | Check `/var/log/cloud-init-output.log` on the instance |
| Can't SSH to instance | Verify key pair, security group SSH rule, and that instance is running |
| Slow first load | t2.micro has limited CPU; first request may take a few seconds |
| Data lost after `docker compose down` | Data persists in the named volume. Only `docker volume rm` deletes it |

## 13. Cost Summary

| Resource | Monthly Cost (Free Tier) |
|----------|------------------------|
| EC2 t2.micro | $0 (750 hrs/mo) |
| EBS 20 GB gp3 | $0 (30 GB free) |
| Elastic IP | $0 (while associated + running) |
| Data transfer | $0 (100 GB free) |
| **Total** | **$0/month** |

> After 12 months, t2.micro costs ~$8.50/month (us-east-1). Consider stopping the instance when not in use.

## 14. Clean Up (When Done)

To avoid charges, terminate everything when you no longer need the deployment:

```bash
# Terminate EC2 instance
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID"

# Release Elastic IP (if allocated)
aws ec2 release-address --allocation-id "$ALLOC_ID"

# Delete security group (after instance is terminated)
aws ec2 delete-security-group --group-id "$SG_ID"

# Delete key pair
aws ec2 delete-key-pair --key-name phishing-app-key
rm phishing-app-key.pem
```
