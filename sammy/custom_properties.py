import json

from valley.exceptions import ValidationException
from valley.mixins import ListMixin
from valley.properties import BaseProperty, MultiProperty
from valley.utils.json_utils import ValleyEncoder
from valley.validators import ForeignListValidator, StringValidator, ForeignValidator, IntegerValidator


class ForeignSubclassListValidator(ForeignListValidator):

    def validate(self, value, key):
        if value:
            for obj in value:
                if not issubclass(obj.__class__,self.foreign_class):
                    raise ValidationException(
                        '{0}: This value ({1}) should be an instance of {2}.'.format(
                            key, obj, self.foreign_class.__name__)
                    )



class ForeignSubclassListMixin(ListMixin):

    def get_validators(self):
        super(ForeignSubclassListMixin, self).get_validators()
        self.validators.insert(len(self.validators),ForeignSubclassListValidator(self.foreign_class))

    def get_db_value(self, value):
        if self.return_type == 'single':
            if not self.return_prop:
                raise ValueError('ForeignProperty classes requires the '
                    'return_prop argument if return_type equals "single"')
            return value._data[self.return_prop]
        if self.return_type == 'list':
            return [obj._data for obj in value]
        if self.return_type == 'json':
            return json.dumps(value, cls=ValleyEncoder)
        else:
            return value


class ForeignInstanceListProperty(ForeignSubclassListMixin,BaseProperty):

    def __init__(self,foreign_class,return_type=None,return_prop=None,**kwargs):
        self.foreign_class = foreign_class
        super(ForeignInstanceListProperty, self).__init__(**kwargs)
        self.return_type = return_type
        self.return_prop = return_prop


class CharForeignProperty(MultiProperty):

    def __init__(self,foreign_class,**kwargs):

        super(CharForeignProperty, self).__init__(
            validators=[ForeignValidator(foreign_class),
                        StringValidator()],**kwargs)


class IntForeignProperty(MultiProperty):

    def __init__(self,foreign_class,**kwargs):

        super(IntForeignProperty, self).__init__(
            validators=[ForeignValidator(foreign_class),
                        IntegerValidator()],**kwargs)