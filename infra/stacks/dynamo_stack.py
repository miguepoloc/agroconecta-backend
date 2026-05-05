"""DynamoDB stack — refresh tokens, rate limiting, audit event log."""

import aws_cdk
import aws_cdk.aws_dynamodb as dynamodb
import constructs


class DynamoStack(aws_cdk.Stack):
    def __init__(
        self,
        scope: constructs.Construct,
        construct_id: str,
        **kwargs: aws_cdk.StackProps,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.refresh_tokens_table = dynamodb.Table(
            self,
            "RefreshTokensTable",
            table_name="agroconecta-refresh-tokens",
            partition_key=dynamodb.Attribute(
                name="token_hash", type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="expires_at",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=aws_cdk.RemovalPolicy.RETAIN,
        )
        self.refresh_tokens_table.add_global_secondary_index(
            index_name="by-user-id",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.KEYS_ONLY,
        )

        self.rate_limits_table = dynamodb.Table(
            self,
            "RateLimitsTable",
            table_name="agroconecta-rate-limits",
            partition_key=dynamodb.Attribute(
                name="key", type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="expires_at",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
        )

        self.events_log_table = dynamodb.Table(
            self,
            "EventsLogTable",
            table_name="agroconecta-events-log",
            partition_key=dynamodb.Attribute(
                name="aggregate_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="occurred_on", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=aws_cdk.RemovalPolicy.RETAIN,
        )
        self.events_log_table.add_global_secondary_index(
            index_name="by-event-type",
            partition_key=dynamodb.Attribute(
                name="event_type", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="occurred_on", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
