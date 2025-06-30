"""
Pulumi Infrastructure as Code for Health Monitoring System
Deploys AWS resources for the federated health monitoring platform
"""

import pulumi
import pulumi_aws as aws
import pulumi_random as random
import json
from typing import Dict, Any

# Get configuration
config = pulumi.Config()
environment = config.get("environment", "development")
project_name = "health-monitoring"

# Create tags for all resources
common_tags = {
    "Project": project_name,
    "Environment": environment,
    "ManagedBy": "Pulumi"
}

# Create VPC and networking
vpc = aws.ec2.Vpc(
    f"{project_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**common_tags, "Name": f"{project_name}-vpc"}
)

# Create internet gateway
igw = aws.ec2.InternetGateway(
    f"{project_name}-igw",
    vpc_id=vpc.id,
    tags={**common_tags, "Name": f"{project_name}-igw"}
)

# Create public subnets
public_subnet_1 = aws.ec2.Subnet(
    f"{project_name}-public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,
    tags={**common_tags, "Name": f"{project_name}-public-subnet-1"}
)

public_subnet_2 = aws.ec2.Subnet(
    f"{project_name}-public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-west-2b",
    map_public_ip_on_launch=True,
    tags={**common_tags, "Name": f"{project_name}-public-subnet-2"}
)

# Create private subnets
private_subnet_1 = aws.ec2.Subnet(
    f"{project_name}-private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="us-west-2a",
    tags={**common_tags, "Name": f"{project_name}-private-subnet-1"}
)

private_subnet_2 = aws.ec2.Subnet(
    f"{project_name}-private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="us-west-2b",
    tags={**common_tags, "Name": f"{project_name}-private-subnet-2"}
)

# Create NAT gateway
nat_eip = aws.ec2.Eip(f"{project_name}-nat-eip", domain="vpc")

nat_gateway = aws.ec2.NatGateway(
    f"{project_name}-nat-gateway",
    allocation_id=nat_eip.id,
    subnet_id=public_subnet_1.id,
    tags={**common_tags, "Name": f"{project_name}-nat-gateway"}
)

# Create route tables
public_route_table = aws.ec2.RouteTable(
    f"{project_name}-public-rt",
    vpc_id=vpc.id,
    tags={**common_tags, "Name": f"{project_name}-public-rt"}
)

private_route_table = aws.ec2.RouteTable(
    f"{project_name}-private-rt",
    vpc_id=vpc.id,
    tags={**common_tags, "Name": f"{project_name}-private-rt"}
)

# Create routes
aws.ec2.Route(
    f"{project_name}-public-route",
    route_table_id=public_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id
)

aws.ec2.Route(
    f"{project_name}-private-route",
    route_table_id=private_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=nat_gateway.id
)

# Associate route tables with subnets
aws.ec2.RouteTableAssociation(
    f"{project_name}-public-rt-assoc-1",
    subnet_id=public_subnet_1.id,
    route_table_id=public_route_table.id
)

aws.ec2.RouteTableAssociation(
    f"{project_name}-public-rt-assoc-2",
    subnet_id=public_subnet_2.id,
    route_table_id=public_route_table.id
)

aws.ec2.RouteTableAssociation(
    f"{project_name}-private-rt-assoc-1",
    subnet_id=private_subnet_1.id,
    route_table_id=private_route_table.id
)

aws.ec2.RouteTableAssociation(
    f"{project_name}-private-rt-assoc-2",
    subnet_id=private_subnet_2.id,
    route_table_id=private_route_table.id
)

# Create security groups
# Application Load Balancer security group
alb_security_group = aws.ec2.SecurityGroup(
    f"{project_name}-alb-sg",
    vpc_id=vpc.id,
    description="Security group for Application Load Balancer",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-alb-sg"}
)

# ECS security group
ecs_security_group = aws.ec2.SecurityGroup(
    f"{project_name}-ecs-sg",
    vpc_id=vpc.id,
    description="Security group for ECS tasks",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8080,
            to_port=8080,
            security_groups=[alb_security_group.id]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5000,
            to_port=5000,
            security_groups=[alb_security_group.id]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-ecs-sg"}
)

# RDS security group
rds_security_group = aws.ec2.SecurityGroup(
    f"{project_name}-rds-sg",
    vpc_id=vpc.id,
    description="Security group for RDS database",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3306,
            to_port=3306,
            security_groups=[ecs_security_group.id]
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-rds-sg"}
)

# ElastiCache security group
redis_security_group = aws.ec2.SecurityGroup(
    f"{project_name}-redis-sg",
    vpc_id=vpc.id,
    description="Security group for Redis ElastiCache",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=6379,
            to_port=6379,
            security_groups=[ecs_security_group.id]
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-redis-sg"}
)

# Create S3 bucket for model storage
model_storage_bucket = aws.s3.Bucket(
    f"{project_name}-models-{environment}",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256"
            )
        )
    ),
    tags=common_tags
)

# Block public access to S3 bucket
aws.s3.BucketPublicAccessBlock(
    f"{project_name}-models-pab",
    bucket=model_storage_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True
)

# Create RDS subnet group
rds_subnet_group = aws.rds.SubnetGroup(
    f"{project_name}-rds-subnet-group",
    subnet_ids=[private_subnet_1.id, private_subnet_2.id],
    tags={**common_tags, "Name": f"{project_name}-rds-subnet-group"}
)

# Generate random password for RDS
rds_password = random.RandomPassword(
    f"{project_name}-rds-password",
    length=16,
    special=True,
    override_special="!#$%&*()-_=+[]{}<>:?"
)

# Create RDS instance
rds_instance = aws.rds.Instance(
    f"{project_name}-mysql",
    allocated_storage=20,
    max_allocated_storage=100,
    storage_type="gp2",
    engine="mysql",
    engine_version="8.0",
    instance_class="db.t3.micro" if environment == "development" else "db.r5.large",
    db_name="health_monitoring",
    username="admin",
    password=rds_password.result,
    parameter_group_name="default.mysql8.0",
    db_subnet_group_name=rds_subnet_group.name,
    vpc_security_group_ids=[rds_security_group.id],
    backup_retention_period=7,
    backup_window="03:00-04:00",
    maintenance_window="Mon:04:00-Mon:05:00",
    storage_encrypted=True,
    skip_final_snapshot=environment == "development",
    deletion_protection=environment == "production",
    tags={**common_tags, "Name": f"{project_name}-mysql"}
)

# Create ElastiCache subnet group
redis_subnet_group = aws.elasticache.SubnetGroup(
    f"{project_name}-redis-subnet-group",
    subnet_ids=[private_subnet_1.id, private_subnet_2.id]
)

# Create ElastiCache Redis cluster
redis_cluster = aws.elasticache.ReplicationGroup(
    f"{project_name}-redis",
    description="Redis cluster for health monitoring",
    node_type="cache.t3.micro" if environment == "development" else "cache.r6g.large",
    port=6379,
    parameter_group_name="default.redis7",
    num_cache_clusters=2,
    automatic_failover_enabled=True,
    multi_az_enabled=True,
    subnet_group_name=redis_subnet_group.name,
    security_group_ids=[redis_security_group.id],
    at_rest_encryption_enabled=True,
    transit_encryption_enabled=True,
    tags=common_tags
)

# Create ECS cluster
ecs_cluster = aws.ecs.Cluster(
    f"{project_name}-cluster",
    tags=common_tags
)

# Create ECS execution role
ecs_execution_role = aws.iam.Role(
    f"{project_name}-ecs-execution-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            }
        }]
    }),
    tags=common_tags
)

# Attach managed policy to execution role
aws.iam.RolePolicyAttachment(
    f"{project_name}-ecs-execution-role-policy",
    role=ecs_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)

# Create ECS task role
ecs_task_role = aws.iam.Role(
    f"{project_name}-ecs-task-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            }
        }]
    }),
    tags=common_tags
)

# Create policy for S3 access
s3_policy = aws.iam.Policy(
    f"{project_name}-s3-policy",
    policy=model_storage_bucket.arn.apply(lambda arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": f"{arn}/*"
        }, {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": arn
        }]
    }))
)

# Attach S3 policy to task role
aws.iam.RolePolicyAttachment(
    f"{project_name}-ecs-task-s3-policy",
    role=ecs_task_role.name,
    policy_arn=s3_policy.arn
)

# Create CloudWatch log group
log_group = aws.cloudwatch.LogGroup(
    f"{project_name}-logs",
    retention_in_days=7 if environment == "development" else 30,
    tags=common_tags
)

# Create Application Load Balancer
alb = aws.lb.LoadBalancer(
    f"{project_name}-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_security_group.id],
    subnets=[public_subnet_1.id, public_subnet_2.id],
    tags=common_tags
)

# Create target groups
backend_target_group = aws.lb.TargetGroup(
    f"{project_name}-backend-tg",
    port=8080,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        healthy_threshold=2,
        interval=30,
        matcher="200",
        path="/actuator/health",
        port="traffic-port",
        protocol="HTTP",
        timeout=5,
        unhealthy_threshold=2
    ),
    tags=common_tags
)

federation_target_group = aws.lb.TargetGroup(
    f"{project_name}-federation-tg",
    port=5000,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        healthy_threshold=2,
        interval=30,
        matcher="200",
        path="/health",
        port="traffic-port",
        protocol="HTTP",
        timeout=5,
        unhealthy_threshold=2
    ),
    tags=common_tags
)

# Create ALB listeners
alb_listener = aws.lb.Listener(
    f"{project_name}-alb-listener",
    load_balancer_arn=alb.arn,
    port="80",
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=backend_target_group.arn
    )]
)

# Create listener rules for federation server
aws.lb.ListenerRule(
    f"{project_name}-federation-rule",
    listener_arn=alb_listener.arn,
    priority=100,
    actions=[aws.lb.ListenerRuleActionArgs(
        type="forward",
        target_group_arn=federation_target_group.arn
    )],
    conditions=[aws.lb.ListenerRuleConditionArgs(
        path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
            values=["/federation/*"]
        )
    )]
)

# Create IoT Core thing type
iot_thing_type = aws.iot.ThingType(
    f"{project_name}-edge-device",
    name=f"{project_name}-edge-device",
    properties=aws.iot.ThingTypePropertiesArgs(
        description="Health monitoring edge devices"
    ),
    tags=common_tags
)

# Create IoT policy
iot_policy_document = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "iot:Connect",
            "iot:Publish",
            "iot:Subscribe",
            "iot:Receive"
        ],
        "Resource": "*"
    }]
})

iot_policy = aws.iot.Policy(
    f"{project_name}-iot-policy",
    name=f"{project_name}-iot-policy",
    policy=iot_policy_document
)

# Create Lambda function for IoT data processing
lambda_role = aws.iam.Role(
    f"{project_name}-lambda-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            }
        }]
    }),
    tags=common_tags
)

# Attach basic execution role to Lambda
aws.iam.RolePolicyAttachment(
    f"{project_name}-lambda-basic-execution",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
)

# Create Lambda function
iot_lambda = aws.lambda_.Function(
    f"{project_name}-iot-processor",
    runtime="python3.9",
    role=lambda_role.arn,
    handler="index.handler",
    code=pulumi.AssetArchive({
        "index.py": pulumi.StringAsset("""
import json
import boto3

def handler(event, context):
    print(f"Received IoT event: {json.dumps(event)}")
    
    # Process IoT data here
    # Forward to federation server or trigger alerts
    
    return {
        'statusCode': 200,
        'body': json.dumps('IoT data processed successfully')
    }
        """)
    }),
    tags=common_tags
)

# Export important values
pulumi.export("vpc_id", vpc.id)
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("rds_endpoint", rds_instance.endpoint)
pulumi.export("redis_endpoint", redis_cluster.primary_endpoint_address)
pulumi.export("s3_bucket", model_storage_bucket.bucket)
pulumi.export("ecs_cluster", ecs_cluster.name)
pulumi.export("log_group", log_group.name)