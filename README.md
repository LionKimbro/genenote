# Genenote

Genenote is a visual notebook for tracking resources that participate in processes of creative variation.

At heart, it is a graph of nodes you can place, connect, materialize onto disk, annotate, and attach files to. That makes it useful for any kind of work where ideas, references, artifacts, source materials, drafts, inspirations, or branches of development need to stay related without being flattened into a folder tree too early.

![Genenote screenshot placeholder](docs/img/screenshot-1.png)

## What It Is For

Genenote is meant for situations where something evolves through variation:

- creative projects with many reference materials
- design explorations with alternate directions
- research threads that split and reconnect
- writing projects with influences, notes, and source artifacts
- music, visual art, story, game, or software concept development
- any process where "this came from that" matters

Instead of treating files as isolated things in folders, Genenote lets you keep a visible genealogy of related materials.

## Basic Idea

Each node can begin as a lightweight visual object on the canvas.

When a node becomes important, you can materialize it. Materializing a node creates a real folder on disk with a small structure:

- `node.json`
- `data.json`
- `notes.txt`
- `attachments/`

This gives you a workflow that supports both:

- early lightweight exploration
- later durable filesystem-backed organization

## Current Features

- interactive node canvas
- node creation, selection, dragging, marquee selection, and linking
- node materialization into on-disk folders
- notes editing for materialized nodes
- attachment browsing for materialized nodes
- drag-and-drop file attachment onto the selected node
- auto-materialization when files are dropped onto an unrealized node
- persisted viewport and node coordinates

## Why Use It

Genenote can be used for a lot of different things because it is not tied to one creative domain.

You might use it to track:

- source images for an art direction
- references and alternates for a story world
- sketches, notes, and attachments for an invention
- influences and spin-offs in a music project
- branching concepts in software or interface design
- families of experiments in research or making

If your process involves variation, inheritance, recombination, divergence, or resource lineage, Genenote is aimed at that kind of work.

## Running

With the package installed, run:

```bash
genenote
```

Or from the repository:

```bash
python -m genenote
```

## Project Storage

Genenote stores project data in a local `.genenote/` directory. This includes:

- `project.json`
- `nodes.json`
- `links.json`
- `nodes/<node_id>/...`

The canvas is the working view. The filesystem is the durable substrate.
