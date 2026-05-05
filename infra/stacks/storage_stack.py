"""S3 storage stack — product images bucket."""

import aws_cdk
import aws_cdk.aws_s3 as s3
import constructs


class StorageStack(aws_cdk.Stack):
    def __init__(
        self,
        scope: constructs.Construct,
        construct_id: str,
        **kwargs: aws_cdk.StackProps,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.products_bucket = s3.Bucket(
            self,
            "ProductsBucket",
            bucket_name=f"agroconecta-products-{self.account}-{self.region}",
            versioned=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            public_read_access=True,
            removal_policy=aws_cdk.RemovalPolicy.RETAIN,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                )
            ],
        )
