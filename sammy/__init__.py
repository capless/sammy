import boto3
import json
import yaml

from awscli.customizations.cloudformation.deployer import Deployer
from valley.properties import *
from valley.contrib import Schema


class SAM(object):
    aws_template_format_version = '2010-09-09'
    transform = 'AWS::Serverless-2016-10-31'
    RENDER_FORMATS = ('json','yaml')

    def __init__(self,resources=[],render_type='yaml'):
        if not isinstance(resources,(list,set,tuple)):
            raise ValueError('resources argument should be a list.')
        if not render_type in self.RENDER_FORMATS:
            raise ValueError('render_type should be in {}'.format(
                self.RENDER_FORMATS))
        self.render_type = render_type
        self.resources = resources
        self.cf = boto3.client('cloudformation')
        self.s3 = boto3.resource('s3')

    def add_resource(self,resource):
        #TODO: Refactor this
        self.resources = list(self.resources)
        self.resources.append(resource)
        self.resources = set(self.resources)

    def get_template_dict(self):
        resources = dict()
        for obj in self.resources:
            resources.update(obj.resource_config)
        template = {
            'AWSTemplateFormatVersion':self.aws_template_format_version,
            'Transform':self.transform,
            'Resources':resources
        }
        return template

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
        return yaml.safe_dump(self.get_template_dict(),
                              default_flow_style=False)

    def to_json(self):
        return json.dumps(self.get_template_dict())


class SAMResource(Schema):
    _resource_type = None

    def __init__(self,name,**kwargs):
        super(SAMResource, self).__init__(**kwargs)
        self.validate()
        self.r_attrs = dict()
        self.r_attrs['Properties'] = {k:v for k,v in self._data.items() if v}
        self.r_attrs['Type'] = self._resource_type

        self.resource_config = {
            name:self.r_attrs
        }

    def add_attr(self,k,v):
        self.r_attrs['Properties'][k] = v


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
    Environment = DictProperty()
    VpcConfig = DictProperty()
    Events = DictProperty()


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

    PrimaryKey = DictProperty(required=True)
    ProvisionedThroughput = DictProperty()
