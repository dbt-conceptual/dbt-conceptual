# Using the Web UI

A quick guide to get started with the dbt-conceptual web interface.

---

## Launching the UI

From your dbt project directory:

```bash
dbc serve
```

Open `http://localhost:8050` in your browser.

### Custom Port

```bash
dbc serve --port 3000
```

### Demo Mode

Explore without a project:

```bash
dbc serve --demo
```

This loads sample data so you can see how things work.

---

## The Three Views

### Editor (Canvas)

The default view. Shows concepts as nodes, relationships as edges.

- Drag to arrange concepts
- Click to select and edit
- Create new concepts and relationships

See [Canvas Editor](../web-ui/canvas.md) for details.

### Coverage

A dashboard showing implementation status:

- Overall coverage percentage
- Coverage by domain
- Coverage by layer
- Orphan models

See [Coverage View](../web-ui/coverage.md) for details.

### Bus Matrix

A dimensional modeling view:

- Fact concepts as rows
- Dimension concepts as columns
- Check marks showing which dimensions apply to which facts

See [Bus Matrix](../web-ui/bus-matrix.md) for details.

---

## Basic Workflow

### View Your Model

1. Launch with `dbc serve`
2. Canvas shows your concepts and relationships
3. Click a concept to see its properties

### Edit a Concept

1. Click a concept to select it
2. Edit fields in the properties panel
3. Changes save automatically to `conceptual.yml`

### Create a Concept

1. Click **Concept** in the toolbar
2. Click on the canvas to place it
3. Fill in the properties

### Create a Relationship

1. Click **Relationship** in the toolbar
2. Click the source concept
3. Click the target concept
4. Fill in the relationship name

### Sync from dbt

1. Click **Sync** in the toolbar (or run `dbc sync`)
2. New models with `meta.concept` tags appear
3. Coverage updates

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Escape` | Deselect |
| `Delete` | Delete selected |
| `Ctrl+Z` | Undo |
| `+` / `-` | Zoom |
| `0` | Fit to screen |

---

## Tips

**Arrange by domain** — Drag concepts from the same domain near each other. The visual grouping helps comprehension.

**Use the coverage view for gaps** — Switch to Coverage to see what's missing, then back to Editor to fix it.

**Export for documentation** — Use **Export > SVG** to get a diagram for your wiki or README.

**Sync regularly** — After adding `meta.concept` tags in your dbt project, click Sync to update the UI.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| UI won't load | Check port isn't in use, try `--port 3001` |
| Canvas is empty | Run `dbc sync` to load from project |
| Changes not appearing | Refresh browser, check file permissions |
| Relationships missing | Verify both concepts exist in `conceptual.yml` |
