"""RDS PostgreSQL stack — private VPC, t4g.micro."""

import aws_cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_rds as rds
import aws_cdk.aws_secretsmanager as secretsmanager
import constructs


class DatabaseStack(aws_cdk.Stack):
    def __init__(
        self,
        scope: constructs.Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        **kwargs: aws_cdk.StackProps,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.db_secret = secretsmanager.Secret(
            self,
            "AgroConectaDbSecret",
            secret_name="agroconecta/db/credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "agroconecta"}',
                generate_string_key="password",
                exclude_characters='"@/\\',
            ),
        )

        self.db_security_group = ec2.SecurityGroup(
            self,
            "DbSecurityGroup",
            vpc=vpc,
            description="Security group for AgroConecta RDS",
            allow_all_outbound=False,
        )

        self.cluster = rds.DatabaseInstance(
            self,
            "AgroConectaDb",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.db_security_group],
            credentials=rds.Credentials.from_secret(self.db_secret),
            database_name="agroconecta",
            backup_retention=aws_cdk.Duration.days(7),
            deletion_protection=True,
            storage_encrypted=True,
            multi_az=False,
        )
