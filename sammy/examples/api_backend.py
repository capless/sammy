import sammy as sm


sam = sm.SAM(Description='Simple CRUD webservice. State is stored in a SimpleTable (DynamoDB) resource.')

sam.add_resource(sm.Function(
    name='GetFunction',
    CodeUri='s3://<bucket>/api_backend.zip',
    Handler='index.get',
    Runtime='nodejs4.3',
    Policies='AmazonDynamoDBReadOnlyAccess',
    Environment=sm.Environment(Variables={'TABLE_NAME':'!Ref Table'}),
    Events=[sm.APIEvent(name='GetResource',Path='/resource/{resourceId}',Method='get')]
))

sam.add_resource(sm.Function(
    name='PutFunction',
    Handler='index.put',
    Runtime='nodejs4.3',
    CodeUri='s3://<bucket>/api_backend.zip',
    Policies='AmazonDynamoDBFullAccess',
    Environment=sm.Environment(Variables={'TABLE_NAME':'!Ref Table'}),
    Events=[sm.APIEvent(name='PutResource',Path='/resource/{resourceId}',Method='put')]
))

sam.add_resource(sm.Function(
    name='DeleteFunction',
    Handler='index.delete',
    Runtime='nodejs4.3',
    CodeUri='s3://<bucket>/api_backend.zip',
    Policies='AmazonDynamoDBFullAccess',
    Environment=sm.Environment(Variables={'TABLE_NAME':'!Ref Table'}),
    Events=[sm.APIEvent(name='DeleteResource',Path='/resource/{resourceId}',Method='delete')]
))

sam.add_resource(sm.SimpleTable(name='Table'))