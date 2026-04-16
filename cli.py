"""Command-line entry point for jex."""

import sys

import click

from jex import __version__
from jex.app import JexApp, load_json


@click.command()
@click.argument("file", required=False, type=click.Path())
@click.version_option(version=__version__)
def main(file: str | None) -> None:
    """jex — interactive JSON explorer.

    Load a JSON file and browse it as a navigable tree.

    \b
    Examples:
      jex data.json
      curl -s https://api.example.com/users | jex
      jex -    # explicit stdin
    """
    try:
        data, source = load_json(file)
    except FileNotFoundError:
        click.echo(f"error: file not found: {file}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:  # type: ignore[name-defined]
        click.echo(f"error: invalid JSON — {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)

    JexApp(data=data, source=source).run()


# json is imported lazily above only to keep the error path tidy
import json  # noqa: E402

if __name__ == "__main__":
    main()
