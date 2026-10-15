# Network Swiss Tool Pro - UI/UX Philosophy

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Design principles and aesthetic standards for the Network Swiss Tool Pro interface. |
| **Scope** | Glassmorphism, NOC-grade observability, typography, and color systems. |
| **Related Documents** | [Visualization Pipeline](../01-architecture/visualization-pipeline.md), [Project Overview](../00-overview/project-overview.md) |
| **Update Responsibility** | UI/UX Lead / Creative Director |
| **Version Awareness** | v6.9.1 (NOC Dashboard Edition) |

---

## Core Principles

### 1. High-Tech NOC Aesthetics
The interface is designed to evoke a modern, data-dense NOC (Network Operations Center) environment. It prioritizes clarity and status visualization over generic decorative elements.

### 2. Glassmorphism (Apple-Style)
As of v6.9.1, the UI adheres to a "Glassmorphism" aesthetic:
- **Translucency:** Side panels and cards use `backdrop-blur` and semi-transparent backgrounds.
- **Elevation:** Subtle shadows and border-glows create depth without visual clutter.
- **High-Density Data:** Information is packed efficiently but remains legible through strict grid alignment.

### 3. Progressive Disclosure (The 3-View System)
To prevent "information overload", the topology visualizer uses a 3-view disclosure model:
1. **Global View:** High-level logical structure (VPC domains, core links).
2. **Detail View:** Deep dive into a specific domain or device on click.
3. **Intelligence View:** Comparative analytics (Shared vs. Orphan links).

## Design Tokens

### Typography
- **Primary Font:** SF Pro (Apple) or Inter (Google Fonts).
- **Monospace Font:** JetBrains Mono (for CLI and raw data).

### Color System
- **Indigo (#6366f1):** Primary branding and VPC domain nodes.
- **Blue (#3b82f6):** Healthy shared links.
- **Red (#ef4444):** Critical errors / Orphan links.
- **Purple (#a855f7):** Peer-links and logical clusters.

## Animation & Micro-interactions
- **Transitions:** All state changes use a 150-250ms ease-in-out transition.
- **Node Glows:** Active links or selected nodes feature a subtle outer-glow animation to draw attention.
- **Slide-in Panels:** Detail panels slide in from the right to maintain spatial context.

## Best Practices for UI Extension
- **Avoid Generic Colors:** Never use `#ff0000` for red; use the design system's `--vpc-error` token.
- **Maintain Grid Alignment:** Align all card-based content to the 8px base grid.
- **Mobile-First Responsiveness:** Ensure all new components stack correctly on tablet and mobile widths (<900px).
