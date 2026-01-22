# Crow's Foot Cardinality Notation

> Visual specification for rendering relationship cardinality on the dbt-conceptual canvas.

---

## Overview

Replace the current text-based cardinality labels (e.g., "1:N") with standard Crow's Foot notation symbols at relationship line endpoints. This provides immediate visual recognition of cardinality without reading text.

---

## Symbol Components

### Base Elements

| Symbol | Name | Meaning | SVG Concept |
|--------|------|---------|-------------|
| `○` | Ring | Optional (zero permitted) | Small circle on line |
| `│` | Bar | Mandatory (at least one) | Short perpendicular line |
| `⋔` | Crow's foot | Many (multiple permitted) | Three lines diverging |

### Reading Direction

Symbols read **from the entity outward** along the line:

```
┌──────────┐
│  Entity  │──○│────────────────
└──────────┘  ↑↑
              ││
              │└─ Cardinality (one vs many)
              └── Optionality (ring vs bar)
```

---

## Cardinality Compositions

| Name | Notation | Symbol | Description |
|------|----------|--------|-------------|
| Zero or One | `0..1` | `○│` | Optional singular |
| Exactly One | `1..1` | `││` | Mandatory singular |
| Zero or Many | `0..*` | `○⋔` | Optional plural |
| One or Many | `1..*` | `│⋔` | Mandatory plural |

---

## Visual Mockups

### Symbol Reference

<svg width="600" height="200" viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="600" height="200" fill="#f5f6f8"/>

  <!-- Title -->
  <text x="300" y="25" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Crow's Foot Symbol Components</text>

  <!-- Ring (Optional) -->
  <g transform="translate(75, 80)">
    <line x1="0" y1="0" x2="80" y2="0" stroke="#4caf50" stroke-width="2"/>
    <circle cx="40" cy="0" r="6" fill="none" stroke="#4caf50" stroke-width="2"/>
    <text x="40" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" fill="#666666">Ring (Optional)</text>
    <text x="40" y="50" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" fill="#888888">○</text>
  </g>

  <!-- Bar (Mandatory) -->
  <g transform="translate(225, 80)">
    <line x1="0" y1="0" x2="80" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="40" y1="-8" x2="40" y2="8" stroke="#4caf50" stroke-width="2"/>
    <text x="40" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" fill="#666666">Bar (Mandatory)</text>
    <text x="40" y="50" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" fill="#888888">│</text>
  </g>

  <!-- Crow's Foot (Many) -->
  <g transform="translate(375, 80)">
    <line x1="0" y1="0" x2="50" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="-12" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="12" stroke="#4caf50" stroke-width="2"/>
    <text x="40" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" fill="#666666">Crow's Foot (Many)</text>
    <text x="40" y="50" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" fill="#888888">⋔</text>
  </g>

  <!-- Composed: Zero or Many -->
  <g transform="translate(75, 150)">
    <line x1="0" y1="0" x2="30" y2="0" stroke="#4caf50" stroke-width="2"/>
    <circle cx="35" cy="0" r="5" fill="none" stroke="#4caf50" stroke-width="2"/>
    <line x1="40" y1="0" x2="50" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="-10" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="10" stroke="#4caf50" stroke-width="2"/>
    <text x="40" y="30" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#666666">Zero or Many</text>
  </g>

  <!-- Composed: One or Many -->
  <g transform="translate(200, 150)">
    <line x1="0" y1="0" x2="32" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="35" y1="-7" x2="35" y2="7" stroke="#4caf50" stroke-width="2"/>
    <line x1="38" y1="0" x2="50" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="-10" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="50" y1="0" x2="80" y2="10" stroke="#4caf50" stroke-width="2"/>
    <text x="40" y="30" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#666666">One or Many</text>
  </g>

  <!-- Composed: Zero or One -->
  <g transform="translate(325, 150)">
    <line x1="0" y1="0" x2="30" y2="0" stroke="#4caf50" stroke-width="2"/>
    <circle cx="35" cy="0" r="5" fill="none" stroke="#4caf50" stroke-width="2"/>
    <line x1="40" y1="0" x2="55" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="58" y1="-7" x2="58" y2="7" stroke="#4caf50" stroke-width="2"/>
    <line x1="61" y1="0" x2="80" y2="0" stroke="#4caf50" stroke-width="2"/>
    <text x="40" y="30" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#666666">Zero or One</text>
  </g>

  <!-- Composed: Exactly One -->
  <g transform="translate(450, 150)">
    <line x1="0" y1="0" x2="32" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="35" y1="-7" x2="35" y2="7" stroke="#4caf50" stroke-width="2"/>
    <line x1="38" y1="0" x2="52" y2="0" stroke="#4caf50" stroke-width="2"/>
    <line x1="55" y1="-7" x2="55" y2="7" stroke="#4caf50" stroke-width="2"/>
    <line x1="58" y1="0" x2="80" y2="0" stroke="#4caf50" stroke-width="2"/>
    <text x="40" y="30" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#666666">Exactly One</text>
  </g>
</svg>

---

### One-to-Many (1:N) - Customer places Orders

<svg width="700" height="180" viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <!-- Background (canvas color) -->
  <rect width="700" height="180" fill="#f5f6f8"/>

  <!-- Customer Concept Node -->
  <g transform="translate(50, 50)">
    <!-- Node container -->
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <!-- Left accent border (domain color - blue for Sales) -->
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#4a9eff"/>
    <!-- Shadow -->
    <filter id="shadow1" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.04"/>
    </filter>

    <!-- Name -->
    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Customer</text>

    <!-- Footer: Model count + Domain -->
    <g transform="translate(20, 50)">
      <!-- Model count badge -->
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">3</text>
      <!-- Domain label -->
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">SALES</text>
    </g>
  </g>

  <!-- Relationship Line with Crow's Foot -->
  <g>
    <!-- Main line (Bezier curve simplified as straight for mockup) -->
    <path d="M 200 90 C 280 90, 380 90, 460 90" fill="none" stroke="#4caf50" stroke-width="2"/>

    <!-- Source end: Exactly One (||) -->
    <line x1="205" y1="82" x2="205" y2="98" stroke="#4caf50" stroke-width="2"/>
    <line x1="212" y1="82" x2="212" y2="98" stroke="#4caf50" stroke-width="2"/>

    <!-- Target end: Zero or Many (○⋔) -->
    <circle cx="448" cy="90" r="5" fill="none" stroke="#4caf50" stroke-width="2"/>
    <line x1="455" y1="90" x2="480" y2="78" stroke="#4caf50" stroke-width="2"/>
    <line x1="455" y1="90" x2="480" y2="90" stroke="#4caf50" stroke-width="2"/>
    <line x1="455" y1="90" x2="480" y2="102" stroke="#4caf50" stroke-width="2"/>

    <!-- Verb label -->
    <rect x="295" y="72" width="70" height="24" rx="4" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <text x="330" y="88" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="500" fill="#1a1a2e">places</text>
  </g>

  <!-- Order Concept Node -->
  <g transform="translate(500, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#4a9eff"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Order</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">5</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">SALES</text>
    </g>
  </g>

  <!-- Legend -->
  <text x="350" y="155" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">Source: ││ (exactly one) — Target: ○⋔ (zero or many)</text>
  <text x="350" y="170" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">"One Customer places zero or many Orders"</text>
</svg>

---

### One-to-One (1:1) - User has Profile

<svg width="700" height="180" viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <rect width="700" height="180" fill="#f5f6f8"/>

  <!-- User Concept Node -->
  <g transform="translate(50, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#9c27b0"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">User</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">2</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">IDENTITY</text>
    </g>
  </g>

  <!-- Relationship Line -->
  <g>
    <path d="M 200 90 C 280 90, 380 90, 460 90" fill="none" stroke="#4caf50" stroke-width="2"/>

    <!-- Source end: Exactly One (||) -->
    <line x1="205" y1="82" x2="205" y2="98" stroke="#4caf50" stroke-width="2"/>
    <line x1="212" y1="82" x2="212" y2="98" stroke="#4caf50" stroke-width="2"/>

    <!-- Target end: Exactly One (||) -->
    <line x1="468" y1="82" x2="468" y2="98" stroke="#4caf50" stroke-width="2"/>
    <line x1="475" y1="82" x2="475" y2="98" stroke="#4caf50" stroke-width="2"/>

    <!-- Verb label -->
    <rect x="305" y="72" width="50" height="24" rx="4" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <text x="330" y="88" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="500" fill="#1a1a2e">has</text>
  </g>

  <!-- Profile Concept Node -->
  <g transform="translate(500, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#9c27b0"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Profile</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">2</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">IDENTITY</text>
    </g>
  </g>

  <text x="350" y="155" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">Both ends: ││ (exactly one)</text>
  <text x="350" y="170" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">"Each User has exactly one Profile"</text>
</svg>

---

### Many-to-Many (N:M) - Student enrolls in Course

<svg width="700" height="180" viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <rect width="700" height="180" fill="#f5f6f8"/>

  <!-- Student Concept Node -->
  <g transform="translate(50, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#4caf50"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Student</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">8</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">ACADEMIC</text>
    </g>
  </g>

  <!-- Relationship Line -->
  <g>
    <path d="M 200 90 C 280 90, 380 90, 460 90" fill="none" stroke="#4caf50" stroke-width="2"/>

    <!-- Source end: Zero or Many (○⋔) - reversed direction -->
    <line x1="200" y1="90" x2="225" y2="78" stroke="#4caf50" stroke-width="2"/>
    <line x1="200" y1="90" x2="225" y2="90" stroke="#4caf50" stroke-width="2"/>
    <line x1="200" y1="90" x2="225" y2="102" stroke="#4caf50" stroke-width="2"/>
    <circle cx="232" cy="90" r="5" fill="none" stroke="#4caf50" stroke-width="2"/>

    <!-- Target end: Zero or Many (○⋔) -->
    <circle cx="448" cy="90" r="5" fill="none" stroke="#4caf50" stroke-width="2"/>
    <line x1="455" y1="90" x2="480" y2="78" stroke="#4caf50" stroke-width="2"/>
    <line x1="455" y1="90" x2="480" y2="90" stroke="#4caf50" stroke-width="2"/>
    <line x1="455" y1="90" x2="480" y2="102" stroke="#4caf50" stroke-width="2"/>

    <!-- Verb label -->
    <rect x="295" y="72" width="70" height="24" rx="4" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <text x="330" y="88" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="500" fill="#1a1a2e">enrolls_in</text>
  </g>

  <!-- Course Concept Node -->
  <g transform="translate(500, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#4caf50"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Course</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">4</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">ACADEMIC</text>
    </g>
  </g>

  <text x="350" y="155" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">Both ends: ○⋔ (zero or many)</text>
  <text x="350" y="170" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">"Students can enroll in many Courses, Courses can have many Students"</text>
</svg>

---

### Draft Relationship Example

<svg width="700" height="180" viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <rect width="700" height="180" fill="#f5f6f8"/>

  <!-- Source Node (Draft) -->
  <g transform="translate(50, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#cccccc" stroke-width="1" stroke-dasharray="5,3"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#9e9e9e" stroke-dasharray="5,3"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Invoice</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">1</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">BILLING</text>
    </g>
  </g>

  <!-- Relationship Line (Draft - dashed, gray) -->
  <g>
    <path d="M 200 90 C 280 90, 380 90, 460 90" fill="none" stroke="#9e9e9e" stroke-width="2" stroke-dasharray="5,5"/>

    <!-- Source end: Exactly One (||) - gray -->
    <line x1="205" y1="82" x2="205" y2="98" stroke="#9e9e9e" stroke-width="2"/>
    <line x1="212" y1="82" x2="212" y2="98" stroke="#9e9e9e" stroke-width="2"/>

    <!-- Target end: One or Many (|⋔) - gray -->
    <line x1="455" y1="82" x2="455" y2="98" stroke="#9e9e9e" stroke-width="2"/>
    <line x1="460" y1="90" x2="480" y2="78" stroke="#9e9e9e" stroke-width="2"/>
    <line x1="460" y1="90" x2="480" y2="90" stroke="#9e9e9e" stroke-width="2"/>
    <line x1="460" y1="90" x2="480" y2="102" stroke="#9e9e9e" stroke-width="2"/>

    <!-- Verb label -->
    <rect x="295" y="72" width="70" height="24" rx="4" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <text x="330" y="88" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="500" fill="#9e9e9e">contains</text>
  </g>

  <!-- Target Node -->
  <g transform="translate(500, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#ff9800"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">LineItem</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">3</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">BILLING</text>
    </g>
  </g>

  <text x="350" y="155" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">Draft relationship: dashed line, gray color</text>
  <text x="350" y="170" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">Source: ││ (exactly one) — Target: │⋔ (one or many)</text>
</svg>

---

### No Cardinality (Current Arrow Style)

<svg width="700" height="180" viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <rect width="700" height="180" fill="#f5f6f8"/>

  <!-- Source Node -->
  <g transform="translate(50, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#4a9eff"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Entity A</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">2</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">DOMAIN</text>
    </g>
  </g>

  <!-- Relationship Line with arrow (no cardinality) -->
  <g>
    <path d="M 200 90 C 280 90, 380 90, 470 90" fill="none" stroke="#4caf50" stroke-width="2"/>

    <!-- Arrow at target end -->
    <polygon points="470,90 458,84 458,96" fill="#4caf50"/>

    <!-- Verb label -->
    <rect x="295" y="72" width="70" height="24" rx="4" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <text x="330" y="88" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="500" fill="#1a1a2e">relates_to</text>
  </g>

  <!-- Target Node -->
  <g transform="translate(500, 50)">
    <rect x="0" y="0" width="150" height="80" rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="0" y="0" width="3" height="80" rx="1.5" fill="#4a9eff"/>

    <text x="75" y="35" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#1a1a2e">Entity B</text>

    <g transform="translate(20, 50)">
      <rect x="0" y="0" width="28" height="22" rx="3" fill="#e8f4ff"/>
      <text x="14" y="15" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#4a9eff">4</text>
      <text x="38" y="14" font-family="Inter, sans-serif" font-size="9" font-weight="500" fill="#666666" letter-spacing="0.3">DOMAIN</text>
    </g>
  </g>

  <text x="350" y="155" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">No cardinality defined: simple arrow (current behavior)</text>
  <text x="350" y="170" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#888888">Backward compatible with existing relationships</text>
</svg>

---

## Mapping from Current Cardinality Values

| Current Value | Source Symbol | Target Symbol | Interpretation |
|---------------|---------------|---------------|----------------|
| `1:1` | `││` | `││` | Exactly one on both ends |
| `1:N` | `││` | `○⋔` | One source, zero-or-many targets |
| `N:1` | `○⋔` | `││` | Zero-or-many sources, one target |
| `N:M` | `○⋔` | `○⋔` | Zero-or-many on both ends |
| (none) | — | `▶` | Keep current arrow, no cardinality symbols |

---

## Implementation Considerations

### 1. SVG Markers

React Flow uses SVG `<marker>` elements for edge endpoints. We need custom marker definitions:

```tsx
// In Canvas.tsx or a dedicated MarkerDefs component
<defs>
  <marker id="crowsfoot-zero-many" ...>
    {/* Ring + crow's foot */}
  </marker>
  <marker id="crowsfoot-one-many" ...>
    {/* Bar + crow's foot */}
  </marker>
  <marker id="crowsfoot-zero-one" ...>
    {/* Ring + bar */}
  </marker>
  <marker id="crowsfoot-one-one" ...>
    {/* Bar + bar */}
  </marker>
</defs>
```

### 2. Edge Configuration

Update edge creation in Canvas.tsx:

```tsx
// Current
markerEnd: { type: 'arrowclosed' }

// Proposed
markerStart: getMarkerForCardinality(cardinality, 'source'),
markerEnd: getMarkerForCardinality(cardinality, 'target'),
```

### 3. Color Inheritance

Markers should inherit or match the edge stroke color (status-based):
- Complete: `#4caf50` (green)
- Draft: `#9e9e9e` (gray)
- Stub: `#f5a623` (orange)
- Error: `#dc2626` (red)

### 4. Label Changes

- **Keep**: Verb label at center of edge
- **Remove**: Cardinality text (now shown via symbols)
- **Keep**: Model count badge (optional)

### 5. Sizing Guidelines

Based on current edge stroke width of 2px:

| Element | Size |
|---------|------|
| Ring radius | 5px |
| Bar length | 16px (8px each side of line) |
| Crow's foot spread | 12px per outer prong |
| Crow's foot angle | ~30° |
| Symbol spacing | 5px |
| Total marker width | ~25px |

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/types.ts` | Keep existing `Cardinality` type |
| `frontend/src/components/Canvas.tsx` | Add marker defs, update edge config |
| `frontend/src/components/RelationshipEdge.tsx` | Remove cardinality text from label |
| `frontend/src/tokens.css` | Add marker styling if needed |

---

## Testing Checklist

- [ ] All four cardinality types render correctly
- [ ] Symbols orient correctly on curved Bezier paths
- [ ] Colors match edge status (complete/draft/stub/error)
- [ ] Self-referential relationships display properly
- [ ] Edges without cardinality show arrow only
- [ ] Symbols scale appropriately if zoom is implemented
- [ ] Export formats (PNG, SVG via Excalidraw) preserve symbols
