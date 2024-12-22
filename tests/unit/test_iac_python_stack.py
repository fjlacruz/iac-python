import aws_cdk as core
import aws_cdk.assertions as assertions

from infraestructure.iac_python_stack import IacPythonStack

# example tests. To run these tests, uncomment this file along with the example
# resource in iac_python/iac_python_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = IacPythonStack(app, "iac-python")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
