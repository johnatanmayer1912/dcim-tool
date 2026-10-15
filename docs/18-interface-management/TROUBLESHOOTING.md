# Troubleshooting Guide: Visual Interface Management System

## Common Errors & Resolutions
- **Issue: Discovered Interfaces display is blank**
  - *Resolution*: Confirm target switch IP credentials in the sidebar. Check the Console panel log output for any SSH connection/authentication errors.
- **Issue: Validation Step 4 (Conflicts) fails**
  - *Resolution*: Ensure that your configuration name matches the selected interface. Conflicts occur if you attempt to switch operational modes (e.g. Access to Trunk) without executing cleanups.
- **Issue: Diff output shows no change**
  - *Resolution*: Ensure that Proposed Configuration lines differ from Current Configuration.
- **Issue: Deployment fails due to timeout**
  - *Resolution*: Confirm device is online and credentials are not locked. Check physical connectivity.
