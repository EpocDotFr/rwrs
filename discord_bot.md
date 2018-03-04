ℹ️ Here's the available commands. **The parameters order is important**, unless otherwise stated.

- **!stats** (alias: **!statistics**): displays stats about the specified player. Parameters:
    - **username**: required. Full username is required
    - **database**: optional, one of **invasion** or **pacific**. Defaults to **invasion**

- **!whereis** (aliases: **!where is**, **!where**): displays information about the server the specified player is currently playing on. Parameters:
    - **username**: required. Giving full username isn't required

- **!server**: displays information about the specified server. Parameters:
    - **name**: required. Giving full server name isn't required

- **!now** (alias: **!currently**): displays numbers about the current players and servers.

- **!status**: displays the current status of the online multiplayer.

- **!servers**: displays the first 10 currently active servers. Options (order doesn't matter):
    - **--ranked**: only return ranked (official) servers
    - **--not-full**: only return servers with room

- **!top** (alias: **!leaderboard**): displays the top players, ordered by score. Parameters:
    - **database**: optional, one of **invasion** or **pacific**. Defaults to **invasion**

- **!pos** (aliases: **!position**, **!rank**): highlights the specified player in the leaderboard, ordered by score. Parameters:
    - **username**: required. Full username is required
    - **database**: optional, one of **invasion** or **pacific**. Defaults to **invasion**