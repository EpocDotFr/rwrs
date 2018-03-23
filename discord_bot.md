**ℹ️ Read first**

- The parameters order is important
- Parameters containing spaces **must be surrounded by `"` or  `'`**
- Usernames starting with a `-` **must be directly prepended with a `\`**

Valid common parameters values are:

- `sort`: `score`, `xp`, `kills`, `deaths`, `ratio`, `streak`, `tk`, `heals`, `shots`, `distance`, `throws`, `vehicles`, `targets`, `time`

- `database`: `invasion`, `pacific`

**📄 Commands list**

- `stats`: displays stats about the specified player. Parameters:
    - `username`: required. Full username is required
    - `database`: optional. Defaults to `invasion`

- `top`: displays the top 24 players. Parameters:
    - `sort`: optional. Defaults to `score`
    - `database`: optional. Defaults to `invasion`

- `pos`: highlights the specified player in the leaderboard. Parameters:
    - `username`: required. Full username is required
    - `sort`: optional. Defaults to `score`
    - `database`: optional. Defaults to `invasion`

- `compare`: compare stats of two players. Parameters:
    - `source_username`: required. Full username is required
    - `target_username`: required. Full username is required
    - `database`: optional. Defaults to `invasion`

- `whereis`: displays information about the server the specified player is currently playing on. Parameters:
    - `username`: required. Full username isn't required

- `server`: displays information about the specified server. Parameters:
    - `name`: required. Full server name isn't required

- `servers`: displays the first 10 currently active servers with room.
    - Parameters:
        - `type`: optional. Filter servers by game type. One of `vanilla`, `pacific` or `rwd`. Defaults to none
    - Options (order doesn't matter):
        - `--ranked`: only return ranked (official) servers

- `now`: displays numbers about the current players and servers.

- `status`: displays the current status of the online multiplayer.

- `info`: displays information about the bot.