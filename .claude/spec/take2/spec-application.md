# dbt-conceptual: Application Specification

> **Version:** 1.0  
> **Date:** January 2026  
> **Companion Documents:** `spec-positioning.md`, `dbt-conceptual-final-mockups.html`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Brand Identity](#2-brand-identity)
3. [Data Model](#3-data-model)
4. [Application Architecture](#4-application-architecture)
5. [User Interface Layout](#5-user-interface-layout)
6. [Canvas](#6-canvas)
7. [Concept Component](#7-concept-component)
8. [Relationship Component](#8-relationship-component)
9. [Property Panel](#9-property-panel)
10. [Modals](#10-modals)
11. [Interactions & Flows](#11-interactions--flows)
12. [Technical Implementation](#12-technical-implementation)
13. [CLI Integration](#13-cli-integration)
14. [Configuration Schema](#14-configuration-schema)
15. [Design Tokens](#15-design-tokens)

---

## 1. Overview

### Purpose

dbt-conceptual provides a visual interface for managing conceptual data models that live alongside dbt projects. The UI is a helper for the underlying YAML — edits in the UI write to `conceptual.yml`, edits to YAML reflect in the UI.

### Core Principle

**YAML is truth, the canvas is a view.**

### Key Features

- Whiteboard-style canvas for concepts and relationships
- Property panel for detailed editing
- Model association workflow (Silver/Gold layers)
- Bi-directional sync with dbt project
- Settings for domains and layer paths
- Export to multiple formats

---

## 2. Brand Identity

### Logo: Entity Seed

A rounded rectangle representing a conceptual entity — the atomic building block from which data models grow.

**Construction:**
- Outer shape: Rounded rectangle, gradient fill
- Header bar: Highlighted section with indicator dot
- Attribute lines: Subtle lines suggesting structure

**Specifications:**

| Element | Value |
|---------|-------|
| Background gradient | `#1e3a5f` → `#112235` (150°) |
| Border | 2px solid `#4a7fb3` |
| Border radius | 12px (large), 8px (medium), 5px (small) |
| Header gradient | `#5ba3f5` → `#3d8ae0` (90°) |
| Header border radius | 6px (large), 4px (medium), 2px (small) |
| Indicator dot | White, 85% opacity, centered vertically in header |

**Sizes:**

| Size | Dimensions | Use |
|------|------------|-----|
| Large | 56×63px | Hero, documentation |
| Medium | 40×45px | App header, banners |
| Small | 26×30px | Favicon, compact UI |

### Wordmark

- **Font:** JetBrains Mono, 500 weight
- **Text:** `dbt-conceptual`
- **Color:** `#1a1a2e` (light bg), `#ffffff` (dark bg)

### Tagline

**"Conceptual data modeling for dbt projects"**

- **Font:** Inter or Source Sans 3, 400 weight
- **Color:** `#888888`

---

## 3. Data Model

### conceptual.yml Schema

```yaml
version: 1

# Domain definitions
domains:
  party:
    name: "Party"
    color: "#E3F2FD"      # Optional, for UI display
  transaction:
    name: "Transaction"
    color: "#FFF3E0"
  catalog:
    name: "Catalog"
    color: "#F1F8E9"

# Concept definitions
concepts:
  customer:
    name: "Customer"
    domain: party           # Single domain
    owner: "customer_team"  # Free text, autocomplete from existing
    definition: "A person or company that purchases products"
    status: complete        # complete | draft | stub (derived, not stored)

  order:
    name: "Order"
    domain: transaction
    owner: "orders_team"
    definition: "A confirmed purchase by a customer"

# Relationship definitions
relationships:
  - name: "customer:places:order"   # Derived or custom_name
    custom_name: null               # Optional override
    verb: "places"
    from: customer
    to: order
    cardinality: "1:N"              # 1:1 | 1:N | N:M (informational)
    domains:                        # Multiple allowed
      - transaction
    owner: "orders_team"
    definition: "A customer places one or more orders"
```

### Model Association (in dbt model.yml)

```yaml
# For dimensions/concepts
models:
  - name: dim_customer
    meta:
      concept: customer

# For facts/bridges (relationship realization)
models:
  - name: fact_order_lines
    meta:
      realizes:
        - customer:places:order
        - order:contains:product
```

### Status Derivation

Status is **derived**, not stored:

| Entity Type | Status | Condition |
|-------------|--------|-----------|
| Concept | `complete` | Has domain AND has ≥1 associated model |
| Concept | `draft` | Missing domain OR zero associated models |
| Concept | `stub` | Created from sync (only name, needs enrichment) |
| Relationship | `complete` | Has ≥1 domain AND (cardinality ≠ N:M OR has ≥1 realizing model) |
| Relationship | `draft` | Missing domain OR (cardinality = N:M AND zero realizing models) |
| Relationship | `stub` | Created from sync (only from/to/verb, needs enrichment) |

### Layer Association

| Layer | Source | Editable |
|-------|--------|----------|
| Gold | `meta.concept` in model.yml within gold_paths | Yes |
| Silver | `meta.concept` in model.yml within silver_paths | Yes |
| Bronze | Inferred from manifest.json lineage (upstream of Silver) | No (read-only) |

---

## 4. Application Architecture

### Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Frontend | React + TypeScript | Component-based UI |
| Canvas | React Flow | Node/edge graph library |
| Build | Vite | Fast dev server, production builds |
| Backend | Flask (Python) | Serves API, static files |
| Storage | YAML files | `conceptual.yml`, `dbt_project.yml` |

### Directory Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Canvas/
│   │   │   ├── ConceptNode.tsx      # Custom React Flow node
│   │   │   ├── RelationshipEdge.tsx # Custom React Flow edge
│   │   │   └── Canvas.tsx           # React Flow wrapper
│   │   ├── PropertyPanel/
│   │   │   ├── PropertyPanel.tsx
│   │   │   ├── PropertiesTab.tsx
│   │   │   ├── ModelsTab.tsx
│   │   │   └── DomainTagsField.tsx
│   │   ├── Modals/
│   │   │   ├── AssociateModelModal.tsx
│   │   │   └── SettingsModal.tsx
│   │   ├── Toolbar.tsx
│   │   ├── TopBar.tsx
│   │   └── Legend.tsx
│   ├── hooks/
│   │   ├── useConceptualModel.ts    # State management
│   │   └── useSync.ts               # Sync operations
│   ├── types.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/state` | GET | Get current conceptual model |
| `/api/state` | POST | Save changes to conceptual.yml |
| `/api/models` | GET | List dbt models with layer/association info |
| `/api/sync` | POST | Trigger sync from dbt project |
| `/api/settings` | GET | Get configuration (domains, paths) |
| `/api/settings` | POST | Update configuration |
| `/api/coverage` | GET | Coverage report HTML |
| `/api/bus-matrix` | GET | Bus matrix HTML |

---

## 5. User Interface Layout

### Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ Top Bar                                                         [⚙] │
│ [Logo] [File Path]                    [Editor] [Coverage] [Bus Matrix] │
├─────────────────────────────────────────────────────────────────────┤
│ Toolbar                                                             │
│ [↖ Select] [□ Concept] [↗ Relationship] | [⊞ Domain]    [100%] [Export] [Sync] │
├─────────────────────────────────────────────────┬───────────────────┤
│                                                 │                   │
│                                                 │  Property Panel   │
│                 Canvas                          │  (320px)          │
│                                                 │                   │
│                                                 │                   │
│                                                 │                   │
├─────────────────────────────────────────────────┴───────────────────┤
│ Legend                                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Top Bar

| Element | Description |
|---------|-------------|
| Logo | Logo mark + "dbt-conceptual" wordmark |
| File path | Badge showing `models/conceptual/conceptual.yml` |
| Main tabs | Editor, Coverage, Bus Matrix |
| Settings | Gear icon → opens Settings modal |

**Specifications:**
- Height: 44px
- Background: `#fafbfc`
- Border: 1px solid `#e5e7eb` (bottom)

### Toolbar

| Tool | Icon | Behavior |
|------|------|----------|
| Select | ↖ | Default. Click to select, drag to move |
| Concept | □ | Click canvas to place new concept |
| Relationship | ↗ | Drag from concept to concept |
| Domain | ⊞ | (Future) Group concepts by domain |

**Right side:**
- Zoom control (display current zoom %)
- Export button
- Sync button

**Specifications:**
- Height: 40px
- Background: `#ffffff`
- Border: 1px solid `#e5e7eb` (bottom)

### Legend

| Item | Visual | Meaning |
|------|--------|---------|
| Complete | Solid border swatch | Has domain + has models |
| Draft | Dashed gray border | Missing domain or zero models |
| Stub | Dashed amber border | Created from sync, needs enrichment |

**Specifications:**
- Height: 36px
- Background: `#fafbfc`
- Border: 1px solid `#e5e7eb` (top)

---

## 6. Canvas

### Background

- **Color:** `#ffffff`
- **Grid:** Dot pattern
  - Dot color: `#dddddd`
  - Dot size: 1px
  - Spacing: 16px
  - Opacity: 40%

### Behavior

| Action | Result |
|--------|--------|
| Click concept | Select, open property panel |
| Click relationship | Select, open property panel |
| Click empty canvas | Deselect, close property panel |
| Right-click concept | Context menu |
| Right-click relationship | Context menu |
| Drag concept | Move concept |
| Scroll/pinch | Zoom |
| Drag canvas | Pan |

### React Flow Configuration

```tsx
<ReactFlow
  nodes={nodes}
  edges={edges}
  nodeTypes={{ concept: ConceptNode }}
  edgeTypes={{ relationship: RelationshipEdge }}
  onNodeClick={handleNodeClick}
  onEdgeClick={handleEdgeClick}
  onPaneClick={handlePaneClick}
  onNodeContextMenu={handleNodeContextMenu}
  onEdgeContextMenu={handleEdgeContextMenu}
  fitView
  snapToGrid
  snapGrid={[16, 16]}
>
  <Background variant="dots" gap={16} size={1} color="#ddd" />
  <Controls />
</ReactFlow>
```

---

## 7. Concept Component

### Visual Design

```
┌─────────────────────────┐
│                         │
│      Concept Name       │  ← 14px, weight 600, #1a1a2e
│        DOMAIN           │  ← 9px uppercase, #888888
│                         │
│ 3                       │  ← Model count badge
└─────────────────────────┘
```

### States

| State | Border | Border Style | Opacity | Count Badge |
|-------|--------|--------------|---------|-------------|
| Complete | `#d0d0d0` | solid | 1.0 | Blue bg (`#e8f4ff`) |
| Complete + Selected | `#4a9eff` | solid | 1.0 | Blue bg |
| Complete + Hover | `#999999` | solid | 1.0 | Blue bg |
| Draft | `#cccccc` | dashed | 0.7 | Gray bg (`#f0f0f0`) |
| Draft + Selected | `#4a9eff` | dashed | 0.85 | Gray bg |
| Stub | `#f5a623` | dashed | 0.7 | Amber bg (`#fef3e0`), "↻" icon |
| Stub + Selected | `#4a9eff` | dashed | 0.85 | Amber bg |

### Specifications

| Property | Value |
|----------|-------|
| Min width | 120px |
| Border width | 2px |
| Border radius | 10px |
| Padding (body) | 14px 16px 10px |
| Name font | Inter, 14px, 600 |
| Name color | `#1a1a2e` |
| Domain font | Inter, 9px, 600, uppercase |
| Domain color | `#888888` |
| Domain letter-spacing | 0.3px |

### Model Count Badge

| Property | Value |
|----------|-------|
| Position | Bottom-left, 6px from edges |
| Font | JetBrains Mono, 10px, 600 |
| Padding | 2px 6px |
| Border radius | 4px |

| State | Background | Color |
|-------|------------|-------|
| Has models | `#e8f4ff` | `#4a9eff` |
| No models | `#f0f0f0` | `#888888` |
| Stub | `#fef3e0` | `#f5a623` |

### Selection State

When selected:
- Border color: `#4a9eff`
- Box shadow: `0 0 0 3px rgba(74, 158, 255, 0.15)`

---

## 8. Relationship Component

### Visual Design

```
           ┌──────────┐
○──────────│  verb    │──────────○
           └──────────┘
1                                N
```

### Line

| Property | Value |
|----------|-------|
| Stroke color | `#bbbbbb` |
| Stroke color (selected) | `#4a9eff` |
| Stroke color (stub) | `#f5a623` |
| Stroke width | 2px |
| Stroke style (stub) | Dashed (`4 2`) |
| Path type | Bezier curve |

### Label (Verb)

| Property | Value |
|----------|-------|
| Background | `#ffffff` |
| Border radius | 3px |
| Padding | 2px 6px |
| Font | Inter, 11px, 500 |
| Color | `#666666` |
| Color (selected) | `#4a9eff` |
| Position | Centered on path |

### Cardinality

| Property | Value |
|----------|-------|
| Font | JetBrains Mono, 9px |
| Color | `#999999` |
| Position | Near endpoints |
| Values | 1, N, M |

---

## 9. Property Panel

### Structure

- **Width:** 320px
- **Background:** `#fafbfc`
- **Border:** 1px solid `#e5e7eb` (left)

### Header

| Element | Specification |
|---------|---------------|
| Title | Entity name, 14px, 600, `#1a1a2e` |
| Close button | "×", 24px hit area |
| Background | `#ffffff` |
| Border | 1px solid `#e5e7eb` (bottom) |
| Padding | 12px 16px |

### Tabs

| Tab | Content |
|-----|---------|
| Properties | Domain, Owner, Name, Status, Description |
| Models | Associated models by layer, add button |

**Tab styling:**
- Active: Color `#4a9eff`, 2px bottom border `#4a9eff`
- Inactive: Color `#666666`
- Font: 12px, 500

### Properties Tab — Concept

| Field | Type | Notes |
|-------|------|-------|
| Domain | Tag field | Single tag for concepts, + to add, × to remove |
| Owner | Text input | Free text, autocomplete from existing owners |
| Name | Text input | Concept name |
| Status | Read-only indicator | Dot + text (Complete/Draft/Stub) |
| Description | Textarea | Free text |

### Properties Tab — Relationship

| Field | Type | Notes |
|-------|------|-------|
| Domain | Tag field | Multiple tags allowed, endpoint suggestions shown until one added |
| Owner | Text input | Free text, autocomplete |
| Name | Text input (readonly) + Edit button | Shows derived `{from}:{verb}:{to}` or `custom_name` |
| Verb | Text input | Free text, autocomplete from existing verbs |
| Cardinality | Select dropdown | 1:1, 1:N, N:M (informational) |
| Status | Read-only indicator | Derived status |
| Description | Textarea | Free text |

### Domain Tags Field

```
┌─────────────────────────────────────────┐
│ [Transaction ×]  [Finance]  (+)         │
│  ↑ assigned       ↑ suggested           │
└─────────────────────────────────────────┘
```

**Assigned tag:**
- Background: `#e8f4ff`
- Color: `#4a9eff`
- Has × to remove

**Suggested tag (endpoint domains, until one assigned):**
- Background: `#f5f5f5`
- Color: `#999999`
- Border: 1px dashed `#cccccc`
- Click to add
- Helper text below: "Click a suggestion or + to add domain"

**Add button:**
- Circle, 22px diameter
- Border: 1px dashed `#4a9eff`
- "+" icon, color `#4a9eff`

### Name Field (Relationship)

Two modes:

**Derived mode (default):**
- Input: readonly, gray background (`#f5f5f5`)
- Value: `{from}:{verb}:{to}` — updates live as verb changes
- Edit button visible

**Custom mode (after Edit clicked):**
- Input: editable, white background
- Value: `custom_name`
- Clear to revert to derived

### Models Tab

```
┌─────────────────────────────────────────┐
│ [GOLD]  (1)                          ▾  │
├─────────────────────────────────────────┤
│ dim_customer                          × │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ [SILVER]  (2)                        ▾  │
├─────────────────────────────────────────┤
│ stg_shopify__customers                × │
│ stg_crm__customers                    × │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ [BRONZE]  (4)  (inferred)            ▸  │
├─────────────────────────────────────────┤
│ raw_shopify.customers                   │
│ raw_crm.contacts                        │
│ ...                                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          + Associate Model...           │
└─────────────────────────────────────────┘
```

### Layer Badges

| Layer | Background | Color |
|-------|------------|-------|
| Gold | `#fef3c7` | `#b45309` |
| Silver | `#f1f5f9` | `#475569` |
| Bronze | `#f5f0ed` | `#8d6e63` |

**Badge styling:**
- Font: 9px, 600, uppercase
- Padding: 2px 6px
- Border radius: 3px

### Section Behavior

| Layer | Expanded by default | Editable |
|-------|---------------------|----------|
| Gold | Yes | Yes (remove models) |
| Silver | Yes | Yes (remove models) |
| Bronze | No (collapsed) | No (read-only, inferred) |

### Empty State

When no models associated:

```
┌─────────────────────────────────────────┐
│              📦                         │
│    No models associated yet             │
│  Associate models to move out of draft  │
└─────────────────────────────────────────┘
```

---

## 10. Modals

### Associate Model Modal

**Trigger:** Click "+ Associate Model..." in Models tab

**Structure:**
```
┌─────────────────────────────────────────┐
│ Associate Model to {Concept}        ×   │
├─────────────────────────────────────────┤
│  [Silver]  [Gold]                       │  ← Layer selector
├─────────────────────────────────────────┤
│  🔍 Search models...                    │  ← Filter input
├─────────────────────────────────────────┤
│  models/gold/                           │  ← Grouped by path
│    ☑ dim_customer           already linked │
│    ☐ dim_customer_segment               │
│    ☐ fact_customer_orders               │
│  models/gold/finance/                   │
│    ☐ dim_customer_credit                │
├─────────────────────────────────────────┤
│  1 model selected       [Cancel] [Associate] │
└─────────────────────────────────────────┘
```

**Layer Selector:**
- Silver and Gold only (Bronze is inferred)
- Active tab: Background `#e8f4ff`, border `#4a9eff`, color `#4a9eff`

**Model List:**
- Grouped by folder path (from layer path config)
- Group title: 10px uppercase, `#999999`
- Checkbox: 16×16px, border-radius 4px
- Checked: Background `#4a9eff`, white checkmark
- Already linked: Disabled state, "already linked" label

**Footer:**
- Count: "X model(s) selected"
- Cancel: Secondary button
- Associate: Primary button

**Behavior:**
1. User selects layer tab
2. Modal shows unassociated models in that layer's folders
3. User searches/filters
4. User checks models to associate
5. Click Associate → adds `meta.concept` to model.yml files
6. Modal closes, panel refreshes

### Settings Modal

**Trigger:** Click gear icon in top bar

**Tabs:**
- Domains
- Layer Paths

#### Domains Tab

```
┌─────────────────────────────────────────┐
│ Configured Domains                      │
├─────────────────────────────────────────┤
│ [■] Party                         ✎  ×  │
│ [■] Transaction                   ✎  ×  │
│ [■] Catalog                       ✎  ×  │
│ [■] Finance                       ✎  ×  │
└─────────────────────────────────────────┘
         + Add Domain
```

**Item:**
- Color swatch (16×16px, border-radius 4px)
- Domain name
- Edit button (✎)
- Delete button (×)

#### Layer Paths Tab

```
┌─────────────────────────────────────────┐
│ Gold Layer Paths                        │
├─────────────────────────────────────────┤
│ models/gold                           × │
│ models/marts                          × │
└─────────────────────────────────────────┘
         + Add Path

┌─────────────────────────────────────────┐
│ Silver Layer Paths                      │
├─────────────────────────────────────────┤
│ models/silver                         × │
│ models/staging                        × │
└─────────────────────────────────────────┘
         + Add Path

┌─────────────────────────────────────────┐
│ Bronze Layer Paths                      │
├─────────────────────────────────────────┤
│ models/bronze                         × │
└─────────────────────────────────────────┘
         + Add Path
         
Note: Bronze associations are inferred from lineage
```

**Path item:**
- Font: JetBrains Mono, 11px
- Delete button (×)

---

## 11. Interactions & Flows

### Creating a Concept

1. User clicks "Concept" tool in toolbar
2. Tool becomes active (highlighted)
3. User clicks on canvas
4. New concept appears at click location
   - Name: "New Concept"
   - Domain: none
   - Status: Draft (dashed border)
5. Property panel opens with Properties tab
6. Name field is focused
7. User types name, selects domain
8. Status updates to Complete when domain assigned AND models associated

### Creating a Relationship

1. User clicks "Relationship" tool in toolbar
2. User clicks on source concept
3. User drags to target concept
4. Relationship line appears
   - Verb: "relates to" (placeholder)
   - Status: Draft
5. Property panel opens with Properties tab
6. Verb field is focused
7. User types verb
8. Derived name updates: `{from}:{verb}:{to}`
9. User optionally adds domain(s)

### Selecting Elements

| Action | Result |
|--------|--------|
| Click concept | Select concept, open panel |
| Click relationship | Select relationship, open panel |
| Click canvas (empty) | Deselect all, close panel |
| Cmd/Ctrl + Click | Multi-select (future) |

### Context Menu

**Right-click on Concept:**

| Item | Action |
|------|--------|
| Edit Properties | Open Properties tab |
| View Models | Open Models tab |
| Associate Model... | Open Associate Model modal |
| — | Divider |
| Delete | Delete with confirmation |

**Right-click on Relationship:**

| Item | Action |
|------|--------|
| Edit Properties | Open Properties tab |
| View Realizations | Open Models tab |
| — | Divider |
| Delete | Delete with confirmation |

### Sync Flow

**Sync button clicked:**

1. CLI scans dbt project for `meta.concept` and `meta.realizes` tags
2. For each referenced concept not in conceptual.yml:
   - Create stub concept (name only)
3. For each referenced relationship not in conceptual.yml:
   - Create stub relationship (from, verb, to only)
4. Update model counts for existing concepts
5. Update Bronze inferred associations from manifest.json
6. UI refreshes to show new stubs (amber dashed border)

### Auto-save

Changes auto-save to `conceptual.yml` after a short debounce (500ms). No explicit save button needed.

Optional: Show subtle "Saved" indicator that fades after 2 seconds.

---

## 12. Technical Implementation

### React Flow Integration

**Custom Node (Concept):**

```tsx
import { Handle, Position, NodeProps } from 'reactflow';

interface ConceptData {
  name: string;
  domain: string | null;
  modelCount: number;
  status: 'complete' | 'draft' | 'stub';
}

export function ConceptNode({ data, selected }: NodeProps<ConceptData>) {
  const statusClass = data.status;
  const hasModels = data.modelCount > 0;
  
  return (
    <div className={`concept ${statusClass} ${selected ? 'selected' : ''}`}>
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
      
      <div className="concept-body">
        <div className="concept-name">{data.name}</div>
        <div className="concept-domain">
          {data.domain || 'no domain'}
        </div>
      </div>
      
      <div className={`concept-count ${hasModels ? 'has-models' : ''} ${data.status}`}>
        {data.status === 'stub' ? '↻' : data.modelCount}
      </div>
    </div>
  );
}
```

**Custom Edge (Relationship):**

```tsx
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';

interface RelationshipData {
  verb: string;
  cardinality: string;
  status: 'complete' | 'draft' | 'stub';
}

export function RelationshipEdge({
  sourceX, sourceY, targetX, targetY,
  sourcePosition, targetPosition,
  data, selected
}: EdgeProps<RelationshipData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX, sourceY, targetX, targetY,
    sourcePosition, targetPosition,
  });
  
  const isStub = data?.status === 'stub';
  
  return (
    <>
      <path
        className={`rel-line ${selected ? 'selected' : ''} ${isStub ? 'stub' : ''}`}
        d={edgePath}
        strokeDasharray={isStub ? '4 2' : undefined}
      />
      <EdgeLabelRenderer>
        <div
          className={`rel-label ${selected ? 'selected' : ''}`}
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
          }}
        >
          {data?.verb || 'relates to'}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
```

### State Management

Use React context or Zustand for global state:

```tsx
interface ConceptualModelState {
  concepts: Record<string, Concept>;
  relationships: Relationship[];
  domains: Domain[];
  settings: Settings;
  
  // Selection
  selectedId: string | null;
  selectedType: 'concept' | 'relationship' | null;
  
  // Actions
  selectConcept: (id: string) => void;
  selectRelationship: (id: string) => void;
  clearSelection: () => void;
  updateConcept: (id: string, updates: Partial<Concept>) => void;
  updateRelationship: (id: string, updates: Partial<Relationship>) => void;
  addConcept: (position: { x: number; y: number }) => void;
  addRelationship: (from: string, to: string) => void;
  deleteConcept: (id: string) => void;
  deleteRelationship: (id: string) => void;
  
  // Sync
  sync: () => Promise<void>;
  save: () => Promise<void>;
}
```

### API Integration

```tsx
// Fetch initial state
const loadState = async () => {
  const response = await fetch('/api/state');
  const data = await response.json();
  return data;
};

// Save changes (debounced)
const saveState = debounce(async (state: ConceptualModelState) => {
  await fetch('/api/state', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state),
  });
}, 500);

// Trigger sync
const sync = async () => {
  const response = await fetch('/api/sync', { method: 'POST' });
  const data = await response.json();
  return data;
};
```

---

## 13. CLI Integration

### Commands

| Command | Description |
|---------|-------------|
| `dbt-conceptual serve` | Start web UI server |
| `dbt-conceptual status` | Show coverage status |
| `dbt-conceptual validate` | Validate conceptual model |
| `dbt-conceptual validate --no-drafts` | Fail if any draft/stub entities |
| `dbt-conceptual sync` | Sync from dbt project |
| `dbt-conceptual sync --create-stubs` | Create stubs for undefined references |
| `dbt-conceptual export --format <fmt>` | Export diagram |
| `dbt-conceptual list concepts` | List all concepts |
| `dbt-conceptual list concepts --status draft` | List concepts by status |
| `dbt-conceptual list relationships` | List all relationships |
| `dbt-conceptual list relationships --status stub` | List relationships by status |

### CI/CD Integration

```yaml
# GitHub Actions example
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install dbt-core dbt-conceptual
      - run: dbt-conceptual validate --no-drafts
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation errors (undefined references, etc.) |
| 2 | Draft/stub entities found (with `--no-drafts`) |

---

## 14. Configuration Schema

### Location

Configuration can be in:
1. `dbt_project.yml` under `vars.dbt_conceptual`
2. Standalone `dbt_conceptual.yml` (future)

### Schema

```yaml
vars:
  dbt_conceptual:
    # Path to conceptual model file
    conceptual_path: models/conceptual/conceptual.yml
    
    # Layer folder mappings
    bronze_paths:
      - models/bronze
    silver_paths:
      - models/silver
      - models/staging
    gold_paths:
      - models/gold
      - models/marts
    
    # Domain definitions (can also be in conceptual.yml)
    domains:
      party:
        name: Party
        color: "#E3F2FD"
      transaction:
        name: Transaction
        color: "#FFF3E0"
```

---

## 15. Design Tokens

### Colors

#### Brand

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#4a9eff` | Interactive elements, selection |
| `--color-primary-light` | `#e8f4ff` | Hover, light backgrounds |
| `--color-primary-dark` | `#3a8eef` | Active states |

#### Logo

| Token | Hex | Usage |
|-------|-----|-------|
| `--logo-bg-start` | `#1e3a5f` | Logo gradient start |
| `--logo-bg-end` | `#112235` | Logo gradient end |
| `--logo-border` | `#4a7fb3` | Logo border |
| `--logo-header-start` | `#5ba3f5` | Logo header gradient start |
| `--logo-header-end` | `#3d8ae0` | Logo header gradient end |

#### Status

| Token | Hex | Usage |
|-------|-----|-------|
| `--status-complete` | `#4caf50` | Complete status dot |
| `--status-draft` | `#9e9e9e` | Draft status dot |
| `--status-draft-border` | `#cccccc` | Draft border |
| `--status-stub` | `#f5a623` | Stub status, amber |
| `--status-stub-light` | `#fef3e0` | Stub background |

#### Layers

| Token | Hex | Usage |
|-------|-----|-------|
| `--layer-gold-bg` | `#fef3c7` | Gold badge background |
| `--layer-gold-text` | `#b45309` | Gold badge text |
| `--layer-silver-bg` | `#f1f5f9` | Silver badge background |
| `--layer-silver-text` | `#475569` | Silver badge text |
| `--layer-bronze-bg` | `#f5f0ed` | Bronze badge background |
| `--layer-bronze-text` | `#8d6e63` | Bronze badge text |

#### UI

| Token | Hex | Usage |
|-------|-----|-------|
| `--text-primary` | `#1a1a2e` | Main text |
| `--text-secondary` | `#666666` | Secondary text |
| `--text-muted` | `#888888` | Muted text, labels |
| `--text-placeholder` | `#aaaaaa` | Placeholder text |
| `--bg-page` | `#f5f6f8` | Page background |
| `--bg-surface` | `#ffffff` | Cards, panels |
| `--bg-surface-alt` | `#fafbfc` | Headers, footers |
| `--border` | `#e5e7eb` | Standard borders |
| `--border-light` | `#f0f0f0` | Light borders |
| `--border-input` | `#dddddd` | Input borders |

### Typography

| Token | Value | Usage |
|-------|-------|-------|
| `--font-sans` | 'Inter', sans-serif | Body text, UI |
| `--font-mono` | 'JetBrains Mono', monospace | Code, technical |
| `--font-size-xs` | 9px | Badges, small labels |
| `--font-size-sm` | 10-11px | Labels, captions |
| `--font-size-base` | 12-13px | Body text |
| `--font-size-md` | 14px | Headings, names |
| `--font-size-lg` | 16px | Modal titles |
| `--font-weight-normal` | 400 | Body text |
| `--font-weight-medium` | 500 | Emphasis |
| `--font-weight-semibold` | 600 | Headings, labels |

### Spacing

| Token | Value |
|-------|-------|
| `--space-1` | 4px |
| `--space-2` | 6px |
| `--space-3` | 8px |
| `--space-4` | 10px |
| `--space-5` | 12px |
| `--space-6` | 14px |
| `--space-7` | 16px |
| `--space-8` | 20px |
| `--space-9` | 24px |

### Border Radius

| Token | Value |
|-------|-------|
| `--radius-sm` | 3px |
| `--radius-md` | 6px |
| `--radius-lg` | 10px |
| `--radius-xl` | 12px |

### Shadows

| Token | Value |
|-------|-------|
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.04)` |
| `--shadow-md` | `0 2px 8px rgba(0,0,0,0.08)` |
| `--shadow-lg` | `0 4px 20px rgba(0,0,0,0.15)` |
| `--shadow-selection` | `0 0 0 3px rgba(74, 158, 255, 0.15)` |

---

## Appendix: File Manifest

| File | Description |
|------|-------------|
| `spec-positioning.md` | Positioning, messaging, target user |
| `spec-application.md` | This document — full technical spec |
| `dbt-conceptual-final-mockups.html` | Visual mockups for all components |

---

*End of specification.*
