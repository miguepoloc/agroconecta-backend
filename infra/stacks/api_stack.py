"""Lambda + API Gateway HTTP stack — no VPC, Neon PostgreSQL + DynamoDB."""

import aws_cdk
import aws_cdk.aws_apigatewayv2 as apigw
import aws_cdk.aws_apigatewayv2_integrations as apigw_integrations
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_secretsmanager as secretsmanager
import constructs

from infra.stacks.dynamo_stack import DynamoStack


class ApiStack(aws_cdk.Stack):
    def __init__(
        self,
        scope: constructs.Construct,
        construct_id: str,
        dynamo_stack: DynamoStack,
        **kwargs: aws_cdk.StackProps,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        jwt_secret = secretsmanager.Secret(
            self,
            "JwtSecret",
            secret_name="agroconecta/jwt/secret_key",
            description="JWT HS256 signing key",
        )

        # Neon PostgreSQL URL — set the secret value manually after first deploy:
        # aws secretsmanager put-secret-value --secret-id agroconecta/db/neon-url \
        #   --secret-string "postgresql+asyncpg://user:pass@ep-xxx.neon.tech/agroconecta"
        neon_secret = secretsmanager.Secret(
            self,
            "NeonDatabaseSecret",
            secret_name="agroconecta/db/neon-url",
            description="Neon PostgreSQL connection URL (asyncpg)",
        )

        self.function = lambda_.Function(
            self,
            "AgroConectaApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="src.entrypoints.lambda_handler.handler",
            code=lambda_.Code.from_asset(
                "..",
                bundling=aws_cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        (
                            "pip install uv && "
                            "uv export --no-hashes -o /tmp/requirements.txt && "
                            "pip install -r /tmp/requirements.txt -t /asset-output && "
                            "cp -r src /asset-output/"
                        ),
                    ],
                ),
            ),
            # No VPC — Lambda connects to Neon over public internet (TLS)
            architecture=lambda_.Architecture.ARM_64,
            memory_size=512,
            timeout=aws_cdk.Duration.seconds(30),
            environment={
                "ENVIRONMENT": "production",
                "AWS_REGION": self.region,
                "DYNAMO_REFRESH_TOKENS_TABLE": dynamo_stack.refresh_tokens_table.table_name,
                "DYNAMO_RATE_LIMITS_TABLE": dynamo_stack.rate_limits_table.table_name,
                "DYNAMO_EVENTS_LOG_TABLE": dynamo_stack.events_log_table.table_name,
                "JWT_SECRET_ARN": jwt_secret.secret_arn,
                "NEON_SECRET_ARN": neon_secret.secret_arn,
            },
        )

        # DynamoDB permissions
        dynamo_stack.refresh_tokens_table.grant_read_write_data(self.function)
        dynamo_stack.rate_limits_table.grant_read_write_data(self.function)
        dynamo_stack.events_log_table.grant_read_write_data(self.function)

        # Secrets Manager permissions
        jwt_secret.grant_read(self.function)
        neon_secret.grant_read(self.function)

        http_api = apigw.HttpApi(
            self,
            "AgroConectaHttpApi",
            api_name="agroconecta-api",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_headers=["Content-Type", "Authorization"],
                allow_methods=[apigw.CorsHttpMethod.ANY],
                allow_origins=["https://agroconecta.co", "http://localhost:3000"],
                max_age=aws_cdk.Duration.days(1),
            ),
        )

        integration = apigw_integrations.HttpLambdaIntegration("LambdaIntegration", self.function)
        http_api.add_routes(
            path="/{proxy+}",
            methods=[apigw.HttpMethod.ANY],
            integration=integration,
        )

        aws_cdk.CfnOutput(self, "ApiUrl", value=http_api.api_endpoint)
        aws_cdk.CfnOutput(
            self,
            "NeonSecretArn",
            value=neon_secret.secret_arn,
            description="Set Neon URL here after creating your Neon project",
        )
