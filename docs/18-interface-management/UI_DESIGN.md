# UI Design Document: Visual Interface Management System

## Visual Aesthetics
- **Grid Map**: Display ports in a multi-column responsive flex grid mimicking switch blades/panels.
- **Indicators**:
  - Green indicator border for Operational Up ports.
  - Grey indicator border for Operational Down ports.
  - Red indicator border for Shutdown / Disabled ports.
- **Port-Channel Grouping**: Interfaces under port-channels feature a blue floating badge displaying their respective parent channel (e.g. `Po10`).

## Interactive Drawer
- Expanding an interface card details both current configuration and proposed settings in a split viewport.
- Buttons for:
  - **Validate Config**: Submits input to the dry-run validation pipeline.
  - **Deploy Config**: Triggers the safety confirmation dialog.
- Validation checklist renders as dynamic green/red indicators beneath the editor text area.
