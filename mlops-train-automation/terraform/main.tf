terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda: ValidateData ---
resource "aws_lambda_function" "validate" {
  filename         = "${path.module}/lambda/validate.zip"
  function_name    = "ValidateData"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "validate.handler"
  runtime          = "python3.10"
  source_code_hash = filebase64sha256("${path.module}/lambda/validate.zip")
}

# --- Lambda: LogMetrics ---
resource "aws_lambda_function" "log_metrics" {
  filename         = "${path.module}/lambda/log_metrics.zip"
  function_name    = "LogMetrics"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "log_metrics.handler"
  runtime          = "python3.10"
  source_code_hash = filebase64sha256("${path.module}/lambda/log_metrics.zip")
}

resource "aws_lambda_permission" "allow_stepfunction_validate" {
  statement_id  = "AllowExecutionFromStepFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.validate.function_name
  principal     = "states.amazonaws.com"
}

resource "aws_lambda_permission" "allow_stepfunction_log_metrics" {
  statement_id  = "AllowExecutionFromStepFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_metrics.function_name
  principal     = "states.amazonaws.com"
}

data "aws_iam_policy_document" "stepfunction_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "stepfunction_exec" {
  name                = "${var.project_name}-stepfunction-exec"
  assume_role_policy  = data.aws_iam_policy_document.stepfunction_trust.json
}

resource "aws_iam_role_policy_attachment" "stepfunction_lambda" {
  role       = aws_iam_role.stepfunction_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
}

resource "aws_sfn_state_machine" "mlops_pipeline" {
  name     = "MLOpsPipeline"
  role_arn = aws_iam_role.stepfunction_exec.arn

  definition = jsonencode({
    Comment = "ML training pipeline: validate → log metrics"
    StartAt = "ValidateData"
    States = {
      ValidateData = {
        Type     = "Task"
        Resource = aws_lambda_function.validate.arn
        Next     = "LogMetrics"
      }
      LogMetrics = {
        Type     = "Task"
        Resource = aws_lambda_function.log_metrics.arn
        End      = true
      }
    }
  })
}

output "step_function_arn" {
  description = "ARN of the Step Function state machine (use in GitLab CI variable STEP_FUNCTION_ARN)"
  value       = aws_sfn_state_machine.mlops_pipeline.id
}

output "step_function_name" {
  description = "Name of the Step Function state machine"
  value       = aws_sfn_state_machine.mlops_pipeline.name
}
