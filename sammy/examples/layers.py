import sammy as sm


sam = sm.SAM(Description='A hello world application.',render_type='yaml')

bucket = sm.S3Bucket(name="TestBucket", BucketName="MyBucket")
layer = sm.LayerVersion(name="TestLayer", ContentUri="ContentTest")
bucket2 = sm.S3Bucket(name="ZTestBucket", BucketName="MyBucket")


sam.add_resource(layer)

sam.add_resource(bucket)
sam.add_resource(bucket2)

#sam.add_resource(
#    sm.Function(name='HelloWorldFunction',
#        Handler='sample.handler', Runtime='python3.6', CodeUri=sm.S3URI(
#            Bucket=sm.Ref(Ref='Bucket'),Key=sm.Ref(Ref='CodeZipKey'))))

print(sam.to_yaml())
