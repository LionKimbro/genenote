from pathlib import Path

from genenote import projectio


def test_load_project_graph_defaults_missing_coordinates_to_origin(tmp_path):
    project_dir = tmp_path / ".genenote"
    projectio.ensure_project_structure(project_dir)

    node_dir = projectio.get_node_dir(project_dir, "node-0001")
    node_dir.mkdir(parents=True)
    projectio.write_json_file(
        node_dir / "node.json",
        {
            "node_id": "node-0001",
            "created_at": 1,
            "title": "Alpha",
            "tags": [],
        },
    )
    projectio.write_json_file(node_dir / "data.json", {})
    (node_dir / "notes.txt").write_text("", encoding="utf-8")
    (node_dir / "attachments").mkdir()

    graph = projectio.load_project_graph(project_dir)

    assert graph["nodes"]["node-0001"]["x"] == 0
    assert graph["nodes"]["node-0001"]["y"] == 0
    assert graph["nodes"]["node-0001"]["materialized"] is True


def test_write_project_graph_only_persists_materialized_nodes_and_edges(tmp_path):
    project_dir = tmp_path / ".genenote"
    graph_data = {
        "nodes": {
            "node-0001": {
                "id": "node-0001",
                "x": 120,
                "y": 300,
                "title": "One",
                "materialized": True,
            },
            "node-0002": {
                "id": "node-0002",
                "x": 400,
                "y": 150,
                "title": "Two",
                "materialized": False,
            },
        },
        "edges": [
            {"from": "node-0001", "to": "node-0002"},
            {"from": "node-0001", "to": "node-0001"},
        ],
    }

    projectio.write_project_graph(project_dir, graph_data)

    assert projectio.read_json_file(projectio.get_nodes_file(project_dir), {}) == {
        "node-0001": [120, 300],
    }
    assert projectio.read_json_file(projectio.get_links_file(project_dir), {}) == {
        "edges": [{"from": "node-0001", "to": "node-0001"}],
    }


def test_materialize_and_save_node_creates_expected_files(tmp_path):
    project_dir = tmp_path / ".genenote"
    node = {
        "id": "node-0001",
        "x": 25,
        "y": 40,
        "title": "Draft Node",
        "materialized": False,
    }

    projectio.materialize_node(project_dir, node)
    projectio.save_materialized_node(project_dir, "node-0001", "Saved Title", "hello")

    node_dir = projectio.get_node_dir(project_dir, "node-0001")
    assert (node_dir / "node.json").exists()
    assert (node_dir / "data.json").exists()
    assert (node_dir / "notes.txt").read_text(encoding="utf-8") == "hello"
    assert (node_dir / "attachments").exists()
    detail = projectio.load_materialized_node_detail(project_dir, "node-0001")
    assert detail["node_json"]["title"] == "Saved Title"


def test_project_viewport_round_trips_in_project_json(tmp_path):
    project_dir = tmp_path / ".genenote"

    projectio.ensure_project_structure(project_dir)
    projectio.save_project_viewport(project_dir, 125, -40)

    assert projectio.load_project_viewport(project_dir) == {
        "x": 125,
        "y": -40,
    }
