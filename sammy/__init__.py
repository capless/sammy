import boto3
import json
import yaml

from awscli.customizations.cloudformation.deployer import Deployer
from valley.properties import *
from valley.contrib import Schema
from valley.utils.json_utils import ValleyEncoderNoType

from sammy.custom_properties import ForeignInstanceListProperty

API_METHODS = (
    ('post','post'),
    ('get','get'),
    ('head','head'),
    ('delete','delete'),
    ('put','put'),
    ('options','options'),
    ('connect','connect'),
    ('any','any'),
)

RENDER_FORMATS = {'json':'json','yaml':'yaml'}


def remove_nulls(obj_dict):
    null_keys = []
    for k, v in obj_dict.items():
        if not v:
            null_keys.insert(0, k)
    for k in null_keys:
        obj_dict.pop(k)
    return obj_dict


class SAM(Schema):
    aws_template_format_version = '2010-09-09'
    transform = 'AWS::Serverless-2016-10-31'
    Description = CharProperty()
    resources = ListProperty()
    render_type = CharProperty(choices=RENDER_FORMATS,default_value='yaml')

    def __init__(self,**kwargs):
        super(SAM, self).__init__(**kwargs)
        self.validate()

        self.cf = boto3.client('cloudformation')
        self.s3 = boto3.resource('s3')

    def add_resource(self,resource):
        resources = self._data.get('resources') or []
        resources.append(resource)
        resources = set(resources)
        self._data['resources'] = list(resources)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        rl = [i.to_dict() for i in obj.get('resources')]
        resources = {i.get('name'):i.get('r') for i in rl}

        template = {
            'AWSTemplateFormatVersion': self.aws_template_format_version,
            'Transform': self.transform,
            'Resources': resources
        }
        if obj.get('Description'):
            template['Description'] = obj.get('Description')
        return template

    def get_template_dict(self):
        return self.to_dict()

    def publish_template(self,bucket,name):
        filename = '{}.{}'.format(name,self.render_type)

        self.s3.Object(bucket, filename).put(
            Body=self.get_template())

    def get_template(self):
        if self.render_type == 'json':
            return self.to_json()
        else:
            return self.to_yaml()

    def publish(self, stack_name):
        d = Deployer(boto3.client('cloudformation'))
        result = d.create_and_wait_for_changeset(
            stack_name=stack_name,
            cfn_template=self.get_template(),
            parameter_values=[],
            capabilities=['CAPABILITY_IAM'])
        d.execute_changeset(result.changeset_id, stack_name)
        d.wait_for_execute(stack_name, result.changeset_type)

    def to_yaml(self):
        jd = json.dumps(self.get_template_dict(),cls=ValleyEncoderNoType)
        #TODO: Write this without converting to JSON first
        jl = json.loads(jd)
        return yaml.safe_dump(jl,
                              default_flow_style=False)

    def to_json(self):
        return json.dumps(self.get_template_dict(),cls=ValleyEncoderNoType)


class S3KeyFilter(Schema):
    S3Key = CharProperty()


class Environment(Schema):
    Variables = DictProperty(required=True)


class SAMResource(Schema):
    _resource_type = None

    name = CharProperty(required=True)

    def __init__(self,**kwargs):
        super(SAMResource, self).__init__(**kwargs)
        self.validate()


    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        name = obj.pop('name')
        r_attrs = {
            'Type':self._resource_type
        }
        if len(obj.keys()) > 0:
            r_attrs['Properties'] = {k: v for k, v in obj.items() if v}

        return {
            'name':name,
            'r':r_attrs
        }


    def add_attr(self,k,v):
        self.r_attrs['Properties'][k] = v


class EventSchema(Schema):
    _event_type = None

    name = CharProperty(required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        event = {'name':obj.pop('name'),
                 'r':{
                    'Type':self._event_type
                 }
                }

        if len(obj.keys()) > 0:
            event['r']['Properties'] = obj
        return event


class APIEvent(EventSchema):
    _event_type = 'API'

    Path = CharProperty(required=True)
    Method = CharProperty(required=True,choices=API_METHODS)
    RestApiId = CharProperty()


class S3Event(EventSchema):
    _event_type = 'S3'

    Bucket = CharProperty(required=True)
    Events = ListProperty(required=True)
    Filter = ForeignProperty(S3KeyFilter)


class SNSEvent(EventSchema):
    _event_type = 'SNS'

    Topic = CharProperty(required=True)


class KinesisEvent(EventSchema):
    _event_type = 'Kinesis'

    Stream = CharProperty(required=True)
    StartingPosition = CharProperty(required=True)
    BatchSize = IntegerProperty()


class DynamoDBEvent(EventSchema):
    _event_type = 'DynamoDB'

    Stream = CharProperty(required=True)
    StartingPosition = CharProperty(required=True)
    BatchSize = IntegerProperty()


class ScheduleEvent(EventSchema):
    Schedule = CharProperty(required=True)
    Input = CharProperty()


class CloudWatchEvent(EventSchema):
    Pattern = DictProperty(required=True)
    Input = CharProperty()
    InputPath = CharProperty()


class IoTRuleEvent(EventSchema):
    Sql = CharProperty(required=True)
    AwsIotSqlVersion = CharProperty()


class AlexaSkillEvent(EventSchema):
    _event_type = 'AlexaSkill'


class DeadLetterQueueSchema(Schema):
    _dlq_type = None

    name = CharProperty(required=True)
    TargetArn = CharProperty(required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        event = {'name':obj.pop('name'),
                 'r':{
                    'Type':self._dlq_type,
                    'Properties':obj
                }}

        return event


class SNSLetterQueue(DeadLetterQueueSchema):
    _dlq_type = 'SNS'


class SQSLetterQueue(DeadLetterQueueSchema):
    _dlq_type = 'SQS'


class Function(SAMResource):
    _resource_type = 'AWS::Serverless::Function'

    Handler = CharProperty(required=True)
    Runtime = CharProperty(required=True,max_length=15)
    CodeUri = CharProperty()
    FunctionName = CharProperty()
    Description = CharProperty()
    MemorySize = IntegerProperty()
    Timeout = IntegerProperty()
    Role = CharProperty()
    Policies = CharProperty()
    Environment = ForeignProperty(Environment)
    VpcConfig = DictProperty()
    Events = ForeignInstanceListProperty(EventSchema)
    Tags = DictProperty()
    Tracing = CharProperty()
    KmsKeyArn = CharProperty()
    DeadLetterQueue = ForeignInstanceListProperty(DeadLetterQueueSchema)

    def to_dict(self):
        obj = super(Function, self).to_dict()
        try:
            events = [i.to_dict() for i in obj['r']['Properties'].pop('Events')]
            obj['r']['Properties']['Events'] = {i.get('name'):i.get('r') for i in events}
        except KeyError:
            pass

        try:
            dlq = [i.to_dict() for i in obj['r']['Properties'].pop('DeadLetterQueue')]
            obj['r']['Properties']['DeadLetterQueue'] = {i.get('name'):i.get('r') for i in dlq}
        except KeyError:
            pass
        return obj


class API(SAMResource):
    _resource_type = "AWS::Serverless::Api"

    StageName = CharProperty(required=True)
    DefinitionUri = CharProperty()
    DefinitionBody = DictProperty()
    CacheClusterEnabled = BooleanProperty()
    CacheClusterSize = CharProperty()
    Variables = DictProperty()


class SimpleTable(SAMResource):
    _resource_type = "AWS::Serverless::SimpleTable"

    PrimaryKey = DictProperty()
    ProvisionedThroughput = DictProperty()

