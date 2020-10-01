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

if __name__ == '__main__':
    unittest.main()