from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
    aws_rds as rds,
    aws_ecr as ecr,
    aws_iam as iam,
)
from constructs import Construct


class KnowflowStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(
            self,
            "KnowflowVPC",
            cidr="10.0.0.0/16",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateECS",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateDB",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=24,
                ),
            ],
        )

        alb_sg = ec2.SecurityGroup(self, "ALB-SG", vpc=vpc)
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))

        ecs_sg = ec2.SecurityGroup(self, "ECS-SG", vpc=vpc)

        rds_sg = ec2.SecurityGroup(self, "RDS-SG", vpc=vpc)
        rds_sg.add_ingress_rule(ecs_sg, ec2.Port.tcp(5432))

        app_secrets = secretsmanager.Secret(
            self, "AppSecrets", secret_name="knowflow-app-secrets"
        )

        fastapi_repo = ecr.Repository(self, "FastAPIRepo")
        neo4j_repo = ecr.Repository(self, "Neo4jRepo")

        ecs_task_role = iam.Role(
            self,
            "EcsTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        ecs_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[app_secrets.secret_arn],
            )
        )

        ecs_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
                resources=[
                    "arn:aws:s3:::your-s3-bucket",
                    "arn:aws:s3:::your-s3-bucket/*",
                ],
            )
        )

        cluster = ecs.Cluster(self, "KnowflowCluster", vpc=vpc)

        postgres = rds.DatabaseInstance(
            self,
            "PostgresDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_3
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateDB"),
            credentials=rds.Credentials.from_generated_secret("postgres"),
            allocated_storage=20,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL
            ),
            security_groups=[rds_sg],
            publicly_accessible=False,
            multi_az=False,
            removal_policy=RemovalPolicy.DESTROY,
        )

        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FastAPIService",
            cluster=cluster,
            cpu=512,
            desired_count=1,
            memory_limit_mib=1024,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(fastapi_repo),
                container_port=8000,
                enable_logging=True,
                task_role=ecs_task_role,
                environment={
                    "ENVIRONMENT": "production",
                },
            ),
            security_groups=[ecs_sg],
        )

        neo4j_task_definition = ecs.FargateTaskDefinition(
            self,
            "Neo4jTaskDef",
            cpu=512,
            memory_limit_mib=1024,
            task_role=ecs_task_role,
        )

        neo4j_container = neo4j_task_definition.add_container(
            "Neo4jContainer",
            image=ecs.ContainerImage.from_registry("neo4j:5.19"),
            environment={"NEO4J_AUTH": "neo4j/password"},
            port_mappings=[ecs.PortMapping(container_port=7687)],
        )

        ecs.FargateService(
            self,
            "Neo4jService",
            cluster=cluster,
            desired_count=1,
            task_definition=neo4j_task_definition,
            security_groups=[ecs_sg],
            assign_public_ip=False,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateECS"),
        )
