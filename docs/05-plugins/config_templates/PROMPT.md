# Prompt Instructions — Template-Based Configuration Generator Plugin

# Purpose
Guides AI systems and engineers on maintaining, debugging, or expanding the config templates plugin.

# Scope
Variable extractors, template bootstrap code, and Jinja2 rendering overrides.

---

## Guidelines for Modification
1. **Bootstrap Templates**:
   - To add default templates, modify `bootstrap_example_templates()` and add the snippet block inside the `examples` dictionary.
2. **Variable Parsing**:
   - If you need to support complex variables (e.g. structured maps or nested arrays), modify `extract_template_variables()` to match custom formats.
3. **Environment Isolation**:
   - Ensure `_get_resource_path()` logic is used consistently to find the `templates/` folder in PyInstaller EXE mode.
