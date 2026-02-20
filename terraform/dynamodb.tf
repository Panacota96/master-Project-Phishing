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

