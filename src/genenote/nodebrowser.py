"""Copyable main interaction module for nodebrowser."""

import math


canvas_widget = None
graph_data = None
widgets = {}
effects = []
callbacks = {
    "generate_node_id": None,
    "on_single_selection_changed": None,
    "on_graph_mutated": None,
    "on_viewport_changed": None,
}

g = {
    "mode": "IDLE",
    "selected_node_id": None,
    "quantizing": False,
    "active_canvas_name": None,
}

raw = {
    "event_name": None,
    "x": 0,
    "y": 0,
    "key": None,
    "shift_down": False,
    "button_1_down": False,
    "canvas_has_focus": False,
    "pointer_node_id": None,
}

raw_prev = {
    "event_name": None,
    "x": 0,
    "y": 0,
    "key": None,
    "shift_down": False,
    "button_1_down": False,
    "canvas_has_focus": False,
    "pointer_node_id": None,
}

derived = {
    "pointer_dx": 0,
    "pointer_dy": 0,
    "press_started": False,
    "press_released": False,
    "drag_started": False,
    "dragging": False,
    "drag_ended": False,
    "hover_node_id": None,
    "press_node_id": None,
    "over_empty": True,
    "click_completed": False,
    "click_empty": False,
    "drag_rect": None,
    "drag_distance": 0,
    "drag_threshold_crossed": False,
}

derived_prev = {
    "drag_distance": 0,
    "drag_threshold_crossed": False,
}

interaction = {
    "mouse_down_x": 0,
    "mouse_down_y": 0,
    "last_mouse_x": 0,
    "last_mouse_y": 0,
    "drag_node_id": None,
    "group_drag_origin": None,
    "marquee_start": None,
    "marquee_end": None,
    "edge_drag_source_id": None,
    "edge_drag_current_pos": None,
    "press_node_id": None,
    "press_consumed": False,
    "ignore_release": False,
}

selection = {
    "group_selected_ids": [],
}

viewport = {
    "offset_x": 0,
    "offset_y": 0,
}

render = {
    "node_radius": 25,
    "selected_inner_radius": 20,
    "node_outline_width": 5,
    "selected_inner_width": 1,
    "marquee_outline_width": 1,
    "hit_slop": 3,
    "background_color": "black",
    "node_outline_color": "white",
    "node_fill_color": "",
    "selected_fill_color": "#1dc14f",
    "selected_inner_color": "#79ff9a",
    "edge_color": "white",
    "marquee_outline_color": "white",
    "marquee_dash": [4, 4],
    "group_halo_color": "blue",
    "group_halo_width": 3,
    "group_halo_radius_offset": 6,
    "group_preview_halo_color": "#6fd3ff",
    "group_preview_halo_width": 2,
    "group_preview_halo_radius_offset": 6,
    "edge_vertical_pull": 60,
    "preview_edge_color": "#7fdfff",
    "preview_create_edge_color": "#6dff8a",
    "preview_unlink_edge_color": "#ff6b6b",
    "preview_edge_width": 2,
    "drag_threshold": 4,
    "quantize_step": 20,
    "materialized_outline_color": "#f2f2f2",
    "unmaterialized_outline_color": "#3a3a3a",
    "materialized_fill_color": "#13361d",
    "unmaterialized_fill_color": "#101010",
    "materialized_edge_color": "#dcdcdc",
    "unmaterialized_edge_color": "#5f5f5f",
    "node_title_color": "#f4f4f4",
    "node_title_dim_color": "#8d8d8d",
    "node_title_offset_y": 42,
}

canvas_items = {
    "node_items_by_id": {},
    "edge_items": [],
    "marquee_item": None,
    "preview_edge_item": None,
}

coordination = {
    "pointer-owner": None,
    "resource-holds": {},
    "leases": {},
}

current_organism = None
tokenizers = []


def _make_organism(name, fn):
    return {
        "NAME": name,
        "ACTIVE": True,
        "STATE": "IDLE",
        "HELD": {},
        "DATA": {},
        "FN": fn,
    }


def _make_tokenizer(name, fn):
    return {
        "NAME": name,
        "ACTIVE": True,
        "FN": fn,
    }


organisms = []


def _derived_defaults():
    return {
        "pointer_dx": 0,
        "pointer_dy": 0,
        "press_started": False,
        "press_released": False,
        "drag_started": False,
        "dragging": False,
        "drag_ended": False,
        "hover_node_id": None,
        "press_node_id": None,
        "over_empty": True,
        "click_completed": False,
        "click_empty": False,
        "drag_rect": None,
        "drag_distance": 0,
        "drag_threshold_crossed": False,
    }


def reset_runtime():
    """Reset mutable runtime state."""

    global canvas_widget, graph_data, current_organism

    canvas_widget = None
    graph_data = None
    current_organism = None
    effects.clear()
    widgets.clear()
    callbacks["generate_node_id"] = None
    callbacks["on_single_selection_changed"] = None
    callbacks["on_graph_mutated"] = None
    callbacks["on_viewport_changed"] = None

    g["mode"] = "IDLE"
    g["selected_node_id"] = None
    g["quantizing"] = False
    g["active_canvas_name"] = None

    viewport["offset_x"] = 0
    viewport["offset_y"] = 0

    for target in (raw, raw_prev):
        target["event_name"] = None
        target["x"] = 0
        target["y"] = 0
        target["key"] = None
        target["shift_down"] = False
        target["button_1_down"] = False
        target["canvas_has_focus"] = False
        target["pointer_node_id"] = None

    derived["drag_distance"] = 0
    derived["pointer_dx"] = 0
    derived["pointer_dy"] = 0
    derived["press_started"] = False
    derived["press_released"] = False
    derived["drag_started"] = False
    derived["dragging"] = False
    derived["drag_ended"] = False
    derived["hover_node_id"] = None
    derived["press_node_id"] = None
    derived["over_empty"] = True
    derived["click_completed"] = False
    derived["click_empty"] = False
    derived["drag_rect"] = None
    derived["drag_threshold_crossed"] = False
    derived_prev["drag_distance"] = 0
    derived_prev["pointer_dx"] = 0
    derived_prev["pointer_dy"] = 0
    derived_prev["press_started"] = False
    derived_prev["press_released"] = False
    derived_prev["drag_started"] = False
    derived_prev["dragging"] = False
    derived_prev["drag_ended"] = False
    derived_prev["hover_node_id"] = None
    derived_prev["press_node_id"] = None
    derived_prev["over_empty"] = True
    derived_prev["click_completed"] = False
    derived_prev["click_empty"] = False
    derived_prev["drag_rect"] = None
    derived_prev["drag_threshold_crossed"] = False

    interaction["mouse_down_x"] = 0
    interaction["mouse_down_y"] = 0
    interaction["last_mouse_x"] = 0
    interaction["last_mouse_y"] = 0
    interaction["drag_node_id"] = None
    interaction["group_drag_origin"] = None
    interaction["marquee_start"] = None
    interaction["marquee_end"] = None
    interaction["edge_drag_source_id"] = None
    interaction["edge_drag_current_pos"] = None
    interaction["press_node_id"] = None
    interaction["press_consumed"] = False
    interaction["ignore_release"] = False

    selection["group_selected_ids"] = []

    canvas_items["node_items_by_id"] = {}
    canvas_items["edge_items"] = []
    canvas_items["marquee_item"] = None

    coordination["pointer-owner"] = None
    coordination["resource-holds"] = {}
    coordination["leases"] = {}

    _init_tokenizers()
    _init_organisms()


def _init_tokenizers():
    tokenizers[:] = [
        _make_tokenizer("pointer-delta-tokenizer", _run_pointer_delta_tokenizer),
        _make_tokenizer("drag-lifecycle-tokenizer", _run_drag_lifecycle_tokenizer),
        _make_tokenizer("hit-test-tokenizer", _run_hit_test_tokenizer),
        _make_tokenizer("empty-space-tokenizer", _run_empty_space_tokenizer),
        _make_tokenizer("click-tokenizer", _run_click_tokenizer),
    ]


def _init_organisms():
    """Create the organism inventory."""

    organisms[:] = [
        _make_organism("pointer-focus-organism", _run_pointer_focus_organism),
        _make_organism("mode-key-organism", _run_mode_key_organism),
        _make_organism("quantize-key-organism", _run_quantize_key_organism),
        _make_organism("layout-key-organism", _run_layout_key_organism),
        _make_organism("node-create-organism", _run_node_create_organism),
        _make_organism("edge-create-organism", _run_edge_create_organism),
        _make_organism("pan-organism", _run_pan_organism),
        _make_organism("group-drag-organism", _run_group_drag_organism),
        _make_organism("node-drag-organism", _run_node_drag_organism),
        _make_organism("marquee-select-organism", _run_marquee_select_organism),
        _make_organism("node-click-select-organism", _run_node_click_select_organism),
        _make_organism("empty-click-clear-selection-organism", _run_empty_click_clear_selection_organism),
        _make_organism("delete-organism", _run_delete_organism),
    ]


def use_canvas(canvas):
    """Attach to a canvas, or detach by passing None."""

    global canvas_widget

    if canvas_widget is not None:
        unbind_canvas_events()

    canvas_widget = canvas

    if canvas_widget is not None:
        bind_canvas_events()
        _configure_canvas_surface()
        redraw_all()


def use_graph_data(data):
    """Attach graph data, or detach by passing None."""

    global graph_data

    graph_data = data
    _ensure_graph_data_shape()
    redraw_all()


def set_callback(name, fn):
    """Register an optional host callback."""

    callbacks[name] = fn


def set_viewport(offset_x, offset_y):
    """Set viewport offsets."""

    viewport["offset_x"] = int(offset_x)
    viewport["offset_y"] = int(offset_y)


def get_viewport():
    """Return current viewport offsets."""

    return {
        "x": viewport["offset_x"],
        "y": viewport["offset_y"],
    }


def bind_canvas_events():
    """Bind the required Tk event surface."""

    if canvas_widget is None:
        return

    canvas_widget.bind("<Button-1>", handle_button_1)
    canvas_widget.bind("<B1-Motion>", handle_button_motion)
    canvas_widget.bind("<ButtonRelease-1>", handle_button_release_1)
    canvas_widget.bind("<KeyPress>", handle_key_press)
    canvas_widget.bind("<KeyRelease>", handle_key_release)


def unbind_canvas_events():
    """Unbind the required Tk event surface."""

    if canvas_widget is None:
        return

    canvas_widget.unbind("<Button-1>")
    canvas_widget.unbind("<B1-Motion>")
    canvas_widget.unbind("<ButtonRelease-1>")
    canvas_widget.unbind("<KeyPress>")
    canvas_widget.unbind("<KeyRelease>")


def _configure_canvas_surface():
    """Apply core canvas configuration."""

    canvas_widget.configure(bg=render["background_color"], takefocus=1)


def handle_button_1(event):
    """Translate Button-1 into RAW and run a cycle."""

    _prepare_pointer_press(event)
    run_cycle()


def handle_button_motion(event):
    """Translate B1-Motion into RAW and run a cycle."""

    _prepare_pointer_motion(event)
    run_cycle()


def handle_button_release_1(event):
    """Translate ButtonRelease-1 into RAW and run a cycle."""

    _prepare_pointer_release(event)
    run_cycle()


def handle_key_press(event):
    """Translate KeyPress into RAW and run a cycle."""

    _prepare_key_event("key-press", event)
    run_cycle()


def handle_key_release(event):
    """Translate KeyRelease into RAW and run a cycle."""

    _prepare_key_event("key-release", event)
    run_cycle()


def _prepare_pointer_press(event):
    _preserve_previous_snapshots()
    interaction["mouse_down_x"] = event.x
    interaction["mouse_down_y"] = event.y
    interaction["last_mouse_x"] = event.x
    interaction["last_mouse_y"] = event.y
    interaction["press_node_id"] = find_node_at(event.x, event.y)
    interaction["press_consumed"] = False
    interaction["ignore_release"] = False
    _update_raw("button-1-press", event)
    _refresh_derived()


def _prepare_pointer_motion(event):
    _preserve_previous_snapshots()
    interaction["last_mouse_x"] = event.x
    interaction["last_mouse_y"] = event.y
    _update_raw("button-1-motion", event)
    _refresh_derived()


def _prepare_pointer_release(event):
    _preserve_previous_snapshots()
    interaction["last_mouse_x"] = event.x
    interaction["last_mouse_y"] = event.y
    _update_raw("button-1-release", event)
    _refresh_derived()


def _prepare_key_event(event_name, event):
    _preserve_previous_snapshots()
    _update_raw(event_name, event)
    _refresh_derived()


def _preserve_previous_snapshots():
    raw_prev.update(raw)
    derived_prev.update(derived)


def _update_raw(event_name, event):
    raw["event_name"] = event_name
    if event_name.startswith("button-1"):
        raw["x"] = getattr(event, "x", raw["x"])
        raw["y"] = getattr(event, "y", raw["y"])
    raw["key"] = getattr(event, "keysym", None)
    state = getattr(event, "state", 0)
    raw["shift_down"] = bool(state & 0x0001)
    if event_name == "button-1-press":
        raw["button_1_down"] = True
    elif event_name == "button-1-release":
        raw["button_1_down"] = False
    raw["canvas_has_focus"] = _canvas_has_focus()
    raw["pointer_node_id"] = find_node_at(raw["x"], raw["y"])


def _refresh_derived():
    return


def run_tokenizers():
    derived.clear()
    derived.update(_derived_defaults())
    for tokenizer in tokenizers:
        if tokenizer["ACTIVE"]:
            tokenizer["FN"]()


def _run_pointer_delta_tokenizer():
    derived["pointer_dx"] = raw["x"] - raw_prev["x"]
    derived["pointer_dy"] = raw["y"] - raw_prev["y"]


def _run_drag_lifecycle_tokenizer():
    dx = raw["x"] - interaction["mouse_down_x"]
    dy = raw["y"] - interaction["mouse_down_y"]
    drag_distance = math.hypot(dx, dy)
    drag_threshold_crossed = drag_distance >= render["drag_threshold"]
    drag_episode_continues = (
        raw["button_1_down"]
        and derived_prev["dragging"]
        and not (raw["event_name"] == "button-1-release")
    )
    dragging = (
        raw["event_name"] == "button-1-motion" and drag_threshold_crossed
    ) or drag_episode_continues

    derived["press_started"] = raw["event_name"] == "button-1-press"
    derived["press_released"] = raw["event_name"] == "button-1-release"
    derived["drag_distance"] = drag_distance
    derived["drag_threshold_crossed"] = drag_threshold_crossed
    derived["drag_started"] = (
        raw["event_name"] == "button-1-motion"
        and drag_threshold_crossed
        and not derived_prev["drag_threshold_crossed"]
    )
    derived["dragging"] = dragging
    derived["drag_ended"] = raw["event_name"] == "button-1-release" and derived_prev["drag_threshold_crossed"]

    if (
        dragging or derived["drag_ended"]
    ):
        derived["drag_rect"] = {
            "x1": interaction["mouse_down_x"],
            "y1": interaction["mouse_down_y"],
            "x2": raw["x"],
            "y2": raw["y"],
        }


def _run_hit_test_tokenizer():
    derived["hover_node_id"] = raw["pointer_node_id"]
    derived["press_node_id"] = interaction["press_node_id"]


def _run_empty_space_tokenizer():
    derived["over_empty"] = raw["pointer_node_id"] is None


def _run_click_tokenizer():
    if raw["event_name"] != "button-1-release":
        return

    if interaction["ignore_release"] or interaction["press_consumed"]:
        return

    if derived["drag_threshold_crossed"]:
        return

    derived["click_completed"] = True

    press_node_id = derived["press_node_id"]
    hover_node_id = derived["hover_node_id"]
    if press_node_id is None and derived["over_empty"]:
        derived["click_empty"] = True


def run_cycle():
    """Run one judge-pattern cycle from current RAW/DERIVED."""

    if canvas_widget is None or graph_data is None:
        return

    run_tokenizers()
    maintain_judge()

    for organism in organisms:
        if not organism["ACTIVE"]:
            continue
        _run_organism(organism)

    maintain_judge()
    apply_effects()
    _finish_cycle()


def _run_organism(organism):
    global current_organism

    current_organism = organism
    organism["FN"](organism)
    current_organism = None


def maintain_judge():
    """Keep coordination state minimal and current."""

    active_names = {
        organism["NAME"]
        for organism in organisms
        if organism["STATE"] != "IDLE"
    }
    stale_names = [name for name in coordination["leases"] if name not in active_names]

    for name in stale_names:
        _release_lease(name)

    pointer_owner = coordination["pointer-owner"]
    if pointer_owner is not None and pointer_owner not in coordination["leases"]:
        coordination["pointer-owner"] = None


def get_permission(request_type, resources=None):
    """Judge permission entrypoint."""

    if current_organism is None:
        return False

    if resources is None:
        resources = []

    owner = current_organism["NAME"]
    requested = list(resources)

    if request_type not in ("START", "HOLD-RESOURCE"):
        return False

    if request_type == "START" and _judge_denies_start(owner, requested):
        return False

    for resource in requested:
        held_by = coordination["resource-holds"].get(resource)
        if held_by is not None and held_by != owner:
            return False

    _ensure_lease(owner)
    for resource in requested:
        coordination["resource-holds"][resource] = owner
        coordination["leases"][owner]["resources"].add(resource)
        if resource == "pointer":
            coordination["pointer-owner"] = owner
    return True


def _judge_denies_start(owner, requested):
    """Apply minimal priority policy for START requests."""

    if owner == "edge-create-organism":
        return False

    if owner == "marquee-select-organism":
        if raw["shift_down"] and interaction["press_node_id"] is None:
            return True

    if owner in ("node-drag-organism", "group-drag-organism"):
        if raw["shift_down"] and interaction["press_node_id"] is not None:
            return True

    if owner == "node-drag-organism":
        if interaction["press_node_id"] in selection["group_selected_ids"]:
            return True

    return False


def emit_effect(effect_type, payload=None):
    """Append an effect to the current effect queue."""

    if payload is None:
        payload = {}
    effects.append({"type": effect_type, "payload": payload})


def notify_done(organism):
    """Tell the judge this organism is no longer engaged."""

    organism["STATE"] = "IDLE"
    organism["HELD"] = {}
    organism["DATA"] = {}
    _release_lease(organism["NAME"])


def _clear_edge_create_interaction():
    interaction["edge_drag_source_id"] = None
    interaction["edge_drag_current_pos"] = None


def _clear_group_drag_interaction():
    interaction["group_drag_origin"] = None


def _clear_node_drag_interaction():
    interaction["drag_node_id"] = None


def _world_to_screen(x, y):
    return x + viewport["offset_x"], y + viewport["offset_y"]


def _screen_to_world(x, y):
    return x - viewport["offset_x"], y - viewport["offset_y"]


def _quantize_value(value):
    step = render["quantize_step"]
    return int(math.floor((value / step) + 0.5) * step)


def _quantize_point(x, y):
    return _quantize_value(x), _quantize_value(y)


def _desired_drag_delta(base_x, base_y):
    total_dx = raw["x"] - interaction["mouse_down_x"]
    total_dy = raw["y"] - interaction["mouse_down_y"]

    if not g["quantizing"]:
        return total_dx, total_dy

    quantized_x = _quantize_value(base_x + total_dx)
    quantized_y = _quantize_value(base_y + total_dy)
    return quantized_x - base_x, quantized_y - base_y


def apply_effects():
    """Apply all queued effects in order."""

    changed_selection = False
    changed_graph = False
    frame_effects = {
        "preview-marquee": None,
        "preview-edge": None,
    }

    while effects:
        effect = effects.pop(0)
        effect_type = effect["type"]
        payload = effect["payload"]

        if effect_type == "focus-canvas":
            canvas_widget.focus_set()
        elif effect_type == "consume-pointer-gesture":
            interaction["press_consumed"] = True
            interaction["ignore_release"] = True
        elif effect_type == "set-mode":
            g["mode"] = payload["mode"]
        elif effect_type == "toggle-quantizing":
            g["quantizing"] = not g["quantizing"]
        elif effect_type == "pan-viewport":
            viewport["offset_x"] += payload["dx"]
            viewport["offset_y"] += payload["dy"]
            if callbacks["on_viewport_changed"] is not None:
                callbacks["on_viewport_changed"](
                    viewport["offset_x"],
                    viewport["offset_y"],
                )
        elif effect_type == "move-group":
            move_group_by(payload["node_ids"], payload["dx"], payload["dy"])
            changed_graph = True
        elif effect_type == "move-node":
            move_node_by(payload["node_id"], payload["dx"], payload["dy"])
            changed_graph = True
        elif effect_type == "align-nodes-horizontal":
            align_nodes_horizontal(payload["node_ids"], payload.get("anchor_node_id"))
            changed_graph = True
        elif effect_type == "distribute-nodes-horizontal":
            distribute_nodes_horizontal(payload["node_ids"])
            changed_graph = True
        elif effect_type == "align-nodes-vertical":
            align_nodes_vertical(payload["node_ids"], payload.get("anchor_node_id"))
            changed_graph = True
        elif effect_type == "distribute-nodes-vertical":
            distribute_nodes_vertical(payload["node_ids"])
            changed_graph = True
        elif effect_type == "create-edge":
            make_edge(payload["from"], payload["to"])
            changed_graph = True
        elif effect_type == "delete-edge":
            delete_edge(payload["from"], payload["to"])
            changed_graph = True
        elif effect_type == "preview-marquee":
            frame_effects["preview-marquee"] = dict(payload)
        elif effect_type == "preview-edge":
            frame_effects["preview-edge"] = dict(payload)
        elif effect_type == "create-node":
            node_id = payload.get("node_id") or _generate_node_id()
            graph_data["nodes"][node_id] = {
                "id": node_id,
                "x": payload["x"],
                "y": payload["y"],
                "title": payload.get("title", node_id),
                "materialized": payload.get("materialized", False),
            }
            changed_graph = True
        elif effect_type == "set-single-selection":
            g["selected_node_id"] = payload["node_id"]
            changed_selection = True
        elif effect_type == "clear-single-selection":
            g["selected_node_id"] = None
            changed_selection = True
        elif effect_type == "clear-group-selection":
            selection["group_selected_ids"] = []
            changed_selection = True
        elif effect_type == "set-group-selection":
            selection["group_selected_ids"] = list(payload["node_ids"])
            changed_selection = True
        elif effect_type == "delete-nodes":
            delete_node_ids(payload["node_ids"])
            changed_graph = True
            changed_selection = True

    if changed_selection and callbacks["on_single_selection_changed"] is not None:
        callbacks["on_single_selection_changed"](g["selected_node_id"])

    if changed_graph and callbacks["on_graph_mutated"] is not None:
        callbacks["on_graph_mutated"]()

    redraw_all(frame_effects)


def redraw_all(frame_effects=None):
    """Rebuild the canvas projection from graph state."""

    if canvas_widget is None:
        return

    if frame_effects is None:
        frame_effects = {}

    canvas_widget.delete("all")
    canvas_items["node_items_by_id"] = {}
    canvas_items["edge_items"] = []
    canvas_items["marquee_item"] = None
    canvas_items["preview_edge_item"] = None
    canvas_items["preview_edge_item"] = None

    if graph_data is None:
        return

    for edge in graph_data["edges"]:
        edge_item = _draw_edge(edge)
        if edge_item is not None:
            canvas_items["edge_items"].append(edge_item)

    for node_id, node in graph_data["nodes"].items():
        canvas_items["node_items_by_id"][node_id] = _draw_node(node, frame_effects)

    _draw_transient_overlays(frame_effects)


def _draw_edge(edge):
    from_node = graph_data["nodes"].get(edge["from"])
    to_node = graph_data["nodes"].get(edge["to"])
    if from_node is None or to_node is None:
        return None

    radius = render["node_radius"]
    pull = render["edge_vertical_pull"]
    from_x, from_y = _world_to_screen(from_node["x"], from_node["y"])
    to_x, to_y = _world_to_screen(to_node["x"], to_node["y"])
    p0 = (from_x, from_y + radius)
    p1 = (from_x, from_y + radius + pull)
    p2 = (to_x, to_y - radius - pull)
    p3 = (to_x, to_y - radius)

    edge_color = render["materialized_edge_color"]
    if not from_node.get("materialized") or not to_node.get("materialized"):
        edge_color = render["unmaterialized_edge_color"]

    return canvas_widget.create_line(
        p0[0], p0[1],
        p1[0], p1[1],
        p2[0], p2[1],
        p3[0], p3[1],
        fill=edge_color,
        smooth=True,
        width=2,
    )


def _draw_node(node, frame_effects):
    x, y = _world_to_screen(node["x"], node["y"])
    radius = render["node_radius"]
    preview_ids = _get_preview_group_selection_ids(frame_effects)

    item_ids = {
        "outer": canvas_widget.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline=_get_node_outline_color(node),
            width=render["node_outline_width"],
            fill=_get_node_fill_color(node),
        ),
    }

    if node["id"] in preview_ids and node["id"] not in selection["group_selected_ids"]:
        halo_radius = radius + render["group_preview_halo_radius_offset"]
        item_ids["preview_halo"] = canvas_widget.create_oval(
            x - halo_radius,
            y - halo_radius,
            x + halo_radius,
            y + halo_radius,
            outline=render["group_preview_halo_color"],
            width=render["group_preview_halo_width"],
        )

    if node["id"] in selection["group_selected_ids"]:
        halo_radius = radius + render["group_halo_radius_offset"]
        item_ids["halo"] = canvas_widget.create_oval(
            x - halo_radius,
            y - halo_radius,
            x + halo_radius,
            y + halo_radius,
            outline=render["group_halo_color"],
            width=render["group_halo_width"],
        )

    if node["id"] == g["selected_node_id"]:
        inner_radius = render["selected_inner_radius"]
        item_ids["inner"] = canvas_widget.create_oval(
            x - inner_radius,
            y - inner_radius,
            x + inner_radius,
            y + inner_radius,
            outline=render["selected_inner_color"],
            width=render["selected_inner_width"],
            fill=render["selected_fill_color"],
        )

    item_ids["label"] = canvas_widget.create_text(
        x,
        y + render["node_title_offset_y"],
        text=node.get("title") or node["id"],
        fill=_get_node_title_color(node),
    )

    return item_ids


def find_node_at(x, y):
    """Return the topmost node hit by the point, or None."""

    if graph_data is None:
        return None

    radius = render["node_radius"] + render["hit_slop"]
    nodes = list(graph_data["nodes"].values())
    nodes.reverse()

    for node in nodes:
        screen_x, screen_y = _world_to_screen(node["x"], node["y"])
        dx = x - screen_x
        dy = y - screen_y
        if math.hypot(dx, dy) <= radius:
            return node["id"]

    return None


def set_group_selection(node_ids):
    """Replace group selection."""

    emit_effect("set-group-selection", {"node_ids": list(node_ids)})
    apply_effects()


def create_node_at(x, y, node_id=None):
    """Create a node and redraw."""

    world_x, world_y = _screen_to_world(x, y)
    emit_effect("create-node", {"x": world_x, "y": world_y, "node_id": node_id})
    apply_effects()


def select_single_node(node_id):
    """Set single selection."""

    emit_effect("set-single-selection", {"node_id": node_id})
    apply_effects()


def clear_single_selection():
    """Clear single selection."""

    emit_effect("clear-single-selection")
    apply_effects()


def clear_group_selection():
    """Clear group selection."""

    emit_effect("clear-group-selection")
    apply_effects()


def delete_selected():
    """Delete group selection or single selection."""

    node_ids = []
    if selection["group_selected_ids"]:
        node_ids = list(selection["group_selected_ids"])
    elif g["selected_node_id"] is not None:
        node_ids = [g["selected_node_id"]]

    if node_ids:
        emit_effect("delete-nodes", {"node_ids": node_ids})
        apply_effects()


def delete_node_ids(node_ids):
    """Delete nodes and any edges touching them."""

    node_id_set = set(node_ids)
    for node_id in node_id_set:
        graph_data["nodes"].pop(node_id, None)

    graph_data["edges"] = [
        edge
        for edge in graph_data["edges"]
        if edge["from"] not in node_id_set and edge["to"] not in node_id_set
    ]

    selection["group_selected_ids"] = [
        node_id
        for node_id in selection["group_selected_ids"]
        if node_id not in node_id_set
    ]

    if g["selected_node_id"] in node_id_set:
        g["selected_node_id"] = None


def move_node_by(node_id, dx, dy):
    """Move a node by delta."""

    node = graph_data["nodes"].get(node_id)
    if node is None:
        return

    node["x"] += dx
    node["y"] += dy


def move_group_by(node_ids, dx, dy):
    """Move a group of nodes by delta."""

    for node_id in node_ids:
        move_node_by(node_id, dx, dy)


def _get_nodes_by_id(node_ids):
    return [
        graph_data["nodes"][node_id]
        for node_id in node_ids
        if node_id in graph_data["nodes"]
    ]


def align_nodes_horizontal(node_ids, anchor_node_id=None):
    """Set selected node y coordinates to the anchor y or their average."""

    nodes = _get_nodes_by_id(node_ids)
    if not nodes:
        return

    if anchor_node_id is not None and anchor_node_id in graph_data["nodes"]:
        average_y = graph_data["nodes"][anchor_node_id]["y"]
    else:
        average_y = sum(node["y"] for node in nodes) / len(nodes)
    for node in nodes:
        node["y"] = average_y


def align_nodes_vertical(node_ids, anchor_node_id=None):
    """Set selected node x coordinates to the anchor x or their average."""

    nodes = _get_nodes_by_id(node_ids)
    if not nodes:
        return

    if anchor_node_id is not None and anchor_node_id in graph_data["nodes"]:
        average_x = graph_data["nodes"][anchor_node_id]["x"]
    else:
        average_x = sum(node["x"] for node in nodes) / len(nodes)
    for node in nodes:
        node["x"] = average_x


def distribute_nodes_horizontal(node_ids):
    """Evenly distribute selected x coordinates from leftmost to rightmost."""

    ordered = sorted(
        _get_nodes_by_id(node_ids),
        key=lambda node: (node["x"], node["id"]),
    )
    if len(ordered) < 3:
        return

    left_x = ordered[0]["x"]
    right_x = ordered[-1]["x"]
    step = (right_x - left_x) / (len(ordered) - 1)

    for index, node in enumerate(ordered[1:-1], start=1):
        node["x"] = left_x + step * index


def distribute_nodes_vertical(node_ids):
    """Evenly distribute selected y coordinates from topmost to bottommost."""

    ordered = sorted(
        _get_nodes_by_id(node_ids),
        key=lambda node: (node["y"], node["id"]),
    )
    if len(ordered) < 3:
        return

    top_y = ordered[0]["y"]
    bottom_y = ordered[-1]["y"]
    step = (bottom_y - top_y) / (len(ordered) - 1)

    for index, node in enumerate(ordered[1:-1], start=1):
        node["y"] = top_y + step * index


def make_edge(from_id, to_id):
    """Append an edge to graph data."""

    graph_data["edges"].append({"from": from_id, "to": to_id})


def delete_edge(from_id, to_id):
    """Remove one matching edge from graph data if present."""

    for index, edge in enumerate(graph_data["edges"]):
        if edge["from"] == from_id and edge["to"] == to_id:
            graph_data["edges"].pop(index)
            return


def has_edge(from_id, to_id):
    """Return True if the directed edge already exists."""

    for edge in graph_data["edges"]:
        if edge["from"] == from_id and edge["to"] == to_id:
            return True
    return False


def _draw_transient_overlays(frame_effects):
    marquee = frame_effects.get("preview-marquee")
    if marquee is not None:
        canvas_items["marquee_item"] = canvas_widget.create_rectangle(
            marquee["x1"],
            marquee["y1"],
            marquee["x2"],
            marquee["y2"],
            outline=render["marquee_outline_color"],
            width=render["marquee_outline_width"],
            dash=tuple(render["marquee_dash"]),
        )
    else:
        canvas_items["marquee_item"] = None

    preview_edge = frame_effects.get("preview-edge")
    if preview_edge is None:
        canvas_items["preview_edge_item"] = None
        return

    source = graph_data["nodes"].get(preview_edge["from"])
    if source is None:
        canvas_items["preview_edge_item"] = None
        return

    radius = render["node_radius"]
    pull = render["edge_vertical_pull"]
    source_x, source_y = _world_to_screen(source["x"], source["y"])
    p0 = (source_x, source_y + radius)
    p1 = (source_x, source_y + radius + pull)
    p2 = (preview_edge["to_x"], preview_edge["to_y"] - pull)
    p3 = (preview_edge["to_x"], preview_edge["to_y"])

    canvas_items["preview_edge_item"] = canvas_widget.create_line(
        p0[0], p0[1],
        p1[0], p1[1],
        p2[0], p2[1],
        p3[0], p3[1],
        fill=preview_edge["color"],
        smooth=True,
        width=render["preview_edge_width"],
        dash=(4, 4),
    )


def _get_preview_group_selection_ids(frame_effects):
    drag_rect = frame_effects.get("preview-marquee")
    if drag_rect is None or graph_data is None:
        return set()

    return set(_find_nodes_in_screen_rect(drag_rect["x1"], drag_rect["y1"], drag_rect["x2"], drag_rect["y2"]))


def _get_node_outline_color(node):
    if node.get("materialized"):
        return render["materialized_outline_color"]
    return render["unmaterialized_outline_color"]


def _get_node_fill_color(node):
    if node.get("materialized"):
        return render["materialized_fill_color"]
    return render["unmaterialized_fill_color"]


def _get_node_title_color(node):
    if node.get("materialized"):
        return render["node_title_color"]
    return render["node_title_dim_color"]


def _run_pointer_focus_organism(organism):
    if raw["event_name"] != "button-1-press":
        return

    if raw["canvas_has_focus"]:
        return

    if not get_permission("START", ["pointer"]):
        return

    emit_effect("focus-canvas")


def _run_mode_key_organism(organism):
    if raw["event_name"] != "key-press":
        return

    if not raw["canvas_has_focus"]:
        return

    mode = None
    if raw["key"] in ("n", "N"):
        mode = "CREATE_NODE"
    elif raw["key"] == "Escape":
        mode = "IDLE"

    if mode is None:
        return

    if not get_permission("START", ["interaction-mode"]):
        return

    emit_effect("set-mode", {"mode": mode})


def _run_quantize_key_organism(organism):
    if raw["event_name"] != "key-press":
        return

    if not raw["canvas_has_focus"]:
        return

    if raw["key"] != "q":
        return

    if not get_permission("START", ["quantize-mode"]):
        return

    emit_effect("toggle-quantizing")


def _run_layout_key_organism(organism):
    if raw["event_name"] != "key-press":
        return

    if not raw["canvas_has_focus"]:
        return

    effect_type = None
    if raw["key"] == "h":
        effect_type = "align-nodes-horizontal"
    elif raw["key"] == "H":
        effect_type = "distribute-nodes-horizontal"
    elif raw["key"] == "v":
        effect_type = "align-nodes-vertical"
    elif raw["key"] == "V":
        effect_type = "distribute-nodes-vertical"

    if effect_type is None:
        return

    node_ids = list(selection["group_selected_ids"])
    if not node_ids:
        return

    if not get_permission("START", ["graph-layout"]):
        return

    emit_effect(
        effect_type,
        {
            "node_ids": node_ids,
            "anchor_node_id": g["selected_node_id"],
        },
    )


def _run_pan_organism(organism):
    if (
        raw["shift_down"]
        and derived["press_started"]
        and derived["press_node_id"] is None
    ):
        if not get_permission("START", ["pointer", "viewport"]):
            return
        organism["STATE"] = "ACTIVE"
        return

    if organism["STATE"] != "ACTIVE":
        return

    if derived["press_released"]:
        notify_done(organism)
        return

    dx = derived["pointer_dx"]
    dy = derived["pointer_dy"]
    if dx or dy:
        emit_effect("pan-viewport", {"dx": dx, "dy": dy})


def _run_node_create_organism(organism):
    if raw["event_name"] != "button-1-release":
        return

    if g["mode"] != "CREATE_NODE":
        return

    if interaction["ignore_release"] or interaction["press_consumed"]:
        return

    if interaction["press_node_id"] is not None:
        return

    if not get_permission("START", ["selection:single"]):
        return

    node_x, node_y = _screen_to_world(raw["x"], raw["y"])
    if g["quantizing"]:
        node_x, node_y = _quantize_point(node_x, node_y)

    emit_effect("create-node", {"x": node_x, "y": node_y})
    next_id = _peek_next_node_id()
    emit_effect("set-single-selection", {"node_id": next_id})
    emit_effect("set-mode", {"mode": "IDLE"})


def _run_edge_create_organism(organism):
    if g["mode"] != "IDLE":
        notify_done(organism)
        _clear_edge_create_interaction()
        return

    if raw["event_name"] == "button-1-release":
        if organism["STATE"] == "ACTIVE":
            target_id = raw["pointer_node_id"]
            source_id = interaction["edge_drag_source_id"]
            if target_id is not None and source_id is not None and target_id != source_id:
                effect_type = "delete-edge" if has_edge(source_id, target_id) else "create-edge"
                emit_effect(effect_type, {"from": source_id, "to": target_id})
        notify_done(organism)
        _clear_edge_create_interaction()
        return

    is_pointer_start_event = raw["event_name"] == "button-1-press"
    is_pointer_drag_event = raw["event_name"] == "button-1-motion"

    if organism["STATE"] != "ACTIVE" and not (is_pointer_start_event or is_pointer_drag_event):
        return

    if interaction["ignore_release"] or interaction["press_consumed"]:
        notify_done(organism)
        _clear_edge_create_interaction()
        return

    if not raw["shift_down"]:
        notify_done(organism)
        _clear_edge_create_interaction()
        return

    source_id = interaction["press_node_id"]
    if source_id is None:
        notify_done(organism)
        _clear_edge_create_interaction()
        return

    if is_pointer_drag_event and not derived["drag_threshold_crossed"]:
        notify_done(organism)
        _clear_edge_create_interaction()
        return

    if organism["STATE"] != "ACTIVE":
        if not get_permission("START", ["pointer", "edge-create"]):
            return
        interaction["edge_drag_source_id"] = source_id
        organism["STATE"] = "ACTIVE"

    interaction["edge_drag_current_pos"] = (raw["x"], raw["y"])
    target_id = raw["pointer_node_id"]
    will_create = (
        target_id is not None
        and target_id != interaction["edge_drag_source_id"]
        and not has_edge(interaction["edge_drag_source_id"], target_id)
    )
    will_unlink = (
        target_id is not None
        and target_id != interaction["edge_drag_source_id"]
        and has_edge(interaction["edge_drag_source_id"], target_id)
    )
    preview_color = render["preview_edge_color"]
    if will_create:
        preview_color = render["preview_create_edge_color"]
    elif will_unlink:
        preview_color = render["preview_unlink_edge_color"]
    emit_effect(
        "preview-edge",
        {
            "from": interaction["edge_drag_source_id"],
            "to_x": raw["x"],
            "to_y": raw["y"],
            "color": preview_color,
        },
    )


def _run_group_drag_organism(organism):
    if g["mode"] != "IDLE":
        notify_done(organism)
        _clear_group_drag_interaction()
        return

    if raw["event_name"] == "button-1-release":
        notify_done(organism)
        _clear_group_drag_interaction()
        return

    if raw["event_name"] != "button-1-motion":
        return

    if interaction["ignore_release"] or interaction["press_consumed"]:
        notify_done(organism)
        _clear_group_drag_interaction()
        return

    node_id = interaction["press_node_id"]
    if node_id is None or node_id not in selection["group_selected_ids"]:
        notify_done(organism)
        _clear_group_drag_interaction()
        return

    if not derived["drag_threshold_crossed"]:
        if organism["STATE"] != "ACTIVE":
            organism["STATE"] = "IDLE"
        return

    if organism["STATE"] != "ACTIVE":
        if not get_permission("START", ["pointer", "group-selection"]):
            return
        interaction["group_drag_origin"] = node_id
        organism["DATA"] = {
            "anchor_origin": (
                graph_data["nodes"][node_id]["x"],
                graph_data["nodes"][node_id]["y"],
            ),
            "applied_dx": 0,
            "applied_dy": 0,
        }
        organism["STATE"] = "ACTIVE"

    anchor_x, anchor_y = organism["DATA"]["anchor_origin"]
    desired_dx, desired_dy = _desired_drag_delta(anchor_x, anchor_y)
    dx = desired_dx - organism["DATA"]["applied_dx"]
    dy = desired_dy - organism["DATA"]["applied_dy"]
    if dx or dy:
        organism["DATA"]["applied_dx"] = desired_dx
        organism["DATA"]["applied_dy"] = desired_dy
        emit_effect(
            "move-group",
            {
                "node_ids": list(selection["group_selected_ids"]),
                "dx": dx,
                "dy": dy,
            },
        )


def _run_node_drag_organism(organism):
    if g["mode"] != "IDLE":
        notify_done(organism)
        _clear_node_drag_interaction()
        return

    if raw["event_name"] == "button-1-release":
        notify_done(organism)
        _clear_node_drag_interaction()
        return

    if not derived["dragging"]:
        if organism["STATE"] != "ACTIVE":
            organism["STATE"] = "IDLE"
        return

    if interaction["ignore_release"] or interaction["press_consumed"]:
        notify_done(organism)
        _clear_node_drag_interaction()
        return

    node_id = derived["press_node_id"]
    if node_id is None:
        notify_done(organism)
        _clear_node_drag_interaction()
        return

    if organism["STATE"] != "ACTIVE":
        if not get_permission("START", ["pointer", f"node:{node_id}"]):
            return
        interaction["drag_node_id"] = node_id
        organism["DATA"] = {
            "origin": (
                graph_data["nodes"][node_id]["x"],
                graph_data["nodes"][node_id]["y"],
            ),
            "applied_dx": 0,
            "applied_dy": 0,
        }
        organism["STATE"] = "ACTIVE"

    drag_node_id = interaction["drag_node_id"]
    if drag_node_id is None:
        return

    origin_x, origin_y = organism["DATA"]["origin"]
    desired_dx, desired_dy = _desired_drag_delta(origin_x, origin_y)
    dx = desired_dx - organism["DATA"]["applied_dx"]
    dy = desired_dy - organism["DATA"]["applied_dy"]
    if dx or dy:
        organism["DATA"]["applied_dx"] = desired_dx
        organism["DATA"]["applied_dy"] = desired_dy
        emit_effect("move-node", {"node_id": drag_node_id, "dx": dx, "dy": dy})


def _run_marquee_select_organism(organism):
    if derived["press_started"] and derived["press_node_id"] is None:
        if not get_permission("START", ["pointer", "group-selection"]):
            notify_done(organism)
            return
        organism["STATE"] = "ARMED"
        return

    if organism["STATE"] == "ARMED":
        if derived["drag_threshold_crossed"]:
            organism["STATE"] = "ACTIVE"
        elif derived["press_released"]:
            notify_done(organism)
            return

    if organism["STATE"] != "ACTIVE":
        return

    drag_rect = derived["drag_rect"]
    if drag_rect is None:
        notify_done(organism)
        return

    if derived["press_released"]:
        node_ids = _find_nodes_in_screen_rect(
            drag_rect["x1"],
            drag_rect["y1"],
            drag_rect["x2"],
            drag_rect["y2"],
        )
        emit_effect("set-group-selection", {"node_ids": node_ids})
        notify_done(organism)
        return

    emit_effect("preview-marquee", drag_rect)


def _run_node_click_select_organism(organism):
    node_id = derived["hover_node_id"]
    if not derived["click_completed"] or node_id is None:
        return

    if not get_permission("START", ["selection:single"]):
        return

    emit_effect("set-single-selection", {"node_id": node_id})


def _run_empty_click_clear_selection_organism(organism):
    if not derived["click_empty"]:
        return

    if not get_permission("START", ["selection:single"]):
        return

    emit_effect("clear-single-selection")
    emit_effect("clear-group-selection")


def _run_delete_organism(organism):
    if raw["event_name"] != "key-press" or raw["key"] != "Delete":
        return

    if not raw["canvas_has_focus"]:
        return

    node_ids = []
    if selection["group_selected_ids"]:
        node_ids = list(selection["group_selected_ids"])
    elif g["selected_node_id"] is not None:
        node_ids = [g["selected_node_id"]]

    if not node_ids:
        return

    if not get_permission("START"):
        return

    emit_effect("delete-nodes", {"node_ids": node_ids})


def _ensure_graph_data_shape():
    if graph_data is None:
        return

    if "nodes" not in graph_data:
        graph_data["nodes"] = {}
    if "edges" not in graph_data:
        graph_data["edges"] = []


def _find_nodes_in_rect(x1, y1, x2, y2):
    left = min(x1, x2)
    right = max(x1, x2)
    top = min(y1, y2)
    bottom = max(y1, y2)
    node_ids = []

    for node_id, node in graph_data["nodes"].items():
        if left <= node["x"] <= right and top <= node["y"] <= bottom:
            node_ids.append(node_id)

    return node_ids


def _find_nodes_in_screen_rect(x1, y1, x2, y2):
    left = min(x1, x2)
    right = max(x1, x2)
    top = min(y1, y2)
    bottom = max(y1, y2)
    node_ids = []

    for node_id, node in graph_data["nodes"].items():
        screen_x, screen_y = _world_to_screen(node["x"], node["y"])
        if left <= screen_x <= right and top <= screen_y <= bottom:
            node_ids.append(node_id)

    return node_ids


def _ensure_lease(owner):
    if owner not in coordination["leases"]:
        coordination["leases"][owner] = {
            "resources": set(),
            "kind": "exclusive",
            "valid": True,
        }


def _release_lease(owner):
    lease = coordination["leases"].pop(owner, None)
    if lease is None:
        return

    for resource in lease["resources"]:
        if coordination["resource-holds"].get(resource) == owner:
            coordination["resource-holds"].pop(resource, None)

    if coordination["pointer-owner"] == owner:
        coordination["pointer-owner"] = None


def _finish_cycle():
    if raw["event_name"] == "button-1-release":
        interaction["press_node_id"] = None
        interaction["press_consumed"] = False
        interaction["ignore_release"] = False


def _canvas_has_focus():
    if canvas_widget is None:
        return False
    return canvas_widget.focus_get() == canvas_widget


def _generate_node_id():
    fn = callbacks["generate_node_id"]
    if fn is not None:
        return fn()
    return _peek_next_node_id()


def _peek_next_node_id():
    index = 1
    if graph_data is None:
        return "node-0001"

    while True:
        node_id = f"node-{index:04d}"
        if node_id not in graph_data["nodes"]:
            return node_id
        index += 1


reset_runtime()
