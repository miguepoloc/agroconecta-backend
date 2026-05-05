"""DynamoDB adapter for login rate limiting."""

import time
import typing

import aioboto3
import botocore.exceptions


class DynamoRateLimitAdapter:
    def __init__(
        self,
        table_name: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ) -> None:
        self._table_name = table_name
        self._session = aioboto3.Session()
        self._kwargs: dict[str, typing.Any] = {"region_name": region}
        if endpoint_url:
            self._kwargs["endpoint_url"] = endpoint_url

    async def increment(self, key: str, window_seconds: int = 900) -> int:
        """Atomically increment the counter for key; returns the new count."""
        expires_at = int(time.time()) + window_seconds
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            try:
                response = await table.update_item(
                    Key={"key": key},
                    UpdateExpression=(
                        "SET #cnt = if_not_exists(#cnt, :zero) + :one, "
                        "expires_at = if_not_exists(expires_at, :exp)"
                    ),
                    ExpressionAttributeNames={"#cnt": "count"},
                    ExpressionAttributeValues={
                        ":zero": 0,
                        ":one": 1,
                        ":exp": expires_at,
                    },
                    ReturnValues="UPDATED_NEW",
                )
                return int(response["Attributes"]["count"])
            except botocore.exceptions.ClientError:
                return 1

    async def is_blocked(self, key: str, max_attempts: int = 5) -> bool:
        """Return True if the key has exceeded max_attempts within its window."""
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            response = await table.get_item(Key={"key": key})
            item = response.get("Item")
            if item is None:
                return False
            if int(item.get("expires_at", 0)) <= int(time.time()):
                return False
            return int(item.get("count", 0)) >= max_attempts

    async def reset(self, key: str) -> None:
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            await table.delete_item(Key={"key": key})
