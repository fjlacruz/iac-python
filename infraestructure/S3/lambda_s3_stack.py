from aws_cdk import (
    Stack,
    aws_s3 as s3,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class LambdaS3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Obtener el entorno desde el contexto del stack
        environment = self.node.try_get_context("env")  # Puede ser dev, qa o prod

        # Si no se obtiene el contexto, asignar un valor predeterminado
        if environment is None:
            environment = "dev"  # Establecer un valor predeterminado si no se pasa el contexto

        # Establecer el nombre del bucket con el entorno
        bucket_name = f"lambda-packagecode-zip-{environment}"

        # Crear un bucket de S3 con el nombre específico
        bucket = s3.Bucket(
            self, "LambdaS3Bucket",
            bucket_name=bucket_name,  # Nombre del bucket con el entorno
            versioned=True,  # Habilita el versionado
            removal_policy=RemovalPolicy.DESTROY  # Eliminar el bucket cuando se destruye la pila
        )

        # Exportar el nombre del bucket
        CfnOutput(
            self, "BucketNameOutput",
            value=bucket.bucket_name,
            description="Bucket to lambda code",
            export_name="LambdaS3BucketName"
        )

        # Exportar el ARN del bucket
        CfnOutput(
            self, "BucketArnOutput",
            value=bucket.bucket_arn,
            description="The ARN of the S3 bucket",
            export_name="LambdaS3BucketArn"
        )

        # Exportar el valor del entorno para verificarlo en el `cdk synth`
        CfnOutput(
            self, "EnvironmentOutput",
            value=environment,
            description="The environment (dev, qa, prod)",
            export_name="LambdaEnvironment"
        )
