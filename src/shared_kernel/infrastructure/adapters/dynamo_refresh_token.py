"""DynamoDB adapter for refresh token storage (replaces PostgreSQL refresh_tokens table)."""

import time
import typing

import aioboto3


class DynamoRefreshTokenAdapter:
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

    async def put(self, token_hash: str, user_id: str, expires_at_unix: int) -> None:
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            await table.put_item(
                Item={
                    "token_hash": token_hash,
                    "user_id": user_id,
                    "expires_at": expires_at_unix,
                    "created_at": int(time.time()),
                }
            )

    async def find_by_hash(self, token_hash: str) -> dict[str, typing.Any] | None:
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            response = await table.get_item(Key={"token_hash": token_hash})
            item = response.get("Item")
            if item is None:
                return None
            if int(item["expires_at"]) <= int(time.time()):
                return None
            return typing.cast(dict[str, typing.Any], item)

    async def delete_by_hash(self, token_hash: str) -> None:
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            await table.delete_item(Key={"token_hash": token_hash})

    async def delete_by_user(self, user_id: str) -> None:
        """Revoke all tokens for a user (logout from all devices)."""
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            response = await table.query(
                IndexName="by-user-id",
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id},
            )
            items = response.get("Items", [])
            if not items:
                return
            async with table.batch_writer() as batch:
                for item in items:
                    await batch.delete_item(Key={"token_hash": item["token_hash"]})
