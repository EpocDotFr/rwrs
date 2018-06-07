:information_source:️ `@rwrs stats username <database> <date>`

_{short_description}_

You can choose for which official (ranked) server type to get the data from using the `database` parameter. `date` can be provided to retrieve stats for a specific day (see below for the allowed formats). Remember stats are updated daily.

**Parameters:**

- `username`: required. Full username is required
- `database`: optional. One of `invasion` or `pacific`. Defaults to `invasion`
- `date`: optional. Defaults to none (gets current stats). Allowed values / formats:
    - `yesterday`
    - `1 day ago` / `{number} days ago`
    - `1 week ago` / `{number} weeks ago`
    - `1 month ago` / `{number} months ago`
    - `1 year ago` / `{number} years ago`
    - `{month name} {day number}`
    - `{month name} {day number} {year}`
    - `{month name} {day number}, {year}`
    - `{year}-{month number}-{day number}`
    - `{day number}/{month number}/{year}`