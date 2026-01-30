# Changelog

All notable changes to GETOLS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- SSH and Telnet connection options
- Custom port support for port forwarding scenarios
- Separate RO (Read-Only) and RW (Read-Write) credentials
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
- SNMP SET operations are explicitly blocked
- RO credentials cannot perform provisioning
- RW credentials are not used for monitoring
- Telnet usage displays security warning
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
