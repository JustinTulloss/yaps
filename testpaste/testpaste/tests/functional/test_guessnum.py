from testpaste.tests import *

class TestGuessnumController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='guessnum'))
        # Test response...
