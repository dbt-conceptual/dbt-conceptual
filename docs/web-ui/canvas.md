# Canvas Editor

The visual interface for viewing and editing your conceptual model.

---

## Overview

The canvas is the main view in dbt-conceptual. It displays concepts as nodes and relationships as edges in a graph layout.

<figure>
  <img src="../assets/ui-screenshot.svg" alt="Canvas editor interface" />
</figure>

Launch it with:

```bash
dbc serve
```

Then open `http://localhost:8050` in your browser.

---

## Interface Layout

| Area | Purpose |
|------|---------|
| **Toolbar** | File path, view tabs (Editor, Coverage, Bus Matrix) |
| **Canvas toolbar** | Tools (Select, Concept, Relationship, Domain), zoom, export |
| **Canvas** | The graph visualization |
| **Messages panel** | Validation messages, sync status |
| **Properties panel** | Details of selected concept or relationship |

---

## Working with Concepts

### Selecting

Click a concept to select it. The properties panel shows its details:
- Domain
- Owner
- Status
- Description
- Implementing models

### Creating

1. Click the **Concept** tool in the toolbar
2. Click on the canvas to place a new concept
3. Fill in the properties panel

Or create directly in `conceptual.yml` — the canvas syncs automatically.

### Moving

Drag concepts to arrange them. Positions are saved automatically.

### Editing

Select a concept, then edit fields in the properties panel. Changes save automatically.

---

## Working with Relationships

### Viewing

Relationships appear as edges between concepts. Hover to see:
- Relationship name
- Cardinality
- Description

### Creating

1. Click the **Relationship** tool in the toolbar
2. Click the source concept
3. Click the target concept
4. Fill in the properties

### Editing

Click an edge to select it, then edit in the properties panel.

---

## Visual Indicators

### Concept Status

| Visual | Meaning |
|--------|---------|
| Solid border | Complete |
| Dashed gray border | Draft |
| Dashed orange border | Stub |
| Gray fill, red badge | Ghost (undefined) |

### Domain Colors

Each domain has a distinct color. Concepts inherit their domain's color, making it easy to see groupings at a glance.

### Model Counts

Concept cards show implementing model counts per layer:

```
🥉 3   🥈 2   🥇 1
bronze silver gold
```

### Error/Warning Badges

Red or orange badges indicate validation issues that need attention.

---

## Toolbar Actions

### Sync

Click **Sync** to refresh the model from your dbt project. This:
- Detects new models with `meta.concept` tags
- Updates coverage counts
- Validates relationships

### Export

Click **Export** to save the canvas as:
- **SVG** — Vector image for documentation
- **PNG** — Raster image for presentations

### Zoom

Use the zoom dropdown or:
- Mouse wheel to zoom
- Click and drag to pan
- Fit button to show all concepts

---

## Filtering

### By Domain

Click a domain in the legend to filter the canvas to just that domain's concepts.

### By Status

Filter to show only:
- Complete concepts
- Incomplete (draft/stub) concepts
- Concepts with validation errors

### Search

Type in the search box to filter concepts by name.

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Escape` | Deselect / cancel |
| `Delete` | Delete selected |
| `Ctrl+Z` | Undo |
| `Ctrl+S` | Save (also auto-saves) |
| `+` / `-` | Zoom in/out |
| `0` | Fit to screen |

---

## Demo Mode

Want to explore without setting up a project?

```bash
dbc serve --demo
```

This loads sample data so you can see how the interface works.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Canvas is empty | Run `dbc sync` to load from your project |
| Changes not saving | Check file permissions on `conceptual.yml` |
| Concepts overlapping | Drag to rearrange, positions are saved |
| Relationships not showing | Check that both concepts exist |
