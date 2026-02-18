.PHONY: lambda test lint validate-eml

lambda:
	./scripts/build_lambda.sh

test:
	pytest tests/ -v --junitxml=report.xml

lint:
	flake8 app/ --max-line-length=120 --exclude=__pycache__

validate-eml:
	python3 scripts/validate_eml_realism.py --root examples --allowlist examples/realism_allowlist.json --report examples/realism_report.json
