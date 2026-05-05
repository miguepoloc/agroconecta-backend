"""IAM stack — OIDC provider and GitHub Actions deployment role."""

import aws_cdk
import aws_cdk.aws_iam as iam
import constructs


class IamStack(aws_cdk.Stack):
    def __init__(
        self,
        scope: constructs.Construct,
        construct_id: str,
        github_org: str = "miguepoloc",
        github_repo: str = "agroconecta-backend",
        **kwargs: aws_cdk.StackProps,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        provider = iam.OpenIdConnectProvider(
            self,
            "GithubOidcProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        role = iam.Role(
            self,
            "GithubActionsRole",
            role_name="agroconecta-github-actions",
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": (
                            f"repo:{github_org}/{github_repo}:*"
                        )
                    }
                },
            ),
        )

        # AdministratorAccess for MVP — scope down per-service in production
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
        )

        aws_cdk.CfnOutput(
            self,
            "GithubRoleArn",
            value=role.role_arn,
            description="ARN to set as AWS_ROLE_ARN in GitHub Secrets",
        )
