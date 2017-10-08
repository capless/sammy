import sammy as sm


sam = sm.SAM(Description='Simple CRUD webservice. State is stored in a SimpleTable (DynamoDB) resource.')

sam.add_resource(sm.Function(
    name='GetFunction',
    CodeUri=sm.S3URI(Bucket='<bucket>',Key='sammytest.zip'),
    Handler='index.get',
    Runtime='python3.6',
    Policies='AmazonDynamoDBReadOnlyAccess',
    Environment=sm.Environment(Variables={'TABLE_NAME':sm.Ref(Ref='Table')}),
    Events=[sm.APIEvent(name='GetResource',Path='/resource/{resourceId}',Method='get')]
))

sam.add_resource(sm.Function(
    name='PutFunction',
    Handler='index.put',
    Runtime='python3.6',
    CodeUri=sm.S3URI(Bucket='<bucket>',Key='sammytest.zip'),
    Policies='AmazonDynamoDBFullAccess',
    Environment=sm.Environment(Variables={'TABLE_NAME':sm.Ref(Ref='Table')}),
    Events=[sm.APIEvent(name='PutResource',Path='/resource/{resourceId}',Method='put')]
))

sam.add_resource(sm.Function(
    name='DeleteFunction',
    Handler='index.delete',
    Runtime='python3.6',
    CodeUri=sm.S3URI(Bucket='<bucket>',Key='sammytest.zip'),
    Policies='AmazonDynamoDBFullAccess',
    Environment=sm.Environment(Variables={'TABLE_NAME':sm.Ref(Ref='Table')}),
    Events=[sm.APIEvent(name='DeleteResource',Path='/resource/{resourceId}',Method='delete')]
))

sam.add_resource(sm.SimpleTable(name='Table'))