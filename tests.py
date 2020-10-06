import unittest
import pathlib as pl
import os
import yaml

from sammy.examples.alexa_skill import sam as al
from sammy.examples.api_backend import sam as ab
from sammy.examples.hello_world import sam as hw
from sammy.examples.updated_function import sam as uf
from sammy.examples.updated_api import sam as ua

class AlexaTestCase(unittest.TestCase):
    template_name = 'alexa_skill.yaml'
    template = al

    def setUp(self):
        template_path = '{}/{}'.format(
            pl.PurePath(
                os.path.abspath(__file__)).parent / 'sammy/examples/yaml', self.template_name)
        with open(template_path, 'r') as f:
            self.template_dict = yaml.load(f)

    def test_template(self):
        s = yaml.safe_load(self.template.get_template())
        self.assertEqual(self.template_dict,s)


class APIBackendTestCase(AlexaTestCase):
    template_name = 'api_backend.yaml'
    template = ab

class HelloWorldTestCase(AlexaTestCase):
    template_name = 'hello_world.yaml'
    template = hw

class UpdatedFunctionTestCase(AlexaTestCase):
    template_name = 'updated_function.yaml'
    template = uf
    
class UpdatedApiTestCase(AlexaTestCase):
    template_name = 'updated_api.yaml'
    template = ua

class Test_SAM_Methods(unittest.TestCase):
    def setUp(self):
        from sammy import SAM
        self.s = SAM(Description='A hello world application.',render_type='yaml')

    def tearDown(self):
        self.s = None

    def test_add_resource(self):
        # Arrange
        from sammy import Function, Ref, S3URI
        f = Function(name='HelloWorldFunction',
        Handler='sample.handler', Runtime='python3.6', CodeUri=S3URI(
            Bucket=Ref(Ref='Bucket'),Key=Ref(Ref='CodeZipKey')))
            
        # Act
        self.s.add_resource(f)

        # Assert
        self.assertIsInstance(self.s._data.get('resources'),list)
        self.assertListEqual(self.s._data.get('resources'), [f])

    def test_add_parameter(self):
        # Arrange
        from sammy import Parameter
        p = Parameter(name='Bucket',Type='String')

        # Act
        self.s.add_parameter(p)

        # Assert
        self.assertIsInstance(self.s._data.get('parameters'), list)
        self.assertListEqual(self.s._data.get('parameters'), [p])

    def test_get_template_dict(self):
        # Arrange
        from sammy import Function, Ref, S3URI, Parameter
        f = Function(name='HelloWorldFunction',
            Handler='sample.handler', Runtime='python3.6', CodeUri=S3URI(
            Bucket=Ref(Ref='Bucket'),Key=Ref(Ref='CodeZipKey')))
        p = Parameter(name='Bucket',Type='String')
        self.s.add_resource(f)
        self.s.add_parameter(p)

        truth_p = p.to_dict()
        truth_f = f.to_dict()
        truth_dict = {'Resources': {truth_f['name']:truth_f['r']}, 'Parameters': {truth_p['name']:truth_p['r']}}
        
        # Act
        test_dict = self.s.to_dict()

        # Assert
        self.assertIsInstance(test_dict, dict)
        self.assertDictContainsSubset(truth_dict, test_dict)

    def test_to_json(self):
        # Arrange
        from sammy import Function, Parameter
        import json
        f = Function(name='HelloWorldFunction',
            Handler='sample.handler', Runtime='python3.6')
        p = Parameter(name='Bucket',Type='String')
        self.s.add_resource(f)
        self.s.add_parameter(p)

        truth_dict = self.s.get_template_dict()

        # Act
        test_json = self.s.to_json()
        test_json_dict = json.loads(test_json)

        # Assert
        self.assertIsInstance(test_json, str)
        self.assertIsInstance(test_json_dict, dict)
        self.assertDictEqual(truth_dict.get('Resources'), test_json_dict.get('Resources'))
        self.assertDictEqual(truth_dict.get('Parameters'), test_json_dict.get('Parameters'))

    def test_to_yaml(self):
        # Arrange
        from sammy import Function, Parameter
        import yaml
        f = Function(name='HelloWorldFunction',
            Handler='sample.handler', Runtime='python3.6')
        p = Parameter(name='Bucket',Type='String')
        self.s.add_resource(f)
        self.s.add_parameter(p)

        truth_dict = self.s.get_template_dict()

        # Act
        test_yaml = self.s.to_yaml()
        test_yaml_dict = yaml.safe_load(test_yaml)

        # Assert
        self.assertIsInstance(test_yaml, str)
        self.assertIsInstance(test_yaml_dict, dict)
        self.assertDictEqual(truth_dict.get('Resources'), test_yaml_dict.get('Resources'))
        self.assertDictEqual(truth_dict.get('Parameters'), test_yaml_dict.get('Parameters'))

    def test_get_template(self):
        # Arrange
        from sammy import Function, Parameter
        import yaml
        f = Function(name='HelloWorldFunction',
            Handler='sample.handler', Runtime='python3.6')
        p = Parameter(name='Bucket',Type='String')
        self.s.add_resource(f)
        self.s.add_parameter(p)

        truth_dict = self.s.get_template_dict()

        # Act
        test_template = self.s.get_template()
        test_template_dict = yaml.safe_load(test_template)

        # Assert
        self.assertEqual(self.s.render_type, 'yaml')
        self.assertIsInstance(test_template, str)
        self.assertIsInstance(test_template_dict, dict)
        self.assertDictEqual(truth_dict.get('Resources'), test_template_dict.get('Resources'))
        self.assertDictEqual(truth_dict.get('Parameters'), test_template_dict.get('Parameters'))

class Test_Function(unittest.TestCase):
    def setUp(self):
        pass 
    def tearDown(self):
        pass

    def test_HelloWorldFunction(self):
        # Arrange,
        # Case taken from HelloWorldFunction
        from sammy import Function
        name = 'HelloWorldFunction' 
        handler= 'sample.handler'
        runtime = 'python3.6'
        
        #  Act
        f = Function(name=name,
                    Handler=handler, 
                    Runtime=runtime)

        # Assert
        self.assertEqual(f.name,name)
        self.assertEqual(f.Handler,handler)
        self.assertEqual(f.Runtime, runtime)

    def test_AWSLambdaFunction(self):
        #Arrange,
        # Case taken from README.md
        from sammy import Function, Ref, S3URI
        name = 'testpublish'
        handler = 's3imageresize.handler'
        runtime = 'python3.6'
        codeUri = S3URI(Bucket=Ref(Ref='your-bucket'),Key=Ref(Ref='photoresizer.zip'))
        
        #  Act
        f = Function(name=name,
                    Handler=handler,
                    Runtime=runtime,
                    CodeUri=codeUri)
                    
        # Assert
        self.assertEqual(f.name,name)
        self.assertEqual(f.Handler, handler)
        self.assertEqual(f.Runtime,runtime)
        self.assertEqual(f.CodeUri, codeUri)

class Test_API(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_API(self):
        # Arrange
        from sammy import API
        from sammy.custom_properties import CharForeignProperty
        from valley.properties import BooleanProperty, DictProperty
        # Example Taken from README.md
        stageName= 'dev'
        definitionUri='s3://your-bucket/your-swagger.yml'
        cacheClusterEnabled = False
        cacheClusterSize = None
        variables = {'SOME_Var': 'test'}

        # Act
        a = API(StageName=stageName,
                DefinitionUri=definitionUri,
                CacheClusterEnabled=cacheClusterEnabled,
                CacheClusterSize=cacheClusterSize,
                Variables=variables)

        # Assert
        self.assertEqual(a.StageName, stageName)
        self.assertEqual(a.DefinitionUri, definitionUri)
        self.assertEqual(a.CacheClusterEnabled, cacheClusterEnabled)
        self.assertEqual(a.CacheClusterSize, cacheClusterSize)
        self.assertEqual(a.Variables, variables)

class Test_SimpleTable(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_SimpleTable(self):
        # Arrange
        # Case Taken from README.md
        from sammy import SimpleTable
        from valley.properties import DictProperty
        name='maintable'
        primaryKey={'Name':'_id','Type':'String'}
        
        # Act
        ddb = SimpleTable(name=name,
                        PrimaryKey=primaryKey)

        # Assert
        self.assertEqual(ddb.name, name)
        self.assertEqual(ddb.PrimaryKey,primaryKey)

class Test_Ref(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    
    def test_Ref(self):
        # Arrange
        # Case Taken from README.md
        from sammy import Ref
        from valley.properties import CharProperty
        name= 'Bucket'

        # Act
        r = Ref(Ref=name)

        # Assert
        self.assertEqual(r.Ref,name)

if __name__ == '__main__':
    unittest.main()