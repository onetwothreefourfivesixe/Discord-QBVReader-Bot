TEXT = {
    "help": [
        """
            Starts a new game in the voice channel.
            You must be connected to a voice channel.
            Limits: Only one game can be started at a time.

            **Category Inputs**:
            The categories specify the type of questions to include in the game. Use the following format:
            `!play <categories> <difficulty>`

            **Available Categories**:
            - sci (science)
            - hist (history)
            - lit (literature)
            - geo (geography)
            - myth (mythology)
            - fa (fine arts)
            - phil (philosophy)
            - tr (trash)
            - rel (religion)
            - ss (social science)

            **Difficulty Levels**:
            - 1 to 10

            **Example Usage**:
            `!play sci,hist 4,5,6`
            `!play lit 8`

            Note: If no categories or difficulty are specified, the default is 'all' for categories and all for difficulties.
        """,

        """
            Adds the user to the current game. The player must add themselves with this command.
            Limits: Cannot add users if the game has not started yet.

            **Example Usage**:
            `!add`
        """,

        """
            Starts the tossup round of the game.
            Limits: Must be called in the correct channel and after players have joined the game.

            **Example Usage**:
            `!start`
        """,

        """
            Buzz in to answer the current tossup question.
            Limits: Only the player who buzzed in can answer. Cannot buzz if a tossup is not active.

            **Example Usage**:
            Type `buzz` in the chat while a tossup is active.
        """,

        """
            Submit your answer to the current tossup question.
            Limits: Only the player who buzzed in can answer; the game must be active.

            **Example Usage**:
            Simply type your answer in the chat after buzzing in.
        """,

        """
            Move to the next tossup question in the game.
            Limits: Must be called after a tossup has ended and only if the game is active.

            **Example Usage**:
            `!next`
        """,

        """
            Displays the current scores of all players in the game.
            Limits: Cannot be called while a tossup is being answered or if the game hasn't started.

            **Example Usage**:
            `!getscores`
        """,

        """
        Displays the current settings of the game (More to be added soon):
                - Categories: The current categories being read
                - Diffi: The current difficulties being read
            Limits: Cannot be called while a tossup is being answered or if the game hasn't started.

            **Example Usage**:
            `!getinfo`
        """,

        """
            Displays the current scores of all players in the game one last time before ending the game.
            Limits: Cannot be called if a game has not been started yet.

            **Example Usage**:
            `!end`
        """
    ],
    "error": {
        "no_voice_channel": "You are not connected to a voice channel.",
        "not_joined": "{user} has not joined the game.",
        "wrong_channel": "Wrong channel! Use commands in {channel}.",
        "game_not_started": "No game has been started yet.",
        "already_started": "The game has already started.",
        "cannot_buzz": "You cannot buzz right now.",
        "buzzed_in": "A tossup is being answered right now.",
        "failed_to_start": "Failed to start the game.",
        "something_wrong": "Something went wrong! If this issue occurs again, please fill out this form: https://forms.gle/fLd6r4yZGRyaRDnw6",
        "cannot_use_command": "You are not allowed to use this command right now.",
        "failed_to_add": "Failed to add player to the game."
    },
    "game": {
        "initialized": "Game started successfully! You have successfully initialized a game! Note, to start the game, type !start. To buzz on a question, type 'buzz'. To answer a question after buzzing, type [your answer], with no commands. To add another player to the game, the user must type !add while a game is running to add themselves.",
        "reading_tossup": "Reading tossup.",
        "buzzed_in": "{user} has buzzed in. Answer?",
        "player_added": "{user} has been added to the game!",
        "scores": "Scores:\n{scores}",
        "final_scores": "Final Scores: {scores}",
        "game_info": "Number of Tossups read: {tossups}\nCategories: {categories}\nDifficulties: {difficulties}",
        "connected": "Connected? {status}",
        "shutdown": "Bot is shutting down..."
    }
}
