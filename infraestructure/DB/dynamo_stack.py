from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        # Obtener el entorno desde el contexto del stack
        environment = self.node.try_get_context("env")  # Puede ser dev, qa o prod

        # Si no se obtiene el contexto, asignar un valor predeterminado
        if environment is None:
            environment = "dev"  # Establecer un valor predeterminado si no se pasa el contexto

        
        # Crear la tabla DynamoDB
        dynamodb_table = dynamodb.Table(
            self, "cdk-table-py",
            table_name="cdk-table-py",  # Nombre de la tabla DynamoDB
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY  # Solo para desarrollo, eliminar al destruir la pila
        )

        # Exportar el ARN y el nombre de la tabla DynamoDB
        CfnOutput(
            self,
            "DynamoDBTableArn",
            value=dynamodb_table.table_arn,
            export_name="DynamoDBTableArn",
            description="ARN de la tabla DynamoDB creada.",
        )

        CfnOutput(
            self,
            "DynamoDBTableName",
            value=dynamodb_table.table_name,
            export_name="DynamoDBTableName",
            description="Nombre de la tabla DynamoDB creada.",
        )
