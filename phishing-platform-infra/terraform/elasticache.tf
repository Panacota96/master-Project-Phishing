# ─── Networking (Default VPC) ────────────────────────────────────────────────

data "aws_default_vpc" "default" {}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_default_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

# ─── Security Groups ─────────────────────────────────────────────────────────

resource "aws_security_group" "lambda" {
  name        = "${local.prefix}-lambda-sg"
  description = "Lambda access to Redis and outbound internet"
  vpc_id      = data.aws_default_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "redis" {
  name        = "${local.prefix}-redis-sg"
  description = "Redis access from Lambda"
  vpc_id      = data.aws_default_vpc.default.id

  ingress {
    description     = "Redis from Lambda"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ─── ElastiCache (Redis) ─────────────────────────────────────────────────────

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.prefix}-redis-subnets"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "${local.prefix}-redis"
  replication_group_description = "Redis cache for real-time dashboard + threat feed"
  engine                        = "redis"
  engine_version                = var.redis_engine_version
  node_type                     = var.redis_node_type
  number_cache_clusters         = 1
  automatic_failover_enabled    = false
  multi_az_enabled              = false
  port                          = 6379
  subnet_group_name             = aws_elasticache_subnet_group.redis.name
  security_group_ids            = [aws_security_group.redis.id]
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = false
  apply_immediately             = true
}

# ─── Outputs ─────────────────────────────────────────────────────────────────

output "redis_endpoint" {
  description = "Primary Redis endpoint (host:port)"
  value       = "${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
}
