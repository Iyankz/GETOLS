<div align="center">
  <img src="assets/GETOLS%20Logo.png" alt="GETOLS Logo" width="400">
</div>

<div align="center">

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420?logo=ubuntu&logoColor=white)
![Debian 12](https://img.shields.io/badge/Debian-12-A81D33?logo=debian&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-10.x-003545?logo=mariadb&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

---

# GETOLS  
**Gateway for Extended OLT Services**

GETOLS adalah platform gateway open-source untuk mengelola operasional **OLT dan ONU multi-vendor** melalui satu interface web yang aman dan terkontrol.

---

## 🧠 Asal Nama GETOLS

### Makna Bahasa Sunda
Dalam bahasa Sunda, kata **getol** berarti:
> **rajin, tekun, konsisten dalam bekerja**

### Makna Teknis
> **Gateway for Extended OLT Services**

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🔌 **Multi-OLT Support** | ZTE ZXA10 C300 & C320 (GPON) |
| 🔐 **Dual Credential** | Pemisahan RO (monitoring) & RW (provisioning) |
| 🔍 **ONU Discovery** | Deteksi ONU yang belum terdaftar via CLI |
| ⚡ **ONU Provisioning** | Registrasi ONU dengan template support |
| 📊 **SNMP Monitoring** | Read-only monitoring RX/TX power |
| 🛡️ **Security** | AES-256-GCM encryption, RBAC, session management |
| 📝 **Activity Logging** | Audit trail lengkap untuk semua aksi |
| 🎨 **Modern UI** | HTMX + Jinja2 responsive web interface |
| 🔧 **Custom Port** | Support port forwarding untuk SSH/Telnet |

---

## 🖼️ Screenshots

> *Screenshots akan ditambahkan setelah deployment*

---

## 📋 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Ubuntu 24.04 LTS / Debian 12 | Ubuntu 24.04 LTS |
| **CPU** | 1 Core | 2+ Cores |
| **RAM** | 1 GB | 2+ GB |
| **Storage** | 10 GB | 20+ GB |
| **Python** | 3.10+ | 3.12 |

---

## 🚀 Quick Installation

### One-Line Install (Recommended)

```bash
# Clone repository
git clone https://github.com/Iyankz/GETOLS.git
cd GETOLS

# Run installer
chmod +x install.sh
sudo ./install.sh
```

### What the installer does:
1. ✅ Installs system dependencies (Python, MariaDB, SNMP)
2. ✅ Creates database and secure user
3. ✅ Sets up Python virtual environment
4. ✅ Configures GETOLS application
5. ✅ Creates systemd service
6. ✅ **Generates secure random admin password**
7. ✅ Displays access credentials

> ⚠️ **Important**: Save the generated password! It will NOT be shown again.

---

## 🔑 Default Access

Setelah instalasi, Anda akan melihat:

```
╔══════════════════════════════════════════════════════════════╗
│  ACCESS INFORMATION                                          │
├──────────────────────────────────────────────────────────────┤
│  URL      : http://<SERVER_IP>:8000                          │
│  Username : admin                                            │
│  Password : <RANDOMLY_GENERATED>                             │
└──────────────────────────────────────────────────────────────┘
```

> 🔒 Password di-generate secara random untuk keamanan. Tidak ada default password.

---

## 📁 Project Structure

```
GETOLS/
├── app/
│   ├── adapters/          # Vendor-specific OLT adapters
│   │   └── zte/           # ZTE C300 & C320 adapters
│   ├── api/               # FastAPI routes
│   ├── core/              # Config, security, database
│   ├── models/            # SQLAlchemy models
│   ├── services/          # Business logic layer
│   ├── snmp/              # SNMP monitoring module
│   ├── templates/         # Jinja2 templates
│   │   ├── layouts/       # Base layouts
│   │   ├── pages/         # Page templates
│   │   └── components/    # Reusable components
│   ├── static/            # CSS, JS, images
│   └── main.py            # Application entry point
├── cli/                   # CLI tools
├── migrations/            # Alembic database migrations
├── assets/                # Logo and documentation assets
├── install.sh             # Auto-installer script
├── requirements.txt       # Python dependencies
├── .env.example           # Environment configuration template
└── README.md
```

---

## ⚙️ Manual Configuration

### Environment Variables

Copy `.env.example` ke `.env` dan sesuaikan:

```bash
cp .env.example .env
nano .env
```

```ini
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/getols_db

# Security (generate dengan: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Session
SESSION_LIFETIME=60

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

---

## 🛠️ Service Management

```bash
# Check status
sudo systemctl status getols

# Start service
sudo systemctl start getols

# Stop service
sudo systemctl stop getols

# Restart service
sudo systemctl restart getols

# View logs
sudo journalctl -u getols -f
```

---

## 💻 CLI Commands

```bash
# Show help
getols --help

# List users
getols list-users

# List OLTs
getols list-olts

# Reset password
getols reset-password -u admin

# Create new admin
getols create-admin

# Cleanup expired sessions
getols cleanup-sessions

# Show version
getols version
```

---

## 👥 User Roles

| Role | Dashboard | OLT Mgmt | Discovery | Provisioning | Templates | Users |
|------|:---------:|:--------:|:---------:|:------------:|:---------:|:-----:|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Operator** | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 🔒 Security Features

- **Password Policy**: Min 8 chars, uppercase, lowercase, number
- **AES-256-GCM**: Encrypted OLT credentials at rest
- **Session Management**: Single session per user
- **RBAC**: Role-based access control
- **Secure Cookies**: HttpOnly, Secure, SameSite
- **SNMP Read-Only**: No write operations via SNMP
- **Credential Separation**: RO & RW credentials separated
- **Activity Logging**: Full audit trail

---

## 📊 Supported OLT Models

| Vendor | Model | Status | Notes |
|--------|-------|--------|-------|
| ZTE | ZXA10 C300 | ✅ Supported | GPON |
| ZTE | ZXA10 C320 | ✅ Supported | GPON |
| Huawei | MA5xxx | 🔜 Planned | Future release |
| FiberHome | AN5xxx | 🔜 Planned | Future release |

---

## 🔧 Adding New OLT

1. Login sebagai Admin
2. Navigate ke **OLT Management**
3. Click **Add OLT**
4. Fill in:
   - OLT Name
   - OLT Type (C300/C320)
   - IP Address
   - Connection Type (SSH/Telnet)
   - Port (default: 22 for SSH, 23 for Telnet)
   - RO Credentials (for discovery & monitoring)
   - RW Credentials (for provisioning)
   - SNMP Community & Port

---

## 📝 Changelog

Lihat [CHANGELOG.md](CHANGELOG.md) untuk riwayat perubahan lengkap.

---

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Yayang Ardiansyah (Iyankz)**

- GitHub: [@Iyankz](https://github.com/Iyankz)
- Website: [Iyankz.github.io](https://Iyankz.github.io)

---

## 🙏 Acknowledgements

- FastAPI Team
- ZTE Documentation
- All contributors and testers

---

<div align="center">

**Built with ❤️ & ☕ by Iyankz and Brother**

</div>
