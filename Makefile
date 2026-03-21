.PHONY: lambda registration-worker test lint validate-eml sync-assets

AWS_REGION ?= eu-west-3
TF_DIR ?= terraform
S3_BUCKET := $(shell terraform -chdir=$(TF_DIR) output -raw s3_bucket_name 2>/dev/null)
AWS_PROFILE_ARG := $(if $(AWS_PROFILE),--profile $(AWS_PROFILE),)
DRY_RUN_ARG := $(if $(DRY_RUN),--dryrun,)

lambda:
	./scripts/build_lambda.sh

registration-worker:
	./scripts/build_registration_worker.sh

test:
	pytest tests/ -v --junitxml=report.xml

lint:
	flake8 app/ --max-line-length=120 --exclude=__pycache__

validate-eml:
	python3 scripts/validate_eml_realism.py --root examples --allowlist examples/realism_allowlist.json --report examples/realism_report.json

sync-assets:
	@if [ -z "$(S3_BUCKET)" ]; then \
		echo "ERROR: Could not resolve S3 bucket from Terraform output. Run terraform init/apply in $(TF_DIR) or set S3_BUCKET via Terraform state."; \
		exit 1; \
	fi
	aws $(AWS_PROFILE_ARG) s3 sync "app/static/videos/" "s3://$(S3_BUCKET)/videos/" \
		--exclude "*" --include "*.mp4" \
		--region "$(AWS_REGION)" \
		$(DRY_RUN_ARG)
