"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb
from random_words import RandomWords


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    num_wins = ndb.IntegerProperty(required=True, default=0)
    num_games = ndb.IntegerProperty(required=True, default=0)
    percentage = ndb.FloatProperty(required=True, default=0.0)

    def to_form(self):
        return UserForm(user_name=self.name,
                        winning_percentage=self.percentage,
                        total_games_completed=self.num_games)


class Game(ndb.Model):
    """Game object"""
    target = ndb.StringProperty(required=True)
    missedLetters = ndb.StringProperty(required=True, default="")
    correctLetters = ndb.StringProperty(required=True, default="")
    usedLetters = ndb.StringProperty(required=True, default="")
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    history = ndb.PickleProperty(required=True, default=[])

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        # select a random word
        rw = RandomWords()
        word = rw.random_word()
        game = Game(user=user,
                    target=word,
                    missedLetters="",
                    correctLetters="",
                    usedLetters="",
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.missedLetters = self.missedLetters
        form.correctLetters = self.correctLetters
        form.usedLetters = self.usedLetters
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()

        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=len(self.usedLetters),
                      missedLetters=len(self.missedLetters))
        score.put()

        # update user num_wins, num_games and percentage information
        if (won):
            self.user.get().num_wins += 1
            self.user.get().put()

        self.user.get().num_games += 1
        self.user.get().put()
        self.user.get().percentage = float(
            float(self.user.get().num_wins) / float(self.user.get().num_games))
        self.user.get().put()

    def add_game_history(self, guess, result):
        """Update game hisotry information"""
        self.history.append({"Guess": str(guess), "Result": str(result)})
        self.put()

    def history_to_form(self):
        """Returns a GameHistoryForm representation of the Game History"""
        form = GameHistoryForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.game_over = self.game_over
        form.history = str(self.history)
        return form


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    missedLetters = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses,
                         missedLetters=self.missedLetters)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    missedLetters = messages.StringField(2, required=True)
    correctLetters = messages.StringField(3, required=True)
    usedLetters = messages.StringField(4, required=True)
    game_over = messages.BooleanField(5, required=True)
    message = messages.StringField(6, required=True)
    user_name = messages.StringField(7, required=True)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)
    missedLetters = messages.IntegerField(5, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class GameHistoryForm(messages.Message):
    """Game Histor Form outbound game history information"""
    urlsafe_key = messages.StringField(1)
    game_over = messages.BooleanField(2)
    user_name = messages.StringField(3)
    history = messages.StringField(4)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


class UserForm(messages.Message):
    """UserForm for outbound User's performance information"""
    user_name = messages.StringField(1, required=True)
    winning_percentage = messages.FloatField(2, required=True)
    total_games_completed = messages.IntegerField(3, required=True)


class UserForms(messages.Message):
    """Return multiple UserForms"""
    items = messages.MessageField(UserForm, 1, repeated=True)
