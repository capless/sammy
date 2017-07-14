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

##### add_resource

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

### Function

```python
from sammy import Function

f = Function('testpublish',Handler='s3imageresize.handler',
             Runtime='python3.6',
             CodeUri='s3://your-bucket/photoresizer.zip')
```