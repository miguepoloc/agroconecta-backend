"""CDK App entry point — AgroConecta infrastructure."""

import aws_cdk

from infra.stacks import api_stack, dynamo_stack, iam_stack, storage_stack

app = aws_cdk.App()
env = aws_cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-east-1",
)

storage = storage_stack.StorageStack(app, "AgroConectaStorage", env=env)
dynamo = dynamo_stack.DynamoStack(app, "AgroConectaDynamo", env=env)
iam = iam_stack.IamStack(app, "AgroConectaIam", env=env)
api = api_stack.ApiStack(app, "AgroConectaApi", dynamo_stack=dynamo, env=env)

app.synth()
