"""Tk application for Genenote."""

import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk

import tkinterdnd2

from genenote import nodebrowser
from genenote import projectio


WINDOW_TITLE = "Genenote"
WINDOW_GEOMETRY = "1400x900"


def launch_app(execroot):
    """Launch the standalone application."""

    state = create_state(execroot)
    root = tkinterdnd2.Tk()
    build_window(state, root)
    root.mainloop()


def create_state(execroot):
    """Create mutable app state."""

    project_dir = Path(execroot) / ".genenote"
    projectio.ensure_project_structure(project_dir)

    return {
        "execroot": Path(execroot),
        "project_dir": project_dir,
        "project_viewport": projectio.load_project_viewport(project_dir),
        "graph_data": projectio.load_project_graph(project_dir),
        "root": None,
        "window": None,
        "widgets": {},
        "selected_node_id": None,
        "selected_attachment_path": None,
        "current_detail_node_id": None,
        "status_text": None,
    }


def build_window(state, root):
    """Build the top-level Tk window."""

    state["root"] = root

    if isinstance(root, tk.Tk) and root.state() != "withdrawn":
        window = root
        window.title(WINDOW_TITLE)
        window.geometry(WINDOW_GEOMETRY)
    else:
        window = tk.Toplevel(root)
        window.title(WINDOW_TITLE)
        window.geometry(WINDOW_GEOMETRY)

    state["window"] = window
    window.protocol("WM_DELETE_WINDOW", lambda: handle_close(state))

    _build_menubar(state)
    _build_layout(state)
    _configure_file_drop(state)
    _configure_nodebrowser(state)
    _bind_global_shortcuts(state)
    refresh_detail_pane(state)
    return window


def destroy_window(state):
    """Destroy the current app window."""

    window = state.get("window")
    if window is None or not window.winfo_exists():
        return
    commit_detail_changes(state)
    window.destroy()
    state["window"] = None


def handle_close(state):
    """Persist detail changes and close the UI."""

    commit_detail_changes(state)
    state["window"].destroy()


def _build_menubar(state):
    """Build the main application menubar."""

    window = state["window"]
    menubar = tk.Menu(window)

    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(
        label="Quit",
        accelerator="Ctrl+Q",
        command=lambda: handle_close(state),
    )
    menubar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(
        label="How To Make Nodes",
        accelerator="F1",
        command=lambda: show_node_help_window(state),
    )
    menubar.add_cascade(label="Help", menu=help_menu)

    window.configure(menu=menubar)
    state["widgets"]["menubar"] = menubar


def _bind_global_shortcuts(state):
    """Bind top-level keyboard shortcuts."""

    window = state["window"]
    window.bind("<Control-q>", lambda event: handle_quit_shortcut(state, event))
    window.bind("<F1>", lambda event: handle_help_shortcut(state, event))


def _build_layout(state):
    window = state["window"]

    style = ttk.Style(window)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    main = ttk.Frame(window, padding=10)
    main.grid(row=0, column=0, sticky="nsew")
    window.rowconfigure(0, weight=1)
    window.columnconfigure(0, weight=1)

    pane = ttk.Panedwindow(main, orient="horizontal")
    pane.grid(row=0, column=0, sticky="nsew")
    main.rowconfigure(0, weight=1)
    main.columnconfigure(0, weight=1)

    browser_frame = ttk.Frame(pane, padding=(0, 0, 10, 0))
    detail_frame = ttk.Frame(pane, padding=(10, 0, 0, 0))
    pane.add(browser_frame, weight=3)
    pane.add(detail_frame, weight=2)

    browser_frame.rowconfigure(0, weight=1)
    browser_frame.columnconfigure(0, weight=1)
    detail_frame.rowconfigure(1, weight=1)
    detail_frame.columnconfigure(0, weight=1)

    canvas = tk.Canvas(browser_frame, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")

    placeholder = ttk.Label(
        detail_frame,
        text="Select a node to view or edit it.",
        justify="left",
    )
    placeholder.grid(row=0, column=0, sticky="nw", pady=(12, 0))

    form = ttk.Frame(detail_frame)
    form.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
    form.columnconfigure(0, weight=1)
    form.rowconfigure(6, weight=1)

    title_label = ttk.Label(form, text="Title")
    title_label.grid(row=0, column=0, sticky="w")

    title_var = tk.StringVar()
    title_entry = ttk.Entry(form, textvariable=title_var, font=("TkDefaultFont", 14))
    title_entry.grid(row=1, column=0, sticky="ew", pady=(4, 10))
    title_var.trace_add("write", lambda *_: handle_title_changed(state))

    materialize_button = ttk.Button(
        form,
        text="CREATE FOLDER",
        command=lambda: handle_materialize_node(state),
    )
    materialize_button.grid(row=2, column=0, sticky="w", pady=(0, 10))

    created_var = tk.StringVar()
    created_label = ttk.Label(form, textvariable=created_var)
    created_label.grid(row=3, column=0, sticky="w", pady=(0, 10))

    path_row = ttk.Frame(form)
    path_row.grid(row=4, column=0, sticky="ew", pady=(0, 10))
    path_row.columnconfigure(0, weight=1)

    folder_path_var = tk.StringVar()
    folder_path_label = ttk.Label(path_row, textvariable=folder_path_var)
    folder_path_label.grid(row=0, column=0, sticky="ew")

    copy_path_button = ttk.Button(
        path_row,
        text="copy",
        command=lambda: copy_text_to_clipboard(state, folder_path_var.get()),
    )
    copy_path_button.grid(row=0, column=1, padx=(8, 0))

    open_path_button = ttk.Button(
        path_row,
        text="open",
        command=lambda: open_path(folder_path_var.get()),
    )
    open_path_button.grid(row=0, column=2, padx=(8, 0))

    notes_header = ttk.Frame(form)
    notes_header.grid(row=5, column=0, sticky="w")

    notes_label = ttk.Label(notes_header, text="Notes")
    notes_label.grid(row=0, column=0, sticky="w")

    copy_notes_button = ttk.Button(
        notes_header,
        text="copy",
        command=lambda: copy_notes_path(state),
    )
    copy_notes_button.grid(row=0, column=1, padx=(8, 0))

    open_notes_button = ttk.Button(
        notes_header,
        text="open",
        command=lambda: open_notes_path(state),
    )
    open_notes_button.grid(row=0, column=2, padx=(8, 0))

    notes_text = tk.Text(form, height=10, wrap="word")
    notes_text.grid(row=6, column=0, sticky="nsew", pady=(4, 10))
    notes_text.bind("<Control-Return>", lambda event: handle_notes_save_shortcut(state, event))

    attachments_header = ttk.Frame(form)
    attachments_header.grid(row=7, column=0, sticky="ew")

    attachments_label = ttk.Label(attachments_header, text="Attachments")
    attachments_label.grid(row=0, column=0, sticky="w")

    copy_attachments_folder_button = ttk.Button(
        attachments_header,
        text="copy",
        command=lambda: copy_attachments_folder_path(state),
    )
    copy_attachments_folder_button.grid(row=0, column=1, padx=(8, 0))

    open_attachments_folder_button = ttk.Button(
        attachments_header,
        text="open",
        command=lambda: open_attachments_folder(state),
    )
    open_attachments_folder_button.grid(row=0, column=2, padx=(8, 0))

    attachments_frame = ttk.Frame(form)
    attachments_frame.grid(row=8, column=0, sticky="nsew", pady=(4, 10))
    attachments_frame.columnconfigure(0, weight=1)
    attachments_frame.rowconfigure(0, weight=1)

    attachments_tree = ttk.Treeview(
        attachments_frame,
        columns=("path",),
        show="tree",
        selectmode="browse",
        height=8,
    )
    attachments_tree.grid(row=0, column=0, sticky="nsew")
    attachments_tree.bind("<<TreeviewSelect>>", lambda event: handle_attachment_selected(state))
    attachments_tree.bind("<Double-1>", lambda event: handle_attachment_double_click(state, event))

    attachment_buttons = ttk.Frame(attachments_frame)
    attachment_buttons.grid(row=0, column=1, sticky="ns", padx=(8, 0))

    copy_attachment_button = ttk.Button(
        attachment_buttons,
        text="copy",
        command=lambda: copy_selected_attachment_path(state),
    )
    copy_attachment_button.grid(row=0, column=0, sticky="ew")

    open_attachment_button = ttk.Button(
        attachment_buttons,
        text="open",
        command=lambda: open_selected_attachment(state),
    )
    open_attachment_button.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    save_button = ttk.Button(
        form,
        text="save",
        command=lambda: save_selected_node(state),
    )
    save_button.grid(row=9, column=0, sticky="w")

    state["status_text"] = tk.StringVar(master=window, value="Ready.")
    status_label = ttk.Label(main, textvariable=state["status_text"])
    status_label.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    state["widgets"].update(
        {
            "canvas": canvas,
            "placeholder": placeholder,
            "form": form,
            "title_var": title_var,
            "title_entry": title_entry,
            "materialize_button": materialize_button,
            "created_var": created_var,
            "created_label": created_label,
            "path_row": path_row,
            "folder_path_var": folder_path_var,
            "notes_header": notes_header,
            "notes_label": notes_label,
            "copy_notes_button": copy_notes_button,
            "open_notes_button": open_notes_button,
            "notes_text": notes_text,
            "attachments_label": attachments_label,
            "attachments_header": attachments_header,
            "attachments_frame": attachments_frame,
            "attachments_tree": attachments_tree,
            "copy_path_button": copy_path_button,
            "open_path_button": open_path_button,
            "copy_attachments_folder_button": copy_attachments_folder_button,
            "open_attachments_folder_button": open_attachments_folder_button,
            "copy_attachment_button": copy_attachment_button,
            "open_attachment_button": open_attachment_button,
            "save_button": save_button,
        }
    )


def _configure_nodebrowser(state):
    canvas = state["widgets"]["canvas"]
    nodebrowser.reset_runtime()
    nodebrowser.use_graph_data(state["graph_data"])
    nodebrowser.set_viewport(
        state["project_viewport"]["x"],
        state["project_viewport"]["y"],
    )
    nodebrowser.use_canvas(canvas)
    nodebrowser.set_callback("generate_node_id", lambda: generate_node_id(state))
    nodebrowser.set_callback(
        "on_single_selection_changed",
        lambda node_id: handle_single_selection_changed(state, node_id),
    )
    nodebrowser.set_callback(
        "on_graph_mutated",
        lambda: handle_graph_mutated(state),
    )
    nodebrowser.set_callback(
        "on_viewport_changed",
        lambda offset_x, offset_y: handle_viewport_changed(state, offset_x, offset_y),
    )


def handle_quit_shortcut(state, event):
    """Close the app from the keyboard."""

    handle_close(state)
    return "break"


def handle_help_shortcut(state, event):
    """Open the node-browser help window from the keyboard."""

    show_node_help_window(state)
    return "break"


def _configure_file_drop(state):
    """Register file-drop handling across the application surface."""

    window = state["window"]
    if not hasattr(window, "drop_target_register"):
        return

    for widget in iter_drop_widgets(window):
        if not hasattr(widget, "drop_target_register"):
            continue
        try:
            widget.drop_target_register(tkinterdnd2.DND_FILES)
            widget.dnd_bind("<<Drop>>", lambda event: handle_drop_files(state, event))
        except tk.TclError:
            return


def handle_single_selection_changed(state, node_id):
    """React to canvas selection changes."""

    commit_detail_changes(state)
    state["selected_node_id"] = node_id
    refresh_detail_pane(state)


def handle_graph_mutated(state):
    """Persist graph-level changes that affect the filesystem project."""

    projectio.write_project_graph(state["project_dir"], state["graph_data"])
    refresh_detail_pane(state)
    set_status(state, "Graph updated.")


def handle_viewport_changed(state, offset_x, offset_y):
    """Persist viewport movement."""

    state["project_viewport"]["x"] = offset_x
    state["project_viewport"]["y"] = offset_y
    projectio.save_project_viewport(state["project_dir"], offset_x, offset_y)


def handle_drop_files(state, event):
    """Handle dropping files anywhere on the app."""

    node_id = state.get("selected_node_id")
    if node_id is None:
        set_status(state, "Select a node before dropping files.")
        return "break"

    node = state["graph_data"]["nodes"].get(node_id)
    if node is None:
        set_status(state, "Selected node is no longer available.")
        return "break"

    file_paths = [path for path in state["window"].tk.splitlist(event.data) if Path(path).is_file()]
    if not file_paths:
        set_status(state, "Drop one or more files to attach them.")
        return "break"

    if not node.get("materialized"):
        node["title"] = state["widgets"]["title_var"].get().strip() or node_id
        projectio.materialize_node(state["project_dir"], node)
        projectio.save_materialized_node(state["project_dir"], node_id, node["title"], "")
        projectio.write_project_graph(state["project_dir"], state["graph_data"])
    else:
        save_selected_node(state)

    copied = projectio.copy_files_into_node_attachments(state["project_dir"], node_id, file_paths)
    refresh_detail_pane(state)
    if copied:
        select_attachment_path(state, copied[-1])
    nodebrowser.redraw_all()
    if copied:
        set_status(state, f"Attached {len(copied)} file(s) to {node_id}.")
    else:
        set_status(state, "No files were attached.")
    return "break"


def refresh_detail_pane(state):
    """Refresh the right-hand pane to match the current selection."""

    widgets = state["widgets"]
    node_id = state["selected_node_id"]
    state["current_detail_node_id"] = node_id

    if node_id is None or node_id not in state["graph_data"]["nodes"]:
        widgets["placeholder"].grid()
        widgets["form"].grid_remove()
        state["selected_attachment_path"] = None
        return

    widgets["placeholder"].grid_remove()
    widgets["form"].grid()

    node = state["graph_data"]["nodes"][node_id]
    widgets["title_var"].set(node.get("title", ""))

    if node.get("materialized"):
        detail = projectio.load_materialized_node_detail(state["project_dir"], node_id)
        widgets["created_var"].set(format_created_text(detail["node_json"].get("created_at")))
        widgets["folder_path_var"].set(detail["folder_path"])
        set_text_widget(widgets["notes_text"], detail["notes_text"])
        populate_attachments(state, detail["attachments"])
        widgets["materialize_button"].grid_remove()
        widgets["created_label"].grid()
        widgets["path_row"].grid()
        widgets["notes_header"].grid()
        widgets["notes_text"].grid()
        widgets["attachments_header"].grid()
        widgets["attachments_frame"].grid()
        widgets["save_button"].state(["!disabled"])
        widgets["save_button"].grid()
        widgets["notes_text"].configure(state="normal")
    else:
        widgets["created_var"].set("")
        widgets["folder_path_var"].set("")
        set_text_widget(widgets["notes_text"], "")
        populate_attachments(state, [])
        widgets["materialize_button"].grid()
        widgets["created_label"].grid_remove()
        widgets["path_row"].grid_remove()
        widgets["notes_header"].grid_remove()
        widgets["notes_text"].grid_remove()
        widgets["attachments_header"].grid_remove()
        widgets["attachments_frame"].grid_remove()
        widgets["save_button"].state(["disabled"])
        widgets["save_button"].grid_remove()
        widgets["notes_text"].configure(state="disabled")


def handle_title_changed(state):
    """Keep graph_data titles in sync with the detail pane."""

    node_id = state["current_detail_node_id"]
    if node_id is None:
        return
    if node_id not in state["graph_data"]["nodes"]:
        return

    title = state["widgets"]["title_var"].get().strip()
    state["graph_data"]["nodes"][node_id]["title"] = title
    nodebrowser.redraw_all()


def handle_materialize_node(state):
    """Create the selected node's folder and files."""

    node_id = state["selected_node_id"]
    if node_id is None:
        return

    node = state["graph_data"]["nodes"].get(node_id)
    if node is None:
        return

    node["title"] = state["widgets"]["title_var"].get().strip() or node_id
    projectio.materialize_node(state["project_dir"], node)
    projectio.save_materialized_node(state["project_dir"], node_id, node["title"], "")
    projectio.write_project_graph(state["project_dir"], state["graph_data"])
    nodebrowser.redraw_all()
    refresh_detail_pane(state)
    set_status(state, f"Materialized {node_id}.")


def save_selected_node(state):
    """Save the currently selected materialized node."""

    node_id = state["selected_node_id"]
    if node_id is None:
        return

    node = state["graph_data"]["nodes"].get(node_id)
    if node is None or not node.get("materialized"):
        return

    title = state["widgets"]["title_var"].get().strip() or node_id
    notes_text = state["widgets"]["notes_text"].get("1.0", "end-1c")
    node["title"] = title
    projectio.save_materialized_node(state["project_dir"], node_id, title, notes_text)
    projectio.write_project_graph(state["project_dir"], state["graph_data"])
    nodebrowser.redraw_all()
    refresh_detail_pane(state)
    set_status(state, f"Saved {node_id}.")


def handle_notes_save_shortcut(state, event):
    """Save the selected node from the notes editor."""

    save_selected_node(state)
    return "break"


def show_node_help_window(state):
    """Show node-browser help in a simple Toplevel."""

    existing = state["widgets"].get("help_window")
    if existing is not None and existing.winfo_exists():
        existing.lift()
        existing.focus_set()
        return

    window = tk.Toplevel(state["window"])
    window.title("How To Make Nodes")
    window.geometry("560x360")
    window.transient(state["window"])

    frame = ttk.Frame(window, padding=10)
    frame.grid(row=0, column=0, sticky="nsew")
    window.rowconfigure(0, weight=1)
    window.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    text = tk.Text(frame, wrap="word")
    text.grid(row=0, column=0, sticky="nsew")
    text.insert("1.0", build_node_help_text())
    text.configure(state="disabled")

    close_button = ttk.Button(frame, text="close", command=window.destroy)
    close_button.grid(row=1, column=0, sticky="e", pady=(10, 0))

    state["widgets"]["help_window"] = window
    window.protocol("WM_DELETE_WINDOW", window.destroy)


def build_node_help_text():
    """Return help text for the node browser."""

    return (
        "How To Make Nodes\n\n"
        "Add a node:\n"
        "- Double-click empty canvas space to create a node there.\n"
        "- Or press 'n' to enter node creation mode, then click empty space.\n\n"
        "Connect or disconnect nodes:\n"
        "- Hold Shift.\n"
        "- Press on a source node and drag toward another node.\n"
        "- Release over the target node.\n"
        "- If no edge exists, this creates one.\n"
        "- If an edge already exists, this removes it.\n\n"
        "Other useful things:\n"
        "- Click a node to select it.\n"
        "- Drag a node to move it.\n"
        "- Drag on empty space to marquee-select nodes.\n"
        "- Hold Shift and drag empty space to pan the viewport.\n"
    )


def iter_drop_widgets(root_widget):
    """Yield the application widgets that should accept file drops."""

    yield root_widget
    for child in root_widget.winfo_children():
        yield from iter_drop_widgets(child)


def commit_detail_changes(state):
    """Commit the current editor state before changing selection or closing."""

    node_id = state.get("current_detail_node_id")
    if node_id is None:
        return
    if node_id not in state["graph_data"]["nodes"]:
        return

    node = state["graph_data"]["nodes"][node_id]
    title = state["widgets"]["title_var"].get().strip()
    node["title"] = title

    if node.get("materialized"):
        notes_text = state["widgets"]["notes_text"].get("1.0", "end-1c")
        projectio.save_materialized_node(state["project_dir"], node_id, title or node_id, notes_text)
        projectio.write_project_graph(state["project_dir"], state["graph_data"])


def populate_attachments(state, attachments):
    """Refresh the attachments tree."""

    tree = state["widgets"]["attachments_tree"]
    tree.delete(*tree.get_children())
    state["selected_attachment_path"] = None

    for item in attachments:
        tree.insert("", "end", iid=item["path"], text=item["name"])

    attachment_buttons_enabled = "disabled" if not attachments else "!disabled"
    state["widgets"]["copy_attachment_button"].state([attachment_buttons_enabled])
    state["widgets"]["open_attachment_button"].state([attachment_buttons_enabled])


def handle_attachment_selected(state):
    """Track the selected attachment path."""

    tree = state["widgets"]["attachments_tree"]
    selection = tree.selection()
    state["selected_attachment_path"] = selection[0] if selection else None


def handle_attachment_double_click(state, event):
    """Open the selected attachment on double-click."""

    handle_attachment_selected(state)
    open_selected_attachment(state)


def select_attachment_path(state, attachment_path):
    """Select one attachment row in the tree if it exists."""

    tree = state["widgets"]["attachments_tree"]
    if not tree.exists(attachment_path):
        return

    tree.selection_set(attachment_path)
    tree.focus(attachment_path)
    tree.see(attachment_path)
    state["selected_attachment_path"] = attachment_path


def copy_selected_attachment_path(state):
    path = state.get("selected_attachment_path")
    if not path:
        return
    copy_text_to_clipboard(state, path)
    set_status(state, "Copied attachment path.")


def open_selected_attachment(state):
    path = state.get("selected_attachment_path")
    if not path:
        return
    open_path(path)


def copy_notes_path(state):
    path = get_notes_path(state)
    if path is None:
        return
    copy_text_to_clipboard(state, path)
    set_status(state, "Copied notes path.")


def open_notes_path(state):
    path = get_notes_path(state)
    if path is None:
        return
    open_path(path)


def copy_attachments_folder_path(state):
    path = get_attachments_folder_path(state)
    if path is None:
        return
    copy_text_to_clipboard(state, path)
    set_status(state, "Copied attachments folder path.")


def open_attachments_folder(state):
    path = get_attachments_folder_path(state)
    if path is None:
        return
    open_path(path)


def get_attachments_folder_path(state):
    node_id = state.get("selected_node_id")
    if node_id is None:
        return None

    node = state["graph_data"]["nodes"].get(node_id)
    if node is None or not node.get("materialized"):
        return None

    return str(projectio.get_node_dir(state["project_dir"], node_id) / "attachments")


def get_notes_path(state):
    node_id = state.get("selected_node_id")
    if node_id is None:
        return None

    node = state["graph_data"]["nodes"].get(node_id)
    if node is None or not node.get("materialized"):
        return None

    return str(projectio.get_node_dir(state["project_dir"], node_id) / "notes.txt")


def copy_text_to_clipboard(state, text):
    """Copy text to the system clipboard."""

    window = state["window"]
    window.clipboard_clear()
    window.clipboard_append(text)
    window.update()


def open_path(path_text):
    """Open a path using the operating system."""

    if not path_text:
        return
    path = str(path_text)
    try:
        os.startfile(path)
    except AttributeError:
        return


def set_text_widget(widget, text):
    """Replace a Text widget's contents."""

    previous_state = str(widget.cget("state"))
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", text)
    widget.configure(state=previous_state)


def generate_node_id(state):
    """Return the next unused node id."""

    index = 1
    while True:
        node_id = f"node-{index:04d}"
        if node_id not in state["graph_data"]["nodes"]:
            return node_id
        index += 1


def set_status(state, text):
    state["status_text"].set(text)


def format_created_text(created_at):
    """Format a unix timestamp as local YYYY-MM-DD."""

    if not created_at:
        return "created: unknown"

    dt = datetime.fromtimestamp(created_at)
    return f"created: {dt.strftime('%Y-%m-%d')}"
