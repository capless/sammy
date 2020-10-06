import sammy as sm

hook = sm.Hooks(PostTraffic="post_traffic", PreTraffic="pre_traffic")
deploy = sm.DeploymentPreference(Type="Todo", Hooks=hook)
on_fail = sm.OnFailure(Destination="destination-path")
event_invoke_destination_config = sm.EventInvokeDestinationConfiguration(
    OnFailure=on_fail)
event_invoke_config = sm.EventInvokeConfiguration(
    MaximumRetryAttempts=15, DestinationConfig=event_invoke_destination_config)
provisioned_concurrency_config = sm.ProvisionedConcurrencyConfig(
    ProvisionedConcurrentExecutions=15)
sam = sm.SAM(Description='Function new properties')

sam.add_resource(sm.Function(
    name='FunctionNewProperties',
    CodeUri=sm.S3URI(Bucket='<bucket>', Key='sammytest.zip'),
    Handler='sample.handler',
    Runtime='python3.6',
    AutoPublishAlias='lambda-alias',
    AutoPublishCodeSha256='sha256-code',
    DeploymentPreference=deploy,
    EventInvokeConfig=event_invoke_config,
    FileSystemConfigs=['config-1', 'config-2'],
    InlineCode='inline-code',
    PermissionBoundary='permission-boundary',
    ProvisionedConcurrencyConfig=provisioned_concurrency_config,
    VersionDescription='version-description'
))
