import logging
import random

from testpaste.lib.base import *

log = logging.getLogger(__name__)

class GuessnumController(BaseController):

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        """A simple "Guess the number" game. A random integer between 1 and 100
        is chosen. The user is then presented with a form to guess a number and
        the controller. When he/she responds, we tell them if the number is to
        high or to low and repeat until they guess the correct number.
        
        This of course calls for multiple HTTP requests and responses going back
        and forth. Note that we don't use a traditional http session - just local
        variables and "web-continuations".
        """
        
        template = """
        %(message)s<br />
        You have guessed %(number_of_guesses)d times.<br />
        <form method="get" action="/guessnum">
        <input type="hidden" name="__wc" value="" />
        <input type="text" name="guess" />
        <input type="submit" value="Guess!" />
        </form>
        """
        if session.has_key('secret') and id != None:
            secret_number = session['secret']
            session['number_of_guesses'] += 1
            try:
                guess = int(request.params.get("guess", [None]))
                if guess < secret_number:
                    message = "You guessed %d - which is to low" % guess
                elif guess > secret_number:
                    message = "You guessed %d - which is to high" % guess
                else:
                    # They got it right so we're done
                    return """Yay - %d is the right number, you made it in %d guesses.<br />
                        <a href="/guessnum">Play again</a>""" % \
                        (guess, session['number_of_guesses'])
            except TypeError:
                guess = None
                message = "You must guess a number!"
            session.save()
        else:
            session['secret'] = random.randint(1,100)
            session['number_of_guesses'] = 0
            message = "Please start guessing numbers between 1 and 100 (both included)"
            session.save()
        
        return template % dict(
            message=message,
            number_of_guesses=session['number_of_guesses'],
        )
