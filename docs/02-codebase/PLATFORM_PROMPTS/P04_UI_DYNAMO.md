# 🧩 Puzzle Piece 4: The Dynamic Web UI

> **[OBJECTIVE]**
> Transform the Static Web UI into a "Dynamic Dashboard" that renders tool buttons and input fields automatically based on the results from the `/api/plugins/list` endpoint.

---

## 🛠️ Task 1: The "Plugin Manager" Tab
Add a new tab in `index.html` (alongside "VLAN Check", "MAC Trace", etc.) labeled **"Plugin Tools"**.

### Logic for JS (app.js):
1.  **Fetch**: On page load, query `/api/plugins/list`.
2.  **Render Sidebar**: For each plugin, create a sidebar button.
3.  **Render Widgets**: When a plugin is clicked:
    - Identify the `required_params` from the metadata.
    - Dynamically generate HTML `<input>` or `<select>` elements for each parameter.
    - Bind the "Execute" button to send a POST request with these dynamic parameters.

---

## 🛠️ Task 2: Dynamic Form Builder
Implement a utility function in the browser-side Javascript to handle different parameter types:
- `integer` -> `<input type="number">`
- `string` -> `<input type="text">`
- `checkbox` -> `<input type="checkbox">`
- `dropdown` (list) -> `<select>`

---

## ✅ QA Validation for the Agent
1.  **Zero-Button State**: If the `modules/plugins/` folder is empty, the "Plugin Tools" tab should display: *"No plugins installed. Drop a python file in modules/plugins to get started."*
2.  **Input Validation**: If a parameter in the metadata is marked as `required: True`, the UI "Execute" button must stay disabled until that field is filled.
3.  **Real-Time Output**: Confirm that logs from the plugin (sent via SocketIO) appear in the main console window exactly like the built-in tools.

---

**Next Action**: Once the UI can "talk" to the plugins, move to [P05_LIFECYCLE.md](./P05_LIFECYCLE.md) to build the safety and upload systems.
