"""CLI entrypoint for Genenote."""

import lionscliapp as app

from genenote import __version__
from genenote import app as genenote_app


def cmd_open():
    """Launch the Genenote GUI."""

    genenote_app.launch_app(app.execroot.get_execroot())


def declare_cli():
    """Declare the CLI application."""

    app.declare_app("genenote", __version__)
    app.describe_app("Creative genealogy notebook with a node canvas and filesystem-backed nodes.")
    app.declare_projectdir(".genenote")
    app.set_flag("search_upwards_for_project_dir", True)

    app.declare_cmd("", cmd_open)
    app.describe_cmd("", "Open the Genenote GUI")


def main():
    """Run the CLI application."""

    declare_cli()
    app.main()
