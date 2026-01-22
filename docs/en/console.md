# Working with the console via `qtasks.__main__`

The `qtasks.__main__` module provides a command line interface for launching and
managing QTasks applications. The CLI is suitable for automation, production work,
and integration with external tools.

Available commands include:

* launching an application;
* viewing statistics via `(A)syncStats`;
* launching an experimental web interface (will be
  migrated to the `qtasks_webview` library).

---

## Main CLI features

* launching the application with the specified `QueueTasks` instance;
* calling component statistics (via `stats inspect`);
* launching the experimental web interface;
* specifying the application via `-A` or `--app` in the format `module:variable`;
* configuring the web interface port.

The command is called in the general form:

```bash
qtasks [options] <command> [options]
```

---

## `run` command

Starts the QTasks application with the specified `QueueTasks` instance.

```bash
qtasks -A <path_to_module:variable_name> run
```

Example:

```bash
qtasks -A based_async_app:app run
```

`-A` and `--app` are completely equivalent.

---

## `stats` command

Used to retrieve data from `(A)syncStats`.
Only the `inspect` subcommand is available in the current version.

```bash
qtasks -A <module:app> stats inspect <target> [parameters]
```

Where `target` is the statistics object:

* `app` — information about the application;
* `tasks` — information about tasks.

Example:

```bash
qtasks -A based_async_app:app stats inspect app json=true
```

The `json=true` parameter is passed as a *positional argument* to the `inspect`
function and enables output in JSON format.

The subcommands `inspect app` and `inspect tasks` directly call the methods:

* `(A)syncStats().inspect().app(json=True)`
* `(A)syncStats().inspect().tasks(json=True)`

The list of targets can be extended (`inspect workers`, `inspect broker`, etc.)
without changing the CLI.

---

## `web` command (experimental)

Launches an experimental web interface (will be moved to the
`qtasks_webview`).

```bash
qtasks web -A <module:app> --port <port>
```

Example:

```bash
qtasks web -A based_async_app:app --port 8000
```

If no port is specified, the default value of `8000` is used.

---

## CLI parameters

### `-A`, `--app`

The path to the application in the format:

```bash
module:variable_name
```

Example:

```bash
based_async_app:app
```

The CLI does not determine the application automatically — this behaviour is
intentional, as the developer may not use the global variable `app`.

### `--port`

Used only by the `web` command. Specifies the web interface port.

---

## Command help

For a complete list of parameters and help:

```bash
qtasks --help
```

For help on a command:

```bash
qtasks <command> --help
```

---

## Example

```bash
qtasks -A based_async_app:app run
qtasks -A based_async_app:app stats inspect tasks json=true
qtasks web -A based_async_app:app --port 8000
```
