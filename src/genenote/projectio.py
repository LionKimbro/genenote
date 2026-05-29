"""Filesystem storage for Genenote projects."""

import json
import shutil
import time
import uuid
from pathlib import Path


APP_VERSION = "0.1.0"


def ensure_project_structure(project_dir):
    """Create the project directory and core files if they do not exist."""

    project_dir.mkdir(parents=True, exist_ok=True)
    get_nodes_root(project_dir).mkdir(parents=True, exist_ok=True)
    get_inbox_dir(project_dir).mkdir(parents=True, exist_ok=True)
    get_outbox_dir(project_dir).mkdir(parents=True, exist_ok=True)

    if not get_project_file(project_dir).exists():
        write_json_file(
            get_project_file(project_dir),
            {
                "project_id": str(uuid.uuid4()),
                "created_at": int(time.time()),
                "version": APP_VERSION,
                "viewport": {
                    "x": 0,
                    "y": 0,
                },
                "config": {
                    "attachments_subdir": "attachments",
                },
            },
        )

    if not get_nodes_file(project_dir).exists():
        write_json_file(get_nodes_file(project_dir), {})

    if not get_links_file(project_dir).exists():
        write_json_file(get_links_file(project_dir), {"edges": []})


def load_project_graph(project_dir):
    """Load the runtime graph from the filesystem project."""

    ensure_project_structure(project_dir)

    nodes_by_id = {}
    stored_positions = read_json_file(get_nodes_file(project_dir), {})
    links_data = read_json_file(get_links_file(project_dir), {"edges": []})

    for node_dir in sorted(get_nodes_root(project_dir).iterdir()):
        if not node_dir.is_dir():
            continue

        node_id = node_dir.name
        node_json = read_json_file(node_dir / "node.json", {})
        coords = stored_positions.get(node_id, [0, 0])
        x, y = normalize_coordinates(coords)

        nodes_by_id[node_id] = {
            "id": node_id,
            "x": x,
            "y": y,
            "title": node_json.get("title", node_id),
            "materialized": True,
            "tags": list(node_json.get("tags", [])),
        }

    edges = []
    for edge in links_data.get("edges", []):
        from_id = edge.get("from")
        to_id = edge.get("to")
        if from_id in nodes_by_id and to_id in nodes_by_id:
            edges.append({"from": from_id, "to": to_id})

    return {
        "nodes": nodes_by_id,
        "edges": edges,
    }


def write_project_graph(project_dir, graph_data):
    """Persist materialized node positions and links."""

    ensure_project_structure(project_dir)
    write_json_file(get_nodes_file(project_dir), build_nodes_coordinates_map(graph_data))
    write_json_file(get_links_file(project_dir), build_links_payload(graph_data))


def load_project_metadata(project_dir):
    """Load project.json metadata."""

    ensure_project_structure(project_dir)
    return read_json_file(get_project_file(project_dir), {})


def load_project_viewport(project_dir):
    """Return the stored viewport offsets."""

    project_data = load_project_metadata(project_dir)
    viewport = project_data.get("viewport", {})
    return {
        "x": int(viewport.get("x", 0)),
        "y": int(viewport.get("y", 0)),
    }


def save_project_viewport(project_dir, offset_x, offset_y):
    """Persist the viewport offsets in project.json."""

    ensure_project_structure(project_dir)
    project_data = read_json_file(get_project_file(project_dir), {})
    project_data["viewport"] = {
        "x": int(offset_x),
        "y": int(offset_y),
    }
    if "config" not in project_data:
        project_data["config"] = {"attachments_subdir": "attachments"}
    write_json_file(get_project_file(project_dir), project_data)


def build_nodes_coordinates_map(graph_data):
    """Return persisted coordinates for materialized nodes only."""

    nodes_payload = {}
    for node_id, node in sorted(graph_data["nodes"].items()):
        if not node.get("materialized"):
            continue
        nodes_payload[node_id] = [
            int(node.get("x", 0)),
            int(node.get("y", 0)),
        ]
    return nodes_payload


def build_links_payload(graph_data):
    """Return persisted edges for materialized nodes only."""

    edges = []
    for edge in graph_data["edges"]:
        from_node = graph_data["nodes"].get(edge["from"])
        to_node = graph_data["nodes"].get(edge["to"])
        if from_node is None or to_node is None:
            continue
        if not from_node.get("materialized") or not to_node.get("materialized"):
            continue
        edges.append({"from": edge["from"], "to": edge["to"]})
    return {"edges": edges}


def materialize_node(project_dir, node):
    """Create on-disk files for a node if needed."""

    ensure_project_structure(project_dir)

    node_id = node["id"]
    node_dir = get_node_dir(project_dir, node_id)
    attachments_dir = node_dir / "attachments"

    node_dir.mkdir(parents=True, exist_ok=True)
    attachments_dir.mkdir(parents=True, exist_ok=True)

    created_at = int(time.time())
    node_title = node.get("title") or node_id
    write_json_file(
        node_dir / "node.json",
        {
            "node_id": node_id,
            "created_at": created_at,
            "title": node_title,
            "tags": list(node.get("tags", [])),
        },
    )
    if not (node_dir / "data.json").exists():
        write_json_file(node_dir / "data.json", {})
    if not (node_dir / "notes.txt").exists():
        (node_dir / "notes.txt").write_text("", encoding="utf-8")

    node["title"] = node_title
    node["materialized"] = True


def save_materialized_node(project_dir, node_id, title, notes_text):
    """Save materialized node metadata and notes."""

    node_dir = get_node_dir(project_dir, node_id)
    node_json = read_json_file(node_dir / "node.json", {})
    node_json["node_id"] = node_id
    node_json["title"] = title
    node_json["tags"] = list(node_json.get("tags", []))
    if "created_at" not in node_json:
        node_json["created_at"] = int(time.time())

    write_json_file(node_dir / "node.json", node_json)
    (node_dir / "notes.txt").write_text(notes_text, encoding="utf-8")


def load_materialized_node_detail(project_dir, node_id):
    """Load node detail data for the right-hand pane."""

    node_dir = get_node_dir(project_dir, node_id)
    node_json = read_json_file(node_dir / "node.json", {})
    notes_path = node_dir / "notes.txt"
    return {
        "node_json": node_json,
        "notes_text": notes_path.read_text(encoding="utf-8") if notes_path.exists() else "",
        "folder_path": str(node_dir),
        "attachments": list_attachments(project_dir, node_id),
    }


def list_attachments(project_dir, node_id):
    """Return attachment paths for a materialized node."""

    attachments_dir = get_node_dir(project_dir, node_id) / "attachments"
    if not attachments_dir.exists():
        return []

    attachments = []
    for path in sorted(attachments_dir.iterdir()):
        if path.is_file():
            attachments.append(
                {
                    "name": path.name,
                    "path": str(path),
                }
            )
    return attachments


def copy_files_into_node_attachments(project_dir, node_id, source_paths):
    """Copy dropped files into a node's attachments directory."""

    attachments_dir = get_node_dir(project_dir, node_id) / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for source_path in source_paths:
        source = Path(source_path)
        if not source.exists() or not source.is_file():
            continue

        target = build_unique_attachment_path(attachments_dir, source.name)
        shutil.copy2(source, target)
        copied.append(str(target))

    return copied


def write_patchboard_message(project_dir, channel, signal):
    """Write a FileTalk/Patchboard message into the project's outbox."""

    outbox_dir = get_outbox_dir(project_dir)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    message = {
        "channel": channel,
        "signal": signal,
        "timestamp": str(time.time()),
    }

    filename = _build_patchboard_message_filename()
    message_path = outbox_dir / filename
    write_json_file(message_path, message)
    return message_path


def get_project_file(project_dir):
    return project_dir / "project.json"


def get_nodes_file(project_dir):
    return project_dir / "nodes.json"


def get_links_file(project_dir):
    return project_dir / "links.json"


def get_nodes_root(project_dir):
    return project_dir / "nodes"


def get_inbox_dir(project_dir):
    return project_dir / "inbox"


def get_outbox_dir(project_dir):
    return project_dir / "outbox"


def get_node_dir(project_dir, node_id):
    return get_nodes_root(project_dir) / node_id


def build_unique_attachment_path(attachments_dir, filename):
    """Return a non-colliding path preserving the original filename."""

    candidate = attachments_dir / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 1

    while True:
        candidate = attachments_dir / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def normalize_coordinates(coords):
    """Normalize coordinate payloads to an integer pair."""

    if not isinstance(coords, list) or len(coords) != 2:
        return 0, 0
    return int(coords[0]), int(coords[1])


def read_json_file(path, fallback):
    """Read JSON from disk, returning fallback if the file is absent."""

    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path, data):
    """Write JSON to disk with a trailing newline."""

    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    path.write_text(text, encoding="utf-8")


def _build_patchboard_message_filename():
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    suffix = uuid.uuid4().hex[:8]
    return f"{stamp}-{suffix}.json"
