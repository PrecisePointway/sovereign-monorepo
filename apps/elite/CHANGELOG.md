# Changelog

All notable changes to Sovereign Sanctuary Elite are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-25

### Added
- **Safety Tools**
  - `safety_guardrail_check.py` - System invariant verification
  - `verify_restore_point.py` - Restore point integrity checker
  - `verify_snapshot_safety.py` - Snapshot verification with temporal checks

- **Restore System**
  - `create_restore_point.py` - Immutable restore point creation
  - `restore_from_point.py` - Safe restoration with backup
  - `restore_allowlist.txt` - Configurable file allowlist

- **Evidence Snapshots**
  - `create_evidence_snapshot.py` - External-facing proof artifacts
  - Auto-generated VERIFY.sh for one-command verification

- **Mirror Takedown**
  - `mirror_takedown.py` - Controlled takedown protocol
  - Failsafe dry-run default
  - Hash-matched confirmation required

- **Documentation**
  - Complete architecture documentation
  - Deployment guide with multi-environment support
  - Safety protocol documentation
  - Code review report
  - PDCA cycle reports (5 cycles)

- **Deployment**
  - Dockerfile with multi-stage build
  - docker-compose.yml for development
  - GitHub Actions CI pipeline

### Fixed
- **HMAC Signature Bug** in verified-agent-elite.ts
  - Fixed signature verification that was always failing
  - Excluded outputSignature from audit trail recomputation

- **Disk Space Threshold Bug** in self_heal_monitor.py
  - Corrected inverted threshold calculation
  - Now correctly warns when free space drops below threshold

- **Infinite Loop Bug** in flight_control_daemon.py
  - Added debouncing to prevent event loops
  - Configurable debounce interval

- **Bare Except Clauses** across multiple files
  - Replaced with specific exception types
  - Improved error logging and debugging

### Changed
- Upgraded to Python 3.11+ requirement
- Standardized on SHA-256 for all hashing
- Unified configuration format (JSON + YAML)

### Security
- All destructive operations require explicit confirmation
- Hash-matched authorization for takedown operations
- Audit trail for all safety-related operations

## [1.0.0] - 2026-01-20

### Added
- Initial release
- Core daemon and models
- Basic self-heal monitor
- Flight control daemon
- Verified agent (TypeScript)

---

[2.0.0]: https://github.com/architect/sovereign-sanctuary-elite/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/architect/sovereign-sanctuary-elite/releases/tag/v1.0.0
