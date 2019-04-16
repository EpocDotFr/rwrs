:information_source:️ `@rwrs event action <name> <datetime> <server_ip_and_port>`

_{short_description}_

The event is shown at the top of every pages on the RWRS website.

**Parameters:**

- `action`: required. One of `set` or `remove`
- `name`: required if `action` is `set`. The name of the event
- `datetime`: required if `action` is `set`. Date and time when the event will begin. Format: `YYYY-MM-DD HH:mm ZZZ`
- `server_ip_and_port`: optional (but only available if `action` is `set`). The server IP and port where the event will take place. Format: `{{ip}}:{{port}}`