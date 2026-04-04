# ─── Users Table ──────────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "users" {
  name         = "${local.prefix}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"

  attribute {
    name = "username"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "group"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "group-index"
    hash_key        = "group"
    range_key       = "username"
    projection_type = "ALL"
  }
}

# ─── Quizzes Table ────────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "quizzes" {
  name         = "${local.prefix}-quizzes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "quiz_id"

  attribute {
    name = "quiz_id"
    type = "S"
  }
}

# ─── Attempts Table ───────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "attempts" {
  name         = "${local.prefix}-attempts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"
  range_key    = "quiz_id"

  attribute {
    name = "username"
    type = "S"
  }

  attribute {
    name = "quiz_id"
    type = "S"
  }

  attribute {
    name = "completed_at"
    type = "S"
  }

  attribute {
    name = "group"
    type = "S"
  }

  global_secondary_index {
    name            = "quiz-index"
    hash_key        = "quiz_id"
    range_key       = "completed_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "group-index"
    hash_key        = "group"
    range_key       = "completed_at"
    projection_type = "ALL"
  }
}

# ─── Responses Table ──────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "responses" {
  name         = "${local.prefix}-responses"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username_quiz_id"
  range_key    = "question_id"

  attribute {
    name = "username_quiz_id"
    type = "S"
  }

  attribute {
    name = "question_id"
    type = "S"
  }

  attribute {
    name = "quiz_question_id"
    type = "S"
  }

  attribute {
    name = "username"
    type = "S"
  }

  global_secondary_index {
    name            = "quiz-question-index"
    hash_key        = "quiz_question_id"
    range_key       = "username"
    projection_type = "ALL"
  }
}

# ─── Inspector Attempts Table ────────────────────────────────────────────────

resource "aws_dynamodb_table" "inspector_attempts" {
  name         = "${local.prefix}-inspector-attempts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"
  range_key    = "submitted_at"

  attribute {
    name = "username"
    type = "S"
  }

  attribute {
    name = "submitted_at"
    type = "S"
  }

  attribute {
    name = "group"
    type = "S"
  }

  attribute {
    name = "email_file"
    type = "S"
  }

  global_secondary_index {
    name            = "group-index"
    hash_key        = "group"
    range_key       = "submitted_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email_file"
    range_key       = "submitted_at"
    projection_type = "ALL"
  }
}

# ─── Inspector Attempts Table (Anonymous) ────────────────────────────────────

resource "aws_dynamodb_table" "inspector_attempts_anon" {
  name         = "${local.prefix}-inspector-attempts-anon"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "attempt_id"
  range_key    = "submitted_at"

  attribute {
    name = "attempt_id"
    type = "S"
  }

  attribute {
    name = "submitted_at"
    type = "S"
  }
}

# ─── Bugs Table ────────────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "bugs" {
  name         = "${local.prefix}-bugs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "bug_id"

  attribute {
    name = "bug_id"
    type = "S"
  }
}

# ─── Answer Key Overrides Table ───────────────────────────────────────────────

resource "aws_dynamodb_table" "answer_key_overrides" {
  name         = "${local.prefix}-answer-key-overrides"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email_file"

  attribute {
    name = "email_file"
    type = "S"
  }
}

# ─── Cohort Tokens Table ───────────────────────────────────────────────────────

resource "aws_dynamodb_table" "cohort_tokens" {
  name         = "${local.prefix}-cohort-tokens"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token"

  attribute {
    name = "token"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}

# ─── Threat Cache (OpenPhish) ─────────────────────────────────────────────────

resource "aws_dynamodb_table" "threat_cache" {
  name         = "${local.prefix}-threat-cache"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "cache_key"

  attribute {
    name = "cache_key"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

# ─── Campaigns ────────────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "campaigns" {
  name         = "${local.prefix}-campaigns"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "campaign_id"

  attribute {
    name = "campaign_id"
    type = "S"
  }

  attribute {
    name = "cohort"
    type = "S"
  }

  global_secondary_index {
    name            = "cohort-index"
    hash_key        = "cohort"
    projection_type = "ALL"
  }
}

# ─── Campaign Events ─────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "campaign_events" {
  name         = "${local.prefix}-campaign-events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "campaign_id"
  range_key    = "event_id"

  attribute {
    name = "campaign_id"
    type = "S"
  }

  attribute {
    name = "event_id"
    type = "S"
  }

  attribute {
    name = "event_type"
    type = "S"
  }

  global_secondary_index {
    name            = "event-type-index"
    hash_key        = "event_type"
    range_key       = "event_id"
    projection_type = "ALL"
  }
}
