.PHONY: install dev test lint format migrate deploy lambda-build localstack-setup localstack-reset

install:
	uv sync

dev:
	uv run fastapi dev src/entrypoints/app.py --host 0.0.0.0 --port 8000

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

migrate:
	uv run alembic upgrade head

migrate-create:
	uv run alembic revision --autogenerate -m "$(name)"

migrate-down:
	uv run alembic downgrade -1

db-up:
	docker compose up db -d

db-test-up:
	docker compose up db_test -d

infra-up:
	docker compose up -d

infra-down:
	docker compose down

deploy:
	cd infra && cdk deploy --all

# Empaqueta solo las deps mínimas + src en lambda.zip compilado para Linux x86_64
# (boto3 ya viene incluido en el runtime de Lambda)
lambda-build:
	rm -rf .lambda_pkg lambda.zip
	pip install \
		--platform manylinux2014_x86_64 \
		--target .lambda_pkg/ \
		--implementation cp \
		--python-version 312 \
		--only-binary=:all: \
		-r lambda-requirements.txt --quiet
	cp -r src .lambda_pkg/
	cd .lambda_pkg && zip -r ../lambda.zip . -q
	rm -rf .lambda_pkg
	@echo "lambda.zip listo ($$(du -sh lambda.zip | cut -f1))"

# Variables de entorno para la Lambda — host.docker.internal apunta al host desde dentro del contenedor
LAMBDA_ENV = Variables={\
AWS_ENDPOINT_URL=http://host.docker.internal:4566,\
AWS_REGION=us-east-1,\
SES_SENDER_EMAIL=test@example.com,\
ENVIRONMENT=staging,\
DATABASE_URL=postgresql+asyncpg://agroconecta:agroconecta@host.docker.internal:5432/agroconecta,\
JWT_SECRET_KEY=965234055e8cfe7c38913f0f631b80113e2b18af7db1a1be769827b72aeeeb0c,\
DYNAMO_REFRESH_TOKENS_TABLE=agroconecta-refresh-tokens,\
DYNAMO_RATE_LIMITS_TABLE=agroconecta-rate-limits,\
DYNAMO_EVENTS_LOG_TABLE=agroconecta-events-log}

# Crea todos los recursos en LocalStack (corre una sola vez, o tras localstack-reset)
localstack-setup:
	@echo "=== Creando tablas DynamoDB ==="
	aws --endpoint-url=http://localhost:4566 dynamodb create-table \
		--table-name agroconecta-refresh-tokens \
		--attribute-definitions AttributeName=token_hash,AttributeType=S AttributeName=user_id,AttributeType=S \
		--key-schema AttributeName=token_hash,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		--global-secondary-indexes '[{"IndexName":"by-user-id","KeySchema":[{"AttributeName":"user_id","KeyType":"HASH"}],"Projection":{"ProjectionType":"KEYS_ONLY"}}]' \
		2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 dynamodb update-time-to-live \
		--table-name agroconecta-refresh-tokens \
		--time-to-live-specification Enabled=true,AttributeName=expires_at 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 dynamodb create-table \
		--table-name agroconecta-rate-limits \
		--attribute-definitions AttributeName=key,AttributeType=S \
		--key-schema AttributeName=key,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 dynamodb update-time-to-live \
		--table-name agroconecta-rate-limits \
		--time-to-live-specification Enabled=true,AttributeName=expires_at 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 dynamodb create-table \
		--table-name agroconecta-events-log \
		--attribute-definitions AttributeName=aggregate_id,AttributeType=S AttributeName=occurred_on,AttributeType=S AttributeName=event_type,AttributeType=S \
		--key-schema AttributeName=aggregate_id,KeyType=HASH AttributeName=occurred_on,KeyType=RANGE \
		--billing-mode PAY_PER_REQUEST \
		--global-secondary-indexes '[{"IndexName":"by-event-type","KeySchema":[{"AttributeName":"event_type","KeyType":"HASH"},{"AttributeName":"occurred_on","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
		2>/dev/null || true
	@echo "=== Creando bus de eventos ==="
	aws --endpoint-url=http://localhost:4566 events create-event-bus --name agroconecta-events 2>/dev/null || true
	@echo "=== Verificando email en SES ==="
	aws --endpoint-url=http://localhost:4566 ses verify-email-identity --email-address test@example.com
	@echo "=== Creando Lambda ==="
	aws --endpoint-url=http://localhost:4566 lambda create-function \
		--function-name agroconecta-event-handler \
		--runtime python3.12 \
		--handler src.entrypoints.event_lambda_handler.handler \
		--zip-file fileb://lambda.zip \
		--role arn:aws:iam::000000000000:role/dummy \
		--timeout 30 \
		--environment "$(LAMBDA_ENV)" \
		2>/dev/null || \
	aws --endpoint-url=http://localhost:4566 lambda update-function-code \
		--function-name agroconecta-event-handler \
		--zip-file fileb://lambda.zip
	@echo "=== Creando regla EventBridge → Lambda ==="
	aws --endpoint-url=http://localhost:4566 events put-rule \
		--name user-registered-rule \
		--event-bus-name agroconecta-events \
		--event-pattern '{"source":["agroconecta.backend"],"detail-type":["UserRegistered"]}' \
		--state ENABLED
	aws --endpoint-url=http://localhost:4566 events put-targets \
		--rule user-registered-rule \
		--event-bus-name agroconecta-events \
		--targets '[{"Id":"notification-lambda","Arn":"arn:aws:lambda:us-east-1:000000000000:function:agroconecta-event-handler"}]'
	aws --endpoint-url=http://localhost:4566 lambda add-permission \
		--function-name agroconecta-event-handler \
		--statement-id eventbridge-invoke \
		--action lambda:InvokeFunction \
		--principal events.amazonaws.com \
		--source-arn arn:aws:events:us-east-1:000000000000:rule/agroconecta-events/user-registered-rule \
		2>/dev/null || true
	@echo "=== LocalStack listo ==="

# Borra y recrea todos los recursos en LocalStack
localstack-reset:
	aws --endpoint-url=http://localhost:4566 dynamodb delete-table --table-name agroconecta-refresh-tokens 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 dynamodb delete-table --table-name agroconecta-rate-limits 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 dynamodb delete-table --table-name agroconecta-events-log 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 lambda delete-function --function-name agroconecta-event-handler 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 events remove-targets --rule user-registered-rule --event-bus-name agroconecta-events --ids notification-lambda 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 events delete-rule --name user-registered-rule --event-bus-name agroconecta-events 2>/dev/null || true
	aws --endpoint-url=http://localhost:4566 events delete-event-bus --name agroconecta-events 2>/dev/null || true
	$(MAKE) localstack-setup
