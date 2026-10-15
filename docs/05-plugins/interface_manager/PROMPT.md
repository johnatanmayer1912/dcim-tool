# Development Instructions - Interface Configuration Manager Plugin

## Plugin Creation

This plugin was created to provide enterprise-grade interface configuration management for Network Swiss Tool Pro.

## Development Guidelines

### Plugin Structure
- Follow the base_template.py structure
- Include METADATA dictionary with all required fields
- Implement run() function with exact signature
- Use only allowed imports (no os.system, subprocess, etc.)
- Generate human-readable reports

### Version Requirements
- Version MUST be in Semantic Format: MAJOR.MINOR.PATCH
- Update VERSION HISTORY on EVERY change
- Update changelog array in METADATA on EVERY change

### Documentation Requirements
- Create docs/plugins/{plugin_id}/ folder
- Create 6 documentation files:
  - README.md - Current version documentation
  - RELEASE_NOTES.md - All release notes history
  - PROMPT.md - Creation/modification instructions (this file)
  - CHANGELOG.md - Detailed changelog
  - TEST_RESULTS.md - Test results by version
  - COMPATIBILITY.md - Platform compatibility
- Create version archive: docs/plugins/{plugin_id}/versions/vX.Y.Z/
- Generate manifest.json for each version

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings for all functions
- Handle errors gracefully
- Log via log_func callback for UI updates

### Testing
- Write unit tests for all functions
- Test with all supported vendors
- Test error scenarios
- Achieve >80% code coverage
- Document test results in TEST_RESULTS.md

### Safety Mechanisms
- Implement dry-run mode
- Implement pre-change backup
- Implement post-change verification
- Implement rollback capability
- Validate all inputs

### Vendor Support
- Support Cisco NX-OS, IOS, IOS-XE, Juniper JUNOS
- Use vendor-specific commands
- Parse vendor-specific output
- Handle vendor-specific syntax

## Modification Instructions

### When Adding New Features
1. Update METADATA version (increment MINOR for new features)
2. Add entry to changelog array in METADATA
3. Update VERSION HISTORY in docstring
4. Implement feature
5. Write/update tests
6. Update documentation
7. Archive old version to versions/ folder
8. Generate manifest.json

### When Fixing Bugs
1. Update METADATA version (increment PATCH for bug fixes)
2. Add entry to changelog array in METADATA
3. Update VERSION HISTORY in docstring
4. Fix bug
5. Write/update tests
6. Update documentation
7. Archive old version to versions/ folder
8. Generate manifest.json

### When Adding New Vendor Support
1. Update METADATA version (increment MINOR)
2. Add entry to changelog array in METADATA
3. Update VERSION HISTORY in docstring
4. Add vendor to VENDOR_COMMANDS dictionary
5. Implement vendor-specific parser
6. Add vendor-specific validation
7. Test with actual vendor devices
8. Update documentation
9. Update COMPATIBILITY.md
10. Archive old version to versions/ folder
11. Generate manifest.json

## Code Review Checklist

- [ ] METADATA includes all required fields
- [ ] Version follows SemVer format
- [ ] Changelog updated in METADATA
- [ ] VERSION HISTORY updated in docstring
- [ ] run() function has correct signature
- [ ] Only allowed imports used
- [ ] Error handling implemented
- [ ] log_func callback used for logging
- [ ] Human-readable report generated
- [ ] Unit tests written
- [ ] Documentation updated
- [ ] Version archived
- [ ] manifest.json generated

## Testing Checklist

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Vendor tests pass for all supported vendors
- [ ] Error scenarios tested
- [ ] Performance tested
- [ ] Security tested
- [ ] Code coverage >80%
- [ ] Test results documented in TEST_RESULTS.md

## Deployment Checklist

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Version archived
- [ ] manifest.json generated
- [ ] RELEASE_NOTES.md updated
- [ ] COMPATIBILITY.md updated
- [ ] Ready for production

## Common Issues and Solutions

### Issue: Plugin not appearing in UI
**Solution**: Check that METADATA has all required fields and plugin_id is unique

### Issue: Connection timeout
**Solution**: Increase timeout in config or check network connectivity

### Issue: Parsing errors
**Solution**: Verify vendor-specific parser handles device output correctly

### Issue: Validation failures
**Solution**: Check validation logic and vendor-specific syntax rules

### Issue: Deployment failures
**Solution**: Check pre-change backup, verify configuration syntax, check device permissions

## Contact

For questions or issues, contact the Network Engineering Team.
