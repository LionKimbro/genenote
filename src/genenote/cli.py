"""CLI entrypoint for Genenote."""

import lionscliapp as app

from genenote import __version__
from genenote import app as genenote_app
from genenote import windows as genenote_windows


def cmd_open():
    """Launch the Genenote GUI."""

    genenote_app.launch_app(app.execroot.get_execroot())


def cmd_install():
    """Install Windows shell integration."""

    genenote_windows.command_install()
    print("Installed Genenote Windows integration.")


def cmd_base():
    """Create a Genenote launcher file in the target folder."""

    target_folder = app.ctx["path.target_folder"]
    launcher_path = genenote_windows.command_base(target_folder)
    print(f"Created {launcher_path}")


def declare_cli():
    """Declare the CLI application."""

    app.declare_app("genenote", __version__)
    app.describe_app("Creative genealogy notebook with a node canvas and filesystem-backed nodes.")
    app.declare_projectdir(".genenote")
    app.set_flag("search_upwards_for_project_dir", True)
    app.declare_key("path.target_folder", ".")
    app.describe_key("path.target_folder", "Target folder for commands such as base")

    app.declare_cmd("", cmd_open)
    app.describe_cmd("", "Open the Genenote GUI")
    app.declare_cmd("install", cmd_install)
    app.describe_cmd("install", "Install Windows file associations and Explorer integration")
    app.declare_cmd("base", cmd_base)
    app.describe_cmd("base", "Create base.genenote in a target folder")


def main():
    """Run the CLI application."""

    genenote_windows.intercept_genenote_launcher_invocation()
    if genenote_windows.maybe_handle_direct_command():
        return
    genenote_windows.rewrite_base_command_argv()
    declare_cli()
    app.main()
