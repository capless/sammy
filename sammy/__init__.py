import collections

import boto3
import json
import time

import botocore
import sys
import yaml


from valley.properties import *
from valley.contrib import Schema
from valley.utils.json_utils import ValleyEncoderNoType

from sammy.custom_properties import ForeignInstanceListProperty, \
    CharForeignProperty, IntForeignProperty
from sammy.exceptions import DeployFailedError

API_METHODS = {
    'post': 'post',
    'get': 'get',
    'head': 'head',
    'delete': 'delete',
    'put': 'put',
    'options': 'options',
    'connect': 'connect',
    'any': 'any'
}

RENDER_FORMATS = {'json': 'json', 'yaml': 'yaml'}

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

    def __init__(self, **kwargs):
        super(SAMSchema, self).__init__(**kwargs)
        self.validate()


class Ref(SAMSchema):
    Ref = CharProperty(required=True)


class Sub(SAMSchema):
    Sub = CharForeignProperty(Ref, required=True)
    Map = DictProperty()

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        Map = obj.get('Map', None)
        if not Map:
            return {
                "Fn::Sub": obj.get('Sub'),
            }
        else:
            return {
                "Fn::Sub": [obj.get('Sub'), obj.get('Map')]
            }


class S3URI(SAMSchema):
    Bucket = CharForeignProperty(Ref, required=True)
    Key = CharForeignProperty(Ref, required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        return obj


class LambdaCode(SAMSchema):
    S3Bucket = CharForeignProperty(Ref, required=True)
    S3Key = CharForeignProperty(Ref, required=True)
    S3ObjectVersion = CharForeignProperty(Ref, required=True)
    ZipFile = CharForeignProperty(Ref, required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        return obj


class S3KeyFilter(SAMSchema):
    S3Key = CharForeignProperty(Ref)


class Environment(SAMSchema):
    Variables = DictProperty(required=True)


class Parameter(SAMSchema):
    name = CharForeignProperty(Ref, required=True)
    Type = CharForeignProperty(Ref, required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        name = obj.pop('name')
        return {
            'name': name,
            'r': obj
        }


class Output(SAMSchema):
    name = CharForeignProperty(Ref, required=True)
    Description = CharForeignProperty(Ref)
    Value = CharForeignProperty(Ref)
    Export = DictProperty()

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        name = obj.pop('name')
        return {
            'name': name,
            'r': obj
        }

class Resource(SAMSchema):
    _resource_type = None

    name = CharForeignProperty(Ref, required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        name = obj.pop('name')

        r_attrs = {
            'Type': self._resource_type
        }
        if len(obj.keys()) > 0:
            r_attrs['Properties'] = {k: v for k, v in obj.items() if v}
        return {
            'name': name,
            'r': r_attrs
        }

    def add_attr(self, k, v):
        self.r_attrs['Properties'][k] = v


class EventSchema(SAMSchema):
    _event_type = None

    name = CharForeignProperty(Ref, required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        event = {'name': obj.pop('name'),
                 'r': {
                     'Type': self._event_type
                 }
                 }

        if len(obj.keys()) > 0:
            event['r']['Properties'] = obj
        return event


class APIEvent(EventSchema):
    _event_type = 'Api'

    Path = CharForeignProperty(Ref, required=True)
    Method = CharForeignProperty(Ref, required=True, choices=API_METHODS)
    RestApiId = CharForeignProperty(Ref)


class S3Event(EventSchema):
    _event_type = 'S3'

    Bucket = CharForeignProperty(Ref, required=True)
    Events = ListProperty(required=True)
    Filter = ForeignProperty(S3KeyFilter)


class SNSEvent(EventSchema):
    _event_type = 'SNS'

    Topic = CharForeignProperty(Ref, required=True)


class SQSEvent(EventSchema):
    _event_type = 'SQS'

    Queue = CharForeignProperty(Ref, required=True)
    BatchSize = IntForeignProperty(Ref)


class KinesisEvent(EventSchema):
    _event_type = 'Kinesis'

    Stream = CharForeignProperty(Ref, required=True)
    StartingPosition = CharForeignProperty(Ref, required=True)
    BatchSize = IntegerProperty()


class DynamoDBEvent(EventSchema):
    _event_type = 'DynamoDB'

    Stream = CharForeignProperty(Ref, required=True)
    StartingPosition = CharForeignProperty(Ref, required=True)
    BatchSize = IntegerProperty()


class ScheduleEvent(EventSchema):
    Schedule = CharForeignProperty(Ref, required=True)
    Input = CharForeignProperty(Ref)


class CloudWatchEvent(EventSchema):
    Pattern = DictProperty(required=True)
    Input = CharForeignProperty(Ref)
    InputPath = CharForeignProperty(Ref)


class IoTRuleEvent(EventSchema):
    Sql = CharForeignProperty(Ref, required=True)
    AwsIotSqlVersion = CharForeignProperty(Ref)


class AlexaSkillEvent(EventSchema):
    _event_type = 'AlexaSkill'


class DeadLetterQueueSchema(SAMSchema):
    _dlq_type = None

    name = CharForeignProperty(Ref, required=True)
    TargetArn = CharForeignProperty(Ref, required=True)

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        event = {'name': obj.pop('name'),
                 'r': {
                     'Type': self._dlq_type,
                     'Properties': obj
                 }}

        return event


class SNSLetterQueue(DeadLetterQueueSchema):
    _dlq_type = 'SNS'


class SQSLetterQueue(DeadLetterQueueSchema):
    _dlq_type = 'SQS'


class Role(Resource):
    _resource_type = 'AWS::IAM::Role'
    _serverless_type = False

    AssumeRolePolicyDocument = DictProperty()
    ManagedPolicyArns = ListProperty()
    MaxSessionDuration = IntegerProperty()
    Path = CharProperty()
    Policies = ListProperty()
    RoleName = CharProperty()


class S3(Resource):
    _resource_type = 'AWS::S3::Bucket'
    _serverless_type = False

    BucketName = CharForeignProperty(Ref)


class SNS(Resource):
    _resource_type = 'AWS::SNS::Topic'
    _serverless_type = False


class SQS(Resource):
    _resource_type = 'AWS::SQS::Queue'
    _serverless_type = False

    ContentBasedDeduplication = BooleanProperty()
    DelaySeconds = IntForeignProperty(SAMSchema)
    FifoQueue = BooleanProperty()
    KmsMasterKeyId = CharForeignProperty(SAMSchema)
    KmsDataKeyReusePeriodSeconds = IntForeignProperty(SAMSchema)
    MaximumMessageSize = IntForeignProperty(SAMSchema)
    MessageRetentionPeriod = IntForeignProperty(SAMSchema)
    ReceiveMessageWaitTimeSeconds = IntForeignProperty(SAMSchema)
    VisibilityTimeout = IntForeignProperty(SAMSchema)
    QueueName = CharForeignProperty(Ref)


class AbstractFunction(Resource):
    Handler = CharForeignProperty(Ref, required=True)
    Runtime = CharForeignProperty(Ref, required=True, max_length=15)
    FunctionName = CharForeignProperty(Ref)
    Description = CharForeignProperty(Ref)
    MemorySize = IntegerProperty()
    Timeout = IntegerProperty()
    Role = CharForeignProperty(SAMSchema)
    Environment = ForeignProperty(Environment)
    VpcConfig = DictProperty()
    KmsKeyArn = CharForeignProperty(Ref)
    Tags = DictProperty()

    def to_dict(self):

        obj = super(AbstractFunction, self).to_dict()
        try:
            events = [i.to_dict() for i in obj['r']['Properties'].pop('Events')]

            obj['r']['Properties']['Events'] = {i.get('name'): i.get('r') for i in events}
        except KeyError:
            pass

        try:
            dlq = [i.to_dict() for i in obj['r']['Properties'].pop('DeadLetterQueue')]
            obj['r']['Properties']['DeadLetterQueue'] = {i.get('name'): i.get('r') for i in dlq}
        except KeyError:
            pass

        return obj


class Function(AbstractFunction):
    _resource_type = 'AWS::Serverless::Function'
    _serverless_type = True

    CodeUri = ForeignProperty(S3URI)
    Policies = CharForeignProperty(Ref)
    Events = ForeignInstanceListProperty(EventSchema)
    Tracing = CharForeignProperty(Ref)
    DeadLetterQueue = ForeignInstanceListProperty(DeadLetterQueueSchema)
    ReservedConcurrentExecutions = IntegerProperty()


class CFunction(AbstractFunction):
    _resource_type = 'AWS::Lambda::Function'
    _serverless_type = False

    Code = ForeignProperty(LambdaCode)
    Layers = ListProperty()
    TracingConfig = DictProperty()



class API(Resource):
    _resource_type = "AWS::Serverless::Api"
    _serverless_type = True

    StageName = CharForeignProperty(Ref, required=True)
    DefinitionUri = CharForeignProperty(Ref)
    DefinitionBody = DictProperty()
    CacheClusterEnabled = BooleanProperty()
    CacheClusterSize = CharForeignProperty(Ref)
    Variables = DictProperty()


class SimpleTable(Resource):
    _resource_type = "AWS::Serverless::SimpleTable"
    _serverless_type = True

    PrimaryKey = DictProperty()
    ProvisionedThroughput = DictProperty()


class DynamoDBTable(Resource):
    _resource_type = "AWS::DynamoDB::Table"
    _serverless_type = False

    AttributeDefinitions = ListProperty(required=True)
    TableName = CharForeignProperty(SAMSchema, required=True)
    GlobalSecondaryIndexes = ListProperty()
    KeySchema = ListProperty(required=True)
    BillingMode = CharForeignProperty(Ref)
    LocalSecondaryIndexes = ListProperty()
    PointInTimeRecoverySpecification = DictProperty()
    ProvisionedThroughput = DictProperty()
    SSESpecification = DictProperty()
    StreamSpecification = DictProperty()
    Tags = DictProperty()
    TimeToLiveSpecification = DictProperty()


class SAM(SAMSchema):
    aws_template_format_version = '2010-09-09'
    transform = 'AWS::Serverless-2016-10-31'
    Description = CharProperty()
    resources = ForeignInstanceListProperty(Resource)
    parameters = ForeignInstanceListProperty(Parameter)
    render_type = CharProperty(choices=RENDER_FORMATS, default_value='yaml')

    def __init__(self, region_name='us-east-1', profile_name='default', **kwargs):
        super(SAM, self).__init__(**kwargs)
        self.region_name = region_name
        self.profile_name = profile_name
        self.changeset_prefix = 'sammy-deploy-'
        self.build_clients_resources()

    def build_clients_resources(self, region_name=None, profile_name=None):
        region_name = region_name or self.region_name
        profile_name = profile_name or self.profile_name

        self.cf_client = self.get_client('cloudformation', region_name=region_name, profile_name=profile_name)
        self.cf_resource = self.get_resource('cloudformation', region_name=region_name, profile_name=profile_name)
        self.s3 = self.get_resource('s3', region_name=region_name, profile_name=profile_name)
        self.sts = self.get_client('sts', region_name=region_name,profile_name=profile_name)

    def add_parameter(self, parameter):
        self._base_properties.get('parameters').validate([parameter], 'parameters')
        parameters = self._data.get('parameters') or []
        parameters.append(parameter)
        parameters = set(parameters)
        self._data['parameters'] = list(parameters)

    def add_resource(self, resource):
        self._base_properties.get('resources').validate([resource], 'resources')
        resources = self._data.get('resources') or []
        resources.append(resource)
        resources = set(resources)
        self._data['resources'] = list(resources)

    def check_global_valid(self):
        """
        Makes sure there aren't any SAM resources in a template that will be used in a CloudFormation StackSet
        :return: bool
        """
        serverless_cnt = len(list(filter(lambda x: x._serverless_type, self._data['resources'])))
        if serverless_cnt > 0:
            return False
        return True

    def to_dict(self):
        obj = remove_nulls(self._data.copy())
        rl = [i.to_dict() for i in obj.get('resources')]

        resources = {i.get('name'): i.get('r') for i in rl}

        template = {
            'AWSTemplateFormatVersion': self.aws_template_format_version,
            'Resources': resources
        }
        if self.transform:
            template['Transform'] = self.transform
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

    def publish_template(self, bucket, name):

        filename = '{}.{}'.format(name, self.render_type)

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
        cf = self.cf_client
        try:
            resp = cf.describe_stacks(StackName=stack_name)
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

    def get_changeset_status(self, change_set_name):
        print(change_set_name)
        response = self.cf_client.describe_change_set(
            ChangeSetName=change_set_name,
        )
        return response['Status']

    def is_stack_instances_current(self, stackset_name, op_id, no_replication_groups):
        obj_list = self.cf_client.list_stack_instances(StackSetName=stackset_name)['Summaries']
        current_list = len(list(filter(lambda x: x.get('Status') == 'CURRENT', obj_list)))
        if current_list != no_replication_groups:
            print(
                'Only {} of the {} replication groups (stack instances) are ready yet. '.format(
                    current_list, no_replication_groups),
                'Checking again in 30 seconds. Stack Name: {}, Operation ID: {}'.format(stackset_name, op_id)
            )
            return False
        return True

    def get_session(self, profile_name='default'):
        return boto3.Session(profile_name=profile_name)

    def get_client(self, service_name, region_name='us-east-1', profile_name='default'):
        s = self.get_session(profile_name=profile_name)
        return s.client(service_name, region_name=region_name)

    def get_resource(self, service_name, region_name='us-east-1', profile_name='default'):
        s = self.get_session(profile_name=profile_name)
        return s.resource(service_name, region_name=region_name)

    def publish_global(self, stackset_name, replication_groups):
        if not self.check_global_valid():
            raise DeployFailedError('The publish_global method cannot publish SAM templates.')
        # Create Stack Set
        print('Creating {} Stack Set'.format(stackset_name))

        self.cf_client.create_stack_set(
            StackSetName=stackset_name,
            TemplateBody=self.get_template(),
        )
        # Create Stack Instances
        print('Creating {} Stack Instances'.format(stackset_name))
        op_id = self.cf_client.create_stack_instances(
            StackSetName=stackset_name,
            Accounts=[
                self.sts.get_caller_identity().get('Account')
            ],
            Regions=replication_groups
        )['OperationId']
        # Number of Replication Groups
        no_replication_groups = len(replication_groups)
        # Wait until all stack instances are created.
        while not self.is_stack_instances_current(stackset_name, op_id, no_replication_groups):
            time.sleep(30)
        print('Stack Set Creation Completed')

    def publish(self, stack_name, **kwargs):
        param_list = [{'ParameterKey': k, 'ParameterValue': v} for k, v in kwargs.items()]
        changeset_name = self.changeset_prefix + str(int(time.time()))
        if self.has_stack(stack_name):
            changeset_type = "UPDATE"
        else:
            changeset_type = "CREATE"

        cf = self.cf_client

        resp = cf.create_change_set(StackName=stack_name, TemplateBody=self.get_template(),
                                    Parameters=param_list, ChangeSetName=changeset_name,
                                    Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                                    ChangeSetType=changeset_type)
        change_set_name = resp['Id']

        result = ChangeSetResult(resp["Id"], changeset_type)

        sys.stdout.write("Waiting for {} changeset {} to complete\n".format(
            stack_name, changeset_type.lower()))

        sys.stdout.flush()

        while True:
            response = self.get_changeset_status(change_set_name)
            print(str(response))
            time.sleep(10)
            if response in ['CREATE_COMPLETE', 'FAILED']:
                print('Changeset {}'.format(response))
                break

        if response == 'CREATE_COMPLETE':
            cf.execute_change_set(
                ChangeSetName=result.changeset_id,
                StackName=stack_name)

            sys.stdout.write("Waiting for {} stack {} to complete\n".format(
                stack_name, changeset_type.lower()))
            sys.stdout.flush()
            # Pick the right waiter
            if changeset_type == "CREATE":
                waiter = cf.get_waiter("stack_create_complete")
            elif changeset_type == "UPDATE":
                waiter = cf.get_waiter("stack_update_complete")
            else:
                raise RuntimeError("Invalid changeset type {0}"
                                   .format(changeset_type))
            try:
                waiter.wait(StackName=stack_name,
                            WaiterConfig={'Delay': 5, 'MaxAttempts': 720})
            except botocore.exceptions.WaiterError as ex:
                LOG.debug("Execute changeset waiter exception", exc_info=ex)
                raise DeployFailedError

            return self.cf_resource.Stack(stack_name)
        else:
            # Print the reason for failure
            print(cf.describe_change_set(
                ChangeSetName=change_set_name,
            )['StatusReason'])

    def unpublish(self, stack_name):
        print('Deleting {} stack'.format(stack_name))
        self.cf_client.delete_stack(StackName=stack_name)

    def to_yaml(self):
        jd = json.dumps(self.get_template_dict(), cls=ValleyEncoderNoType)
        # TODO: Write this without converting to JSON first
        jl = json.loads(jd)
        return yaml.safe_dump(jl,
                              default_flow_style=False)

    def to_json(self):
        return json.dumps(self.get_template_dict(), cls=ValleyEncoderNoType)


class CFT(SAM):
    transform = None

    outputs = ForeignInstanceListProperty(Output)

    def add_output(self, output):
        self._base_properties.get('outputs').validate([output], 'outputs')
        outputs = self._data.get('outputs') or []
        outputs.append(output)
        outputs = set(outputs)
        self._data['outputs'] = list(outputs)

    def to_dict(self):
        template = super(CFT, self).to_dict()
        obj = remove_nulls(self._data.copy())
        if obj.get('outputs'):
            pl = [i.to_dict() for i in obj.get('outputs')]
            outputs = {i.get('name'): i.get('r') for i in pl}
            if len(outputs.keys()) > 0:
                template['Outputs'] = outputs
        return template
