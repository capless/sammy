import unittest
import pathlib as pl
import os
import yaml

from sammy import SAM
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


if __name__ == '__main__':
    unittest.main()