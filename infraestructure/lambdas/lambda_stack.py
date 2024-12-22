from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    CfnOutput,
    aws_apigateway as apigateway,
    Fn,
)
from constructs import Construct


class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Importar el ARN y el nombre de la tabla DynamoDB
        table_arn = Fn.import_value("DynamoDBTableArn")
        table_name = Fn.import_value("DynamoDBTableName")

        # Importar el nombre y ARN del bucket S3
        bucket_name = Fn.import_value("LambdaS3BucketName")
        bucket_arn = Fn.import_value("LambdaS3BucketArn")
        
        
        # Obtener el entorno desde el contexto del stack
        environment = self.node.try_get_context("env")  # Puede ser dev, qa o prod

        # Si no se obtiene el contexto, asignar un valor predeterminado
        if environment is None:
            environment = "dev"  # Establecer un valor predeterminado si no se pasa el contexto
      
        # Establecer el nombre de la lambda
        lambda_name = f"lambda-packagecode-zip-{environment}"
        # Crear función Lambda
        lambda_function = _lambda.Function(
            self,
            "cdk-lambda-py",
            function_name=lambda_name,
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="app.lambda_handler",
            code=_lambda.Code.from_inline(
                """
                def lambda_handler(event, context):
                    return {'statusCode': 200, 'body': 'Lambda base...!!'}
                """
            ),
            environment={
                "DYNAMODB_TABLE_NAME": table_name,
                "S3_BUCKET_NAME": bucket_name,
            },
            tracing=_lambda.Tracing.ACTIVE,
        )

        # Crear alias apuntando a la versión actual
        version = lambda_function.current_version
        alias_name_ = f"{environment}"
        alias = _lambda.Alias(
            self,
            alias_name_,
            alias_name=alias_name_,
            version=version,
        )

        # Crear política personalizada para permitir acceso a DynamoDB
        dynamodb_policy = iam.PolicyStatement(
            actions=["dynamodb:*"],
            resources=[table_arn],
        )
        lambda_function.add_to_role_policy(dynamodb_policy)

        # Crear política personalizada para permitir acceso al bucket S3
        s3_policy = iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
            resources=[f"{bucket_arn}/*"],
        )
        lambda_function.add_to_role_policy(s3_policy)

        # Asignar permiso al Alias para ser invocado por el API Gateway
        alias.add_permission(
            "ApiGatewayInvokePermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
        )

        # Crear API Gateway REST con integración a la Lambda (Alias)
        rest_api = apigateway.RestApi(
            self,
            "cdk-apigateway-py",
            description="API Gateway REST para Lambda",
            endpoint_types=[apigateway.EndpointType.EDGE],
            deploy=True,
            deploy_options=apigateway.StageOptions(
                stage_name="dev",
                tracing_enabled=True,
            ),
        )

        # Crear un recurso proxy en el API Gateway
        proxy_resource = rest_api.root.add_resource("{proxy+}")
        proxy_resource.add_method(
            "ANY",
            apigateway.LambdaIntegration(alias),
            authorization_type=apigateway.AuthorizationType.NONE,
        )

        # Construir el ARN del Alias manualmente
        alias_arn = f"arn:aws:lambda:{self.region}:{self.account}:function:{lambda_function.function_name}:{alias.alias_name}"

         # Exportar el ARN y el nombre de la función Lambda
        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=lambda_function.function_arn,
            export_name="LambdaFunctionArn",
            description="ARN de la función Lambda creada.",
        )

        CfnOutput(
            self,
            "LambdaFunctionAliasArn",
            value=alias.function_arn,
            export_name="LambdaFunctionAliasArn",
            description="ARN del Alias de la función Lambda creada.",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=lambda_function.function_name,
            export_name="LambdaFunctionName",
            description="Nombre de la función Lambda creada.",
        )

        CfnOutput(
            self,
            "LambdaFunctionAliasName",
            value=alias.alias_name,
            export_name="LambdaFunctionAliasName",
            description="Nombre del Alias de la función Lambda creada.",
        )
