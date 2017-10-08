# sammy
Python library for generating AWS SAM (Serverless Application Model) templates with validations.


## Features

- Render templates with YAML or JSON
- Validations are done with [Valley](https://github.com/capless/valley)

## Documentation

### Python Versions Supported

- Python 3.6+

### Quick Start

#### Install 

```bash
pip install sammy
```

#### Simple Example

```python
from sammy import SAM, Function, API, SimpleTable

f = Function('testpublish',Handler='s3imageresize.handler',
             Runtime='python3.6',
             CodeUri='s3://your-bucket/photoresizer.zip')

ddb = SimpleTable('maintable',PrimaryKey={'Name':'_id','Type':'String'})

s = SAM(render_type='yaml')

s.add_resource(f)
s.add_resource(ddb)

print(s.to_yaml())
```


### SAM

SAM is the class that generates the SAM template.

```python
from sammy import SAM, SimpleTable

s = SAM(resources=[SimpleTable('maintable',PrimaryKey={'Name':'_id','Type':'String'})],
render_type='json')
```

#### Keyword Arguments

- **resources** - List of resource classes (API, SimpleTable, or Function)
- **render_type** - This is a string and there are only two options JSON or YAML.

#### Methods

##### add_resource(resource)

Add a resource class to the template

###### Example

```python
from sammy import Function, SAM

s = SAM(render_type='json')

f = Function('testpublish',Handler='s3imageresize.handler',
             Runtime='python3.6',
             CodeUri='s3://your-bucket/photoresizer.zip')

s.add_resource(f)
```

##### add_parameter(parameter)

Add a parameter class to the template

###### Example

```python
import sammy as sm

s = sm.SAM(render_type='json')

s.add_parameter(sm.Parameter(name='Bucket',Type='String'))
```

##### get_template_dict()

Returns Python *dict* object representation of the template.

##### to_json()

Returns a JSON representation of the template.

##### to_yaml()

Returns a YAML representation of the template.

##### get_template()

Returns a YAML or JSON representation of the template depending on what you set the render_type to on initialization.

##### publish_template(bucket_name)

Publishes the SAM template to S3

##### publish(stack_name)

Publishes the SAM template to Cloudformation 


### Function

This class represents an AWS Lambda function

```python
from sammy import Function

f = Function('testpublish',Handler='s3imageresize.handler',
             Runtime='python3.6',
             CodeUri='s3://your-bucket/photoresizer.zip')
```

### API

This class represents an AWS API Gateway

```python
from sammy import API

a = API(StageName='dev',DefinitionUri='s3://your-bucket/your-swagger.yml',
    CacheClusterEnabled=False,CacheClusterSize=None,Variables={'SOME_VAR':'test'})
```

### SimpleTable

This class represents a simple DynamoDB table

```python
from sammy import SimpleTable

ddb = SimpleTable('maintable',PrimaryKey={'Name':'_id','Type':'String'})
```

### Ref

This class represents a reference

```python
import sammy as sm


sam = sm.SAM(Description='A hello world application.',render_type='yaml')

sam.add_parameter(sm.Parameter(name='Bucket',Type='String'))

sam.add_parameter(sm.Parameter(name='CodeZipKey',Type='String'))

sam.add_resource(
    sm.Function(name='HelloWorldFunction',
        Handler='sample.handler', Runtime='python3.6', CodeUri=sm.S3URI(
            Bucket=sm.Ref(Ref='Bucket'),Key=sm.Ref(Ref='CodeZipKey'))))

```