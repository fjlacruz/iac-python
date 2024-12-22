#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infraestructure.lambdas.lambda_stack import LambdaStack
from infraestructure.DB.dynamo_stack import DynamoDBStack
from infraestructure.S3.lambda_s3_stack import LambdaS3Stack
from infraestructure.CICD.cicd_stack import CicdStack


app = cdk.App()


# Crear el stack de DynamoDB
#DynamoDBStack(app, "DynamoDBStack")
dynamo_stack = DynamoDBStack(app, "DynamoDBStack")

# Crear el stack del s3 para almacenar el codigo de la lambda
lambda_s3_stack = LambdaS3Stack(app, "LambdaS3Stack")

# Crear el stack de Lambda, que depende del stack de DynamoDB
lambda_stack = LambdaStack(app, "LambdaStack")

cicd_stack = CicdStack(app, "CicdStack")

# Establecer dependencia explícita
lambda_stack.add_dependency(lambda_s3_stack)
lambda_stack.add_dependency(dynamo_stack)
cicd_stack.add_dependency(lambda_stack)


app.synth()
