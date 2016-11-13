# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameForms, UserForm, UserForms, GameHistoryForm
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
GET_HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1),)
GET_GAME_HISTORY_REQUEST = endpoints.ResourceContainer(
    GameHistoryForm,
    urlsafe_game_key=messages.StringField(1),)

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key)
        except ValueError:
            raise endpoints.BadRequestException('The word must contain '
                                                'only letters!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        # taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over is False:
                return game.to_form('Time to make a move!')
            else:
                return game.to_form("Game already over")
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if game.game_over:
            return game.to_form('Game already over!')

        guess = request.guess.lower()

        while len(game.missedLetters) < 6:

            if guess not in game.usedLetters:
                if len(guess) != 1:
                    msg = "Please enter a single letter!"

                elif guess not in "abcdefghijklmnopqrstuvwxyz":
                    msg = "Please enter a LETTER!"

                # right guess
                elif guess in game.target:

                    game.correctLetters += guess
                    game.put()
                    game.usedLetters += guess
                    game.put()

                    reveal_target = self.progress_updater(game)
                    msg = "Right guess! Target: " + reveal_target + \
                        ". Letters used: " + game.usedLetters + "."
                    game.add_game_history(guess, msg)

                    # player wins
                    if self.win(game):
                        game.end_game(True)
                        return game.to_form("You win! Target word is: " + game.target + ".")

                # wrong guess
                elif guess not in game.target:

                    game.missedLetters += guess
                    game.put()
                    game.usedLetters += guess
                    game.put()

                    reveal_target = self.progress_updater(game)
                    msg = "Wrong guess! Target: " + reveal_target + \
                        ". Letters used: " + game.usedLetters + "."
                    game.add_game_history(guess, msg)

            else:
                msg = "Your have already guessed that letter. Choose another one!"

            # out of number of wrong guesses
            if len(game.missedLetters) >= 6:
                game.end_game(False)
                return game.to_form("Game over! Target word is: " + game.target + ".")

            game.put()
            return game.to_form(msg)

    def progress_updater(self, game):
        """Helper function of make_move to partially reveal the target word"""
        blanks = "_" * len(game.target)
        for i in range(len(game.target)):
            if game.target[i] in game.correctLetters:
                blanks = blanks[:i] + game.target[i] + blanks[i + 1:]

        reveal_target = " ".join(blanks)
        return reveal_target

    def win(self, game):
        """Helper function of make_move to determine if player wins"""
        foundAllLetters = True
        for i in range(len(game.target)):
            if game.target[i] not in game.correctLetters:
                foundAllLetters = False
                break

        return foundAllLetters

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(Game.user == user.key).filter(
            Game.game_over == False)
        return GameForms(items=[game.to_form("Time to make a move!") for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path="game/{urlsafe_game_key}/cancel",
                      name="cancel_game",
                      http_method="DELETE")
    def cancel_game(self, request):
        """Cancel a game in progress."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return StringMessage(message="Cancel game failed! This game has completed!")
            else:
                # delete the game
                game.key.delete()
                return StringMessage(message="Game canceled!")
        else:
            raise endpoints.NotFoundException("Game not found!")

    @endpoints.method(request_message=GET_HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path="scores/high_scores",
                      name="get_high_scores",
                      http_method="GET")
    def get_high_scores(self, request):
        """Return scores in descending order of number of guesses and missed letters. 
           A leader board"""
        if request.number_of_results:
            scores = Score.query(Score.won == True).order(
                Score.guesses, Score.missedLetters).fetch(request.number_of_results)
        else:
            scores = Score.query(Score.won == True).order(
                Score.guesses, Score.missedLetters).fetch()
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=UserForms,
                      path="user_rankings",
                      name="get_user_rankings",
                      http_method="GET")
    def get_user_rankings(self, request):
        """Return user rankings in descending order of win percentage 
           and number of games played"""
        users = User.query().order(-User.percentage, -User.num_games).fetch()
        return UserForms(items=[user.to_form() for user in users])

    @endpoints.method(request_message=GET_GAME_HISTORY_REQUEST,
                      response_message=GameHistoryForm,
                      path="game/{urlsafe_game_key}/history",
                      name="get_game_history",
                      http_method="GET")
    def get_game_history(self, request):
        """Return game hisotry with each guess and result"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.history_to_form()

        else:
            raise endpoints.NotFoundException('Game not found!')

api = endpoints.api_server([HangmanApi])
