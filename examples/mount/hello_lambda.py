# The handler "hello_lambda.handler" of an event function of AWS Lambda, of the payload format 2.0, whose stage is the
# path it is mounted under
def handler(event, context):
    stage, path = event['requestContext']['stage'], event['rawPath']
    body = f'Hello Lambda at {stage} for {path}!'
    return {'statusCode': 200, 'headers': {'content-type': 'text/plain'}, 'body': body}
