.PHONY: lambda test lint

lambda:
	./scripts/build_lambda.sh

test:
	pytest tests/ -v

lint:
	flake8 app/ --max-line-length=120 --exclude=__pycache__
