## Design A Game: Hangman -- Shumei Lin

##Requirements:
 - Required python 2.7 and Firefox with protection disabled. 
 - Required installation of RandomWords python module. 
    In terminal, do: 
        git clone https://github.com/tomislater/RandomWords.git
        cd RandomWords
        python setup.py install

## Localhost Run Instructions:
In terminal(Mac) or Command Prompt(Windows) navigate to the project directory. 
Run the app with the devserver using dev_appserver.py DIR by typing dev_appserver.py app.yaml.
Ensure it's running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.

 
##Game Description:
Hangman is a simple guessing game. Each game begins with a random 'target'
word. 'Guesses' are sent to the `make_move` endpoint which will reply
with either: 'right guess', 'wrong guess', 'you win', or 'game over' (if the maximum
number of wrong guesses is reached). The 'make_move' endpoint will also partially 
reveal the target during the game. 
Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Play Game Instructions/Game Rules:
 - Go to localhost:8080/_ah/api/explorer. 
 - Go to hangman API in Services (protection needs to be disabled in Firefox).
 - Create a new user by going to the hangman.create_user endpoint. 
 - Create a new game with a user name by going to the hangman.new_game endpoint.
 - Go to hangman.make_move endpoint to start guessing (playing the game).
 - Each guess can only contain a single letter, otherwise an error message is displayed. 
 - The maximum number of wrong guesses is 6. When the number of wrong guesses reaches 6, game is over. 

## Score Keeping Explanation:
 - The Score model stores the number of guesses taken before the game has completed.
   The Score model also stores the number of missed letters of a game.  

##Score Ranking/High Scores:
 - The get_high_scores endpoint gives scores in ascending order of total number of guesses and total number of missed letters. 
 - Fewer guesses gives higher score rank with ties broken by number of missed letters (fewer missed letters gives higher score). 

##Player Ranking Explanation:
 - The get_user_rankings endpoint ranks players in descending order of wins/games percentage and number of total games completed of the player. 
 - Higher wins/games percentage gives higher player rank with ties broken by number of games completed (more games completed gives higher rank).

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 - __init__.py, dmails.dat, lorem_ipsum.dat, lorem_ipsum.py, nicknames.dat, 
   nouns.dat, random_words.py: Python RandomWords 0.1.5 module files.  

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. 
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms.
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage conforming game canceled or error.
    - Description: Cancel a game in progress. Will raise a NotFoundException if game does not exist.

- **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms
    - Description: Returns all of an individual User's active games. 
    Will raise a NotFoundException if user is not found.

- **get_high_scores**
    - Path: "scores/high_scores"
    - Method: GET
    - Parameters: number_of_results (optional)
    - Returns: ScoreForms
    - Description: Return scores in descending order of number of guesses and missed letters. A leader board. 
    Number of scores returned is limited by the optional parameter number_of_results.

- **get_user_rankings**
    - Path: "user_rankings"
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Return user rankings in descending order of win percentage and number of games played.

- **get_game_history**
    - Path: "game/{urlsafe_game_key}/history"
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistoryForm
    - Description: Return game history with each guess and result. 
    Will raise a NotFoundException if game is not found.


##Models Included:
 - **User**
    - Stores unique user_name, (optional) email address, and game performance information.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, missedLetters, correctLetters,
    usedLetters, game_over flag, message, user_name).
 - **GameForms**
    - Multiple GameForm container.
 - **NewGameForm**
    - Used to create a new game (user_name).
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses, missedLetters).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
 - **GameHistoryForm
    - Representation of a game's history information (urlsafe_key, game_over flag, 
    user_name, history).
 - **UserForm
    - Representation of a user's information (user_name, winning_percentage, total_games_played).
 - **UserForms
    - Multiple UserForm container.