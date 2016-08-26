import sys
import unittest

from dummy.lazy_action import Alpha, Beta

if sys.version_info >= (3, 3):
    from imagination.assembler.core import Assembler
    from imagination.debug          import dump_meta_container
    from imagination.exc            import UnexpectedParameterException, UndefinedContainerIDError, UndefinedDefaultValueException


class FunctionalTest(unittest.TestCase):
    """ This test is done via the assembler core. """
    def setUp(self):
        if sys.version_info < (3, 3):
            self.skipTest('The tested feature is not supported in Python {}.'.format(sys.version))

    def test_call_entity_with_missing_required_parameters(self):
        """ The constructor does not have all required parameters. """
        test_filepaths = [
            'test/data/locator-instantiation-error.xml',
        ]

        assembler = Assembler()
        assembler.load(*test_filepaths)

        self.assertRaises(UndefinedDefaultValueException, assembler.core.get, 'poow-1')

    def test_call_entity_with_unexpected_parameters(self):
        """ The constructor receives unexpected parameters. """
        test_filepaths = [
            'test/data/locator-with-unexpected-parameters.xml',
        ]

        assembler = Assembler()
        assembler.load(*test_filepaths)

        self.assertRaises(UnexpectedParameterException, assembler.core.get, 'dioe')

    def test_call_entity_with_unexpected_parameters(self):
        """ The constructor receives unexpected parameters. """
        test_filepaths = [
            'test/data/locator-with-undefined-entity.xml',
        ]

        assembler = Assembler()
        assembler.load(*test_filepaths)

        self.assertRaises(UndefinedContainerIDError, assembler.core.get, 'dioe')

    def test_call_undefined_entity(self):
        test_filepaths = [
            'test/data/locator-factorization.xml',
        ]

        assembler = Assembler()
        assembler.load(*test_filepaths)

        self.assertRaises(UndefinedContainerIDError, assembler.core.get, 'panda')
