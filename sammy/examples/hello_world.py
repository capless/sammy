import sammy as sm


sam = sm.SAM(Description='A hello world application.')

sam.add_parameter(sm.Parameter(name='Bucket',Type='String'))

sam.add_parameter(sm.Parameter(name='CodeZipKey',Type='String'))

sam.add_resource(
    sm.Function(name='HelloWorldFunction',
        Handler='index.handler', Runtime='nodejs4.3', CodeURI=sm.CodeURI(
            Bucket='!Bucket',Key='!CodeZipKey')))
