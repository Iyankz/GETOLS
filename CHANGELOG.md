# Changelog

All notable changes to GETOLS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-01-30

### Changed
- **CLI Access**: ZTE OLT now uses Telnet only (removed SSH option)
- **SNMP v2c**: Separated into RO (Read-Only) and RW (Read-Write) communities
  - SNMP RO: Used for monitoring operations
  - SNMP RW: Optional, Admin-only, for ONU reset/maintenance (all usage logged)
- **Logo Display**: Increased logo sizes for better branding
  - Login page: 300px width
  - Sidebar: 180-200px width
  - Header: 120-140px width
- **Logo Background**: Removed black background, now transparent PNG

### Added
- SNMP Setup Scripts helper on Add OLT page (copy-paste ready)
- SNMP RW community field (AES-256-GCM encrypted)
- SNMP RW usage logging in Activity Log
- Header logo display
- Alembic migration for SNMP RW column

### Fixed
- SQLAlchemy DetachedInstanceError on user session
- User null-safety checks in templates
- Activity, Users, Templates pages full implementation
- Favicon now properly displayed (32x32 ICO/PNG)

### Security
- All SNMP RW operations are logged with user, timestamp, and target
- SNMP RW access restricted to Admin role only
- SNMP RW cannot be used for primary provisioning

---

## [1.0.0] - 2026-01-30

### 🎉 Initial Stable Release

First production-ready release of GETOLS.

### Added

#### Core Features
- Web-based dashboard with HTMX + Jinja2
- FastAPI backend with async support
- MariaDB database with SQLAlchemy ORM
- Alembic database migrations

#### OLT Management
- Support for ZTE ZXA10 C300 (GPON)
- Support for ZTE ZXA10 C320 (GPON)
- Telnet connection for CLI access
- Custom port support for port forwarding scenarios
- Separate RO (Read-Only) and RW (Read-Write) CLI credentials
- Separate SNMP RO and RW communities
- Connection testing for CLI and SNMP

#### ONU Operations
- ONU Discovery via CLI commands
- ONU Registration with template support
- ONU Deletion with confirmation
- Manual parameter override during provisioning
- Provisioning templates for quick deployment

#### Monitoring
- SNMP v2c read-only monitoring
- ONU status monitoring (Online/Offline/Low Signal)
- RX/TX optical power levels
- Signal quality indicators

#### Security
- Role-Based Access Control (Admin/Operator/Viewer)
- AES-256-GCM credential encryption at rest
- Secure session cookies (HttpOnly, Secure, SameSite)
- Password policy enforcement (8+ chars, mixed case, number)
- Single session per user enforcement
- Randomly generated admin password on installation
- Activity logging with full audit trail

#### CLI Tools
- `getols reset-password` - Reset user password
- `getols list-users` - List all users
- `getols list-olts` - List configured OLTs
- `getols create-admin` - Create new admin user
- `getols cleanup-sessions` - Clean expired sessions
- `getols cleanup-logs` - Clean old activity logs

#### Installation
- One-command installer for Ubuntu 24.04 / Debian 12
- Automatic dependency installation
- Secure password generation
- Systemd service configuration
- Verbose installation output

### Security Notes
- SNMP SET operations restricted to Admin only (ONU reset)
- SNMP RW usage fully logged in Activity Log
- RO credentials cannot perform provisioning
- RW credentials are not used for monitoring
- All sensitive credentials encrypted at rest

---

## [0.1.0] - 2026-01-18

### Added
- Initial concept and architecture
- Workflow design
- Command definitions
- Web dashboard menu structure
- Project documentation

---

## Future Roadmap

### [1.1.0] - Planned
- Huawei MA5xxx support
- Bulk ONU provisioning
- Export/Import templates
- Dashboard statistics charts

### [1.2.0] - Planned
- FiberHome AN5xxx support
- Telegram Bot integration
- Email notifications
- Scheduled tasks

### [2.0.0] - Planned
- Multi-tenant support
- API authentication (JWT)
- Webhook integrations
- Custom adapter SDK
