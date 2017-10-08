import sammy as sm


sam = sm.SAM(Description='A hello world application.',render_type='yaml')

sam.add_parameter(sm.Parameter(name='Bucket',Type='String'))

sam.add_parameter(sm.Parameter(name='CodeZipKey',Type='String'))

sam.add_resource(
    sm.Function(name='HelloWorldFunction',
        Handler='sample.handler', Runtime='python3.6', CodeUri=sm.S3URI(
            Bucket=sm.Ref(Ref='Bucket'),Key=sm.Ref(Ref='CodeZipKey'))))
