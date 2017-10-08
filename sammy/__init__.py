import boto3
import json
import yaml

from awscli.customizations.cloudformation.deployer import Deployer
from valley.properties import *
from valley.contrib import Schema
from valley.utils.json_utils import ValleyEncoderNoType

from sammy.custom_properties import ForeignInstanceListProperty, CharForeignProperty


API_METHODS = {
    'post':'post',
    'get':'get',
    'head':'head',
    'delete':'delete',
    'put':'put',
    'options':'options',
    'connect':'connect',
    'any':'any'
}
RENDER_FORMATS = {'json':'json','yaml':'yaml'}

def remove_nulls(obj_dict):
    null_keys = []
    for k, v in obj_dict.items():
        if not v:
            null_keys.insert(0, k)
    for k in null_keys:
        obj_dict.pop(k)
    return obj_dict


class SAMSchema(Schema):

    def __init__(self,**kwargs):
        super(SAMSchema, self).__init__(**kwargs)
        self.validate()


class Ref(SAMSchema):
    Ref = CharProperty(required=True)


class S3URI(SAMSchema):
    Bucket = CharForeignProperty(Ref,required=True)
    Key = CharForeignProperty(Ref,required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        return obj


class S3KeyFilter(SAMSchema):
    S3Key = CharForeignProperty(Ref)


class Environment(SAMSchema):
    Variables = DictProperty(required=True)


class Parameter(SAMSchema):
    name = CharForeignProperty(Ref,required=True)
    Type = CharForeignProperty(Ref,required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        name = obj.pop('name')
        return {
            'name':name,
            'r':obj
        }

class Resource(SAMSchema):
    _resource_type = None

    name = CharForeignProperty(Ref,required=True)

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


class EventSchema(SAMSchema):
    _event_type = None

    name = CharForeignProperty(Ref,required=True)

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
    _event_type = 'Api'

    Path = CharForeignProperty(Ref,required=True)
    Method = CharForeignProperty(Ref,required=True,choices=API_METHODS)
    RestApiId = CharForeignProperty(Ref)


class S3Event(EventSchema):
    _event_type = 'S3'

    Bucket = CharForeignProperty(Ref,required=True)
    Events = ListProperty(required=True)
    Filter = ForeignProperty(S3KeyFilter)


class SNSEvent(EventSchema):
    _event_type = 'SNS'

    Topic = CharForeignProperty(Ref,required=True)


class KinesisEvent(EventSchema):
    _event_type = 'Kinesis'

    Stream = CharForeignProperty(Ref,required=True)
    StartingPosition = CharForeignProperty(Ref,required=True)
    BatchSize = IntegerProperty()


class DynamoDBEvent(EventSchema):
    _event_type = 'DynamoDB'

    Stream = CharForeignProperty(Ref,required=True)
    StartingPosition = CharForeignProperty(Ref,required=True)
    BatchSize = IntegerProperty()


class ScheduleEvent(EventSchema):
    Schedule = CharForeignProperty(Ref,required=True)
    Input = CharForeignProperty(Ref)


class CloudWatchEvent(EventSchema):
    Pattern = DictProperty(required=True)
    Input = CharForeignProperty(Ref)
    InputPath = CharForeignProperty(Ref)


class IoTRuleEvent(EventSchema):
    Sql = CharForeignProperty(Ref,required=True)
    AwsIotSqlVersion = CharForeignProperty(Ref)


class AlexaSkillEvent(EventSchema):
    _event_type = 'AlexaSkill'


class DeadLetterQueueSchema(SAMSchema):
    _dlq_type = None

    name = CharForeignProperty(Ref,required=True)
    TargetArn = CharForeignProperty(Ref,required=True)

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


class Function(Resource):
    _resource_type = 'AWS::Serverless::Function'

    Handler = CharForeignProperty(Ref,required=True)
    Runtime = CharForeignProperty(Ref,required=True,max_length=15)
    CodeUri = ForeignProperty(S3URI)
    FunctionName = CharForeignProperty(Ref)
    Description = CharForeignProperty(Ref)
    MemorySize = IntegerProperty()
    Timeout = IntegerProperty()
    Role = CharForeignProperty(Ref)
    Policies = CharForeignProperty(Ref)
    Environment = ForeignProperty(Environment)
    VpcConfig = DictProperty()
    Events = ForeignInstanceListProperty(EventSchema)
    Tags = DictProperty()
    Tracing = CharForeignProperty(Ref)
    KmsKeyArn = CharForeignProperty(Ref)
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


class API(Resource):
    _resource_type = "AWS::Serverless::Api"

    StageName = CharForeignProperty(Ref,required=True)
    DefinitionUri = CharForeignProperty(Ref)
    DefinitionBody = DictProperty()
    CacheClusterEnabled = BooleanProperty()
    CacheClusterSize = CharForeignProperty(Ref)
    Variables = DictProperty()


class SimpleTable(Resource):
    _resource_type = "AWS::Serverless::SimpleTable"

    PrimaryKey = DictProperty()
    ProvisionedThroughput = DictProperty()


class SAM(SAMSchema):
    aws_template_format_version = '2010-09-09'
    transform = 'AWS::Serverless-2016-10-31'
    Description = CharProperty()
    resources = ForeignInstanceListProperty(Resource)
    parameters = ForeignInstanceListProperty(Parameter)
    render_type = CharProperty(choices=RENDER_FORMATS,default_value='yaml')

    def __init__(self,**kwargs):
        super(SAM, self).__init__(**kwargs)

        self.cf = boto3.client('cloudformation')
        self.s3 = boto3.resource('s3')

    def add_parameter(self,parameter):
        self._base_properties.get('parameters').validate([parameter],'parameters')
        parameters = self._data.get('parameters') or []
        parameters.append(parameter)
        parameters = set(parameters)
        self._data['parameters'] = list(parameters)

    def add_resource(self,resource):
        self._base_properties.get('resources').validate([resource],'resources')
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
        if obj.get('parameters'):
            pl = [i.to_dict() for i in obj.get('parameters')]
            parameters = {i.get('name'): i.get('r') for i in pl}
            if len(parameters.keys()) > 0:
                template['Parameters'] = parameters
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

    def publish(self, stack_name,**kwargs):
        param_list = [{'ParameterKey':k,'ParameterValue':v} for k,v in kwargs.items()]
        d = Deployer(boto3.client('cloudformation'))
        result = d.create_and_wait_for_changeset(
            stack_name=stack_name,
            cfn_template=self.get_template(),
            parameter_values=param_list,
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