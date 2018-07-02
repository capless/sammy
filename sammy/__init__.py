import collections

import boto3
import json
import logging
import time

import botocore
import sys
import yaml

from boto3 import exceptions


from valley.properties import *
from valley.contrib import Schema
from valley.utils.json_utils import ValleyEncoderNoType

from sammy.custom_properties import ForeignInstanceListProperty, \
    CharForeignProperty, IntForeignProperty


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

CF = boto3.client('cloudformation')

LOG = logging.getLogger(__name__)

ChangeSetResult = collections.namedtuple(
                "ChangeSetResult", ["changeset_id", "changeset_type"])

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


class Sub(SAMSchema):
    Sub = CharForeignProperty(Ref,required=True)
    Map = DictProperty()

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        Map = obj.get('Map',None)
        if not Map:
            return {
                "Fn::Sub":obj.get('Sub'),
            }
        else:
            return {
                "Fn::Sub":[obj.get('Sub'),obj.get('Map')]
            }


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


class SQSEvent(EventSchema):
    _event_type = 'SQS'

    Queue = CharForeignProperty(Ref, required=True)
    BatchSize = IntForeignProperty(Ref)


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


class Role(Resource):
    _resource_type = 'AWS::IAM::Role'

    AssumeRolePolicyDocument = DictProperty()
    ManagedPolicyArns = ListProperty()
    MaxSessionDuration = IntegerProperty()
    Path = CharProperty()
    Policies = ListProperty()
    RoleName = CharProperty()


class S3(Resource):
    _resource_type = 'AWS::S3::Bucket'


class SNS(Resource):
    _resource_type = 'AWS::SNS::Topic'


class SQS(Resource):
    _resource_type = 'AWS::SQS::Queue'
    QueueName = CharForeignProperty(Ref)


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
        self.changeset_prefix = 'sammy-deploy-'

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


    def has_stack(self, stack_name):
        """
        Checks if a CloudFormation stack with given name exists
        :param stack_name: Name or ID of the stack
        :return: True if stack exists. False otherwise
        """
        try:
            resp = CF.describe_stacks(StackName=stack_name)
            if len(resp["Stacks"]) != 1:
                return False

            # When you run CreateChangeSet on a a stack that does not exist,
            # CloudFormation will create a stack and set it's status
            # REVIEW_IN_PROGRESS. However this stack is cannot be manipulated
            # by "update" commands. Under this circumstances, we treat like
            # this stack does not exist and call CreateChangeSet will
            # ChangeSetType set to CREATE and not UPDATE.
            stack = resp["Stacks"][0]
            return stack["StackStatus"] != "REVIEW_IN_PROGRESS"

        except botocore.exceptions.ClientError as e:
            # If a stack does not exist, describe_stacks will throw an
            # exception. Unfortunately we don't have a better way than parsing
            # the exception msg to understand the nature of this exception.
            msg = str(e)

            if "Stack with id {0} does not exist".format(stack_name) in msg:
                LOG.debug("Stack with id {0} does not exist".format(
                    stack_name))
                return False
            else:
                # We don't know anything about this exception. Don't handle
                LOG.debug("Unable to get stack details.", exc_info=e)
                raise e

    def publish(self, stack_name,**kwargs):
        param_list = [{'ParameterKey':k,'ParameterValue':v} for k,v in kwargs.items()]
        changeset_name = self.changeset_prefix + str(int(time.time()))
        if self.has_stack(stack_name):
            changeset_type = "UPDATE"
        else:
            changeset_type = "CREATE"

        resp = CF.create_change_set(StackName=stack_name,TemplateBody=self.get_template(),
                             Parameters=param_list,ChangeSetName=changeset_name,
                            Capabilities=['CAPABILITY_IAM'],ChangeSetType=changeset_type)
        result = ChangeSetResult(resp["Id"], changeset_type)

        sys.stdout.write("Waiting for {} stack change set creation to complete\n".format(
            stack_name))
        sys.stdout.flush()
        waiter = CF.get_waiter("change_set_create_complete")
        try:
            waiter.wait(ChangeSetName=result.changeset_id, StackName=stack_name,
                        WaiterConfig={'Delay': 5})
        except botocore.exceptions.WaiterError as ex:
            LOG.debug("Create changeset waiter exception", exc_info=ex)
        CF.execute_change_set(
                ChangeSetName=result.changeset_id,
                StackName=stack_name)

        sys.stdout.write("Waiting for {} stack {} to complete\n".format(
            stack_name,changeset_type.lower()))
        sys.stdout.flush()

        # Pick the right waiter
        if changeset_type == "CREATE":
            waiter = CF.get_waiter("stack_create_complete")
        elif changeset_type == "UPDATE":
            waiter = CF.get_waiter("stack_update_complete")
        else:
            raise RuntimeError("Invalid changeset type {0}"
                               .format(changeset_type))
        try:
            waiter.wait(StackName=stack_name,
                        WaiterConfig={'Delay': 5,'MaxAttempts': 720})
        except botocore.exceptions.WaiterError as ex:
            LOG.debug("Execute changeset waiter exception", exc_info=ex)

            raise exceptions.DeployFailedError(stack_name=stack_name)

    def unpublish(self,stack_name):
        print('Deleting {} stack'.format(stack_name))
        CF.delete_stack(StackName=stack_name)

    def to_yaml(self):
        jd = json.dumps(self.get_template_dict(),cls=ValleyEncoderNoType)
        #TODO: Write this without converting to JSON first
        jl = json.loads(jd)
        return yaml.safe_dump(jl,
                              default_flow_style=False)

    def to_json(self):
        return json.dumps(self.get_template_dict(),cls=ValleyEncoderNoType)