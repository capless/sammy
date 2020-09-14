import sammy as sm

sam = sm.SAM(Description='API new properties')
access_log_setting = sm.AccessLogSetting(
    DestinationArn='destination-arn', Format='format')
cognito_authorization_identity = sm.CognitoAuthorizationIdentity(
    Header='header',
    ReauthorizeEvery='15',
    ValidationExpression='validation-expression')
cognito_authorizer = sm.CognitoAuthorizer(
    AuthorizationScopes=['scope-1', 'scope-2'],
    Identity=cognito_authorization_identity,
    UserPoolArn='user-pool')
resource_policy_statement = sm.ResourcePolicyStatement(
    AwsAccountBlacklist=['bl-1', 'bl-2'])
quota_settings = sm.QuotaSettings(Limit=99, Offset=15, Period='period')
throttle_settings = sm.ThrottleSettings(BurstLimit=22, RateLimit=10.15)
api_usage_plan = sm.ApiUsagePlan(CreateUsagePlan='usage-plan',
                                 description='description',
                                 Quota=quota_settings,
                                 Tags=['tag-1', 'tag-2'],
                                 Throttle=throttle_settings,
                                 UsagePlanName='usage-plan')
api_auth = sm.ApiAuth(
    AddDefaultAuthorizerToCorsPreflight=True,
    ApiKeyRequired=True,
    Authorizers=cognito_authorizer,
    DefaultAuthorizer='default-authorizer',
    InvokeRole='invoke-role',
    ResourcePolicy=resource_policy_statement,
    UsagePlan=api_usage_plan,)
canary_setting = sm.CanarySetting(
    DeploymentId='deployment-id',
    PercentTraffic=10.0,
    StageVariableOverrides={"key": "value"},
    UseStageCache=True)
route_53 = sm.Route53Configuration(
    DistributionDomainName='distribution-domain',
    EvaluateTargetHealth=True,
    HostedZoneId='hosted-zone-id',
    HostedZoneName='hosted-zone-name',
    IpV6=True)
domain_configuration = sm.DomainConfiguration(
    BasePath=['base-1', 'base-2'],
    CertificateArn='Certificate-arn',
    DomainName='domain-name',
    EndpointConfiguration='endpoint-configuration',
    Route53=route_53)
endpoint_configuration = sm.EndpointConfiguration(
    Type='endpoint-type',
    VPCEndpointIds=['vpc-endpoint-a', 'vpc-endpoint-b'])
method_setting = sm.MethodSettings(
    CacheDataEncrypted=True,
    CacheTtlInSeconds=12,
    CachingEnabled=True,
    DataTraceEnabled=True,
    HttpMethod='http://',
    LoggingLevel='logging-level',
    MetricsEnabled=True,
    ResourcePath='resource-path',
    ThrottlingBurstLimit=12,
    ThrottlingRateLimit=12.0
)
a = sm.API(
    name='ApiNewProperties',
    StageName='dev',
    DefinitionUri='s3://your-bucket/your-swagger.yml',
    CacheClusterEnabled=False,
    CacheClusterSize=None,
    Variables={'SOME_VAR': 'test'},
    AccessLogSetting=access_log_setting,
    Auth=api_auth,
    BinaryMediaTypes=['type-a', 'type-b'],
    CanarySetting=canary_setting,
    Cors='cors-tring',
    Domain=domain_configuration,
    EndpointConfiguration=endpoint_configuration,
    GatewayResponses={"key": "value"},
    MethodSettings=method_setting,
    MinimumCompressionSize=12,
    Models={"key": "value"},
    OpenApiVersion='api-version',
    Tags={"key": "value"},
    TracingEnabled=True,
)

sam.add_resource(a)
