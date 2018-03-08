❓ **The parameters order is important**, unless otherwise stated. If a parameter contains one or more spaces, **you'll have to surround it with double or simple quotes**. Here's the common valid parameters values:

- `sort`: `score`, `xp`, `kills`, `deaths`, `ratio`, `streak`, `tk`, `heals`, `shots`, `distance`, `throws`, `vehicles`, `targets`, `time`

- `database`: `invasion`, `pacific`

**Commands list:**

- `stats` (alias: `statistics`): displays stats about the specified player. Parameters:
    - `username`: required. Full username is required
    - `database`: optional. Defaults to `invasion`

- `whereis` (aliases: `where is`, `where`): displays information about the server the specified player is currently playing on. Parameters:
    - `username`: required. Full username isn't required

- `server`: displays information about the specified server. Parameters:
    - `name`: required. Full server name isn't required

- `servers`: displays the first 10 currently active servers. Options (order doesn't matter):
    - `--ranked`: only return ranked (official) servers
    - `--not-full`: only return servers with room

- `top` (alias: `leaderboard`): displays the top 15 players. Parameters:
    - `sort`: optional. Defaults to `score`
    - `database`: optional. Defaults to `invasion`

- `pos` (aliases: `position`, `ranking`): highlights the specified player in the leaderboard. Parameters:
    - `username`: required. Full username is required
    - `sort`: optional. Defaults to `score`
    - `database`: optional. Defaults to `invasion`

- `now` (alias: `currently`): displays numbers about the current players and servers.

- `status`: displays the current status of the online multiplayer.

- `info`: displays information about the bot.

- `help`: what you are reading right now.