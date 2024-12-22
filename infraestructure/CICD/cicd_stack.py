from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_s3 as s3,
    Fn,
    RemovalPolicy,
    CfnOutput,
    SecretValue,
)
from constructs import Construct

class CicdStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Importar el nombre y ARN del bucket S3
        bucket_name = Fn.import_value("LambdaS3BucketName")
        bucket_arn = Fn.import_value("LambdaS3BucketArn")

        # Importar el ARN y el nombre de la función Lambda
        lambda_function_arn = Fn.import_value("LambdaFunctionArn")
        lambda_function_name = Fn.import_value("LambdaFunctionName")
        lambda_function_alias_name = Fn.import_value("LambdaFunctionAliasName")

        # Crear referencia al bucket S3
        s3_bucket = s3.Bucket.from_bucket_attributes(
            self, "ImportedBucket", bucket_name=bucket_name, bucket_arn=bucket_arn
        )

        # Definir rol para CodeBuild con permisos específicos
        codebuild_role = iam.Role(
            self,
            "CodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
        )

        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:UpdateFunctionCode",
                    "lambda:PublishVersion",
                    "lambda:UpdateAlias",
                    "lambda:GetFunction",
                ],
                resources=[lambda_function_arn],
            )
        )

        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[f"{bucket_arn}/*"],
            )
        )

        # Crear proyecto de CodeBuild
        codebuild_project = codebuild.PipelineProject(
            self,
            "LambdaCodeBuildProject",
            role=codebuild_role,
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_6_0,
                privileged=True,
                environment_variables={
                    "bucket_name": codebuild.BuildEnvironmentVariable(value=bucket_name),
                    "lambda_function_name": codebuild.BuildEnvironmentVariable(value=lambda_function_name),
                    "lambda_function_alias_name": codebuild.BuildEnvironmentVariable(value=lambda_function_alias_name),
                    "BUILD_ARTIFACT": codebuild.BuildEnvironmentVariable(value='package.zip'),
                },
            ),
            build_spec=codebuild.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "install": {
                            "commands": [
                                "echo \"Instalando dependencias para la función Lambda...\"",
                                "pip install -r requirements.txt",
                            ]
                        },
                        "build": {
                            "commands": [
                                "echo \"Empaquetando la función Lambda...\"",
                                "cd src && zip -r ../$BUILD_ARTIFACT . && cd ..",
                                "zip -r $BUILD_ARTIFACT requirements.txt",
                                "aws s3 cp $BUILD_ARTIFACT s3://$bucket_name/$BUILD_ARTIFACT",
                                "aws lambda update-function-code --function-name $lambda_function_name --s3-bucket $bucket_name --s3-key $BUILD_ARTIFACT --publish",
                                "FUNCTION_VERSION=$(aws lambda get-function --function-name $lambda_function_name --query 'Configuration.Version' --output text)",
                                "aws lambda update-alias --function-name $lambda_function_name --name $lambda_function_alias_name --function-version $FUNCTION_VERSION",
                            ]
                        },
                        "post_build": {
                            "commands": [
                                "echo \"El código se ha empaquetado y desplegado correctamente\"",
                            ]
                        },
                    },
                    "artifacts": {
                        "files": ["package.zip"]
                    },
                }
            ),
        )

        # Crear pipeline
        pipeline = codepipeline.Pipeline(
            self,
            "LambdaCodePipeline",
            pipeline_name="LambdaCodePipeline",
            artifact_bucket=s3_bucket,
        )

        # Fuente: GitHub
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="fjlacruz",
            repo="sam-py",
            oauth_token=SecretValue.unsafe_plain_text(
                "token-git-hub"
            ),
            branch="master",
            output=source_output,
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action],
        )

        # Build: CodeBuild
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=codebuild_project,
            input=source_output,
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action],
        )

        # Salidas del Stack
        CfnOutput(
            self,
            "PipelineNameOutput",
            value=pipeline.pipeline_name,
            export_name="PipelineName",
            description="Nombre del pipeline de CI/CD creado.",
        )
