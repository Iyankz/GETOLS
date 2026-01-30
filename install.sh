#!/bin/bash
#
# GETOLS v1.0.0 Installation Script
# Gateway for Extended OLT Services
#
# Supported OS: Ubuntu 24.04 LTS, Debian 12
# Repository: https://github.com/Iyankz/GETOLS
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
GETOLS_DIR="/opt/getols"
GETOLS_USER="getols"
GETOLS_GROUP="getols"
VENV_DIR="${GETOLS_DIR}/venv"
DB_NAME="getols_db"
DB_USER="getols"

# Generated credentials storage
DB_PASSWORD=""
ADMIN_PASSWORD=""

# Print banner
print_banner() {
    echo -e "${CYAN}"
    echo "  ██████╗ ███████╗████████╗ ██████╗ ██╗     ███████╗"
    echo " ██╔════╝ ██╔════╝╚══██╔══╝██╔═══██╗██║     ██╔════╝"
    echo " ██║  ███╗█████╗     ██║   ██║   ██║██║     ███████╗"
    echo " ██║   ██║██╔══╝     ██║   ██║   ██║██║     ╚════██║"
    echo " ╚██████╔╝███████╗   ██║   ╚██████╔╝███████╗███████║"
    echo "  ╚═════╝ ╚══════╝   ╚═╝    ╚═════╝ ╚══════╝╚══════╝"
    echo -e "${NC}"
    echo -e "${YELLOW}Gateway for Extended OLT Services - v1.0.0${NC}"
    echo -e "${BLUE}Installation Script${NC}"
    echo -e "${CYAN}https://github.com/Iyankz/GETOLS${NC}"
    echo ""
}

# Print step
print_step() {
    echo -e "\n${GREEN}[STEP]${NC} $1"
    echo "----------------------------------------"
}

# Print info
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Print warning
print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Print error
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print success
print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        echo "Please run: sudo ./install.sh"
        exit 1
    fi
    print_success "Running as root"
}

# Detect OS
detect_os() {
    print_step "Detecting Operating System"
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        PRETTY_NAME=$PRETTY_NAME
    else
        print_error "Cannot detect OS. This script supports Ubuntu 24.04 and Debian 12."
        exit 1
    fi
    
    print_info "Detected: $PRETTY_NAME"
    
    if [[ "$OS" != "ubuntu" && "$OS" != "debian" ]]; then
        print_error "Unsupported OS: $OS"
        print_error "This script supports Ubuntu 24.04 and Debian 12 only."
        exit 1
    fi
    
    print_success "OS is supported"
}

# Get server IP
get_server_ip() {
    # Try to get the primary IP address
    SERVER_IP=$(ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n1)
    
    if [[ -z "$SERVER_IP" ]]; then
        SERVER_IP=$(hostname -I | awk '{print $1}')
    fi
    
    if [[ -z "$SERVER_IP" ]]; then
        SERVER_IP="localhost"
    fi
    
    print_info "Server IP: $SERVER_IP"
}

# Generate random password
generate_password() {
    local length=${1:-24}
    openssl rand -base64 48 | tr -d '/+=' | head -c "$length"
}

# Install system dependencies
install_dependencies() {
    print_step "Installing System Dependencies"
    
    print_info "Updating package lists..."
    apt-get update
    
    print_info "Installing required packages..."
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        mariadb-server \
        mariadb-client \
        libmariadb-dev \
        libmariadb-dev-compat \
        snmp \
        libsnmp-dev \
        build-essential \
        libffi-dev \
        libssl-dev \
        curl \
        wget \
        git
    
    print_success "System dependencies installed"
}

# Setup MariaDB
setup_database() {
    print_step "Setting Up MariaDB Database"
    
    # Generate database password
    DB_PASSWORD=$(generate_password 24)
    print_info "Generated secure database password"
    
    # Start MariaDB if not running
    print_info "Starting MariaDB service..."
    systemctl start mariadb
    systemctl enable mariadb
    print_success "MariaDB service started"
    
    # Create database and user
    print_info "Creating database: ${DB_NAME}"
    mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    print_success "Database created"
    
    print_info "Creating database user: ${DB_USER}"
    mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
    mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    print_success "Database user created and privileges granted"
}

# Create system user
create_user() {
    print_step "Creating System User"
    
    if id "$GETOLS_USER" &>/dev/null; then
        print_info "User ${GETOLS_USER} already exists"
    else
        print_info "Creating user: ${GETOLS_USER}"
        useradd --system --home-dir "$GETOLS_DIR" --shell /bin/false "$GETOLS_USER"
        print_success "System user created"
    fi
}

# Install GETOLS
install_getols() {
    print_step "Installing GETOLS Application"
    
    # Create directory
    print_info "Creating directory: ${GETOLS_DIR}"
    mkdir -p "$GETOLS_DIR"
    
    # Copy files
    print_info "Copying application files..."
    cp -r . "$GETOLS_DIR/"
    print_success "Application files copied"
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    
    # Install Python dependencies
    print_info "Installing Python dependencies (this may take a few minutes)..."
    "$VENV_DIR/bin/pip" install -r "$GETOLS_DIR/requirements.txt"
    print_success "Python dependencies installed"
    
    # Generate secrets
    print_info "Generating security keys..."
    SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    print_success "Security keys generated"
    
    # Create .env file
    print_info "Creating configuration file..."
    cat > "$GETOLS_DIR/.env" << EOF
# GETOLS Configuration
# Generated on $(date)

APP_NAME=GETOLS
APP_VERSION=1.0.0
DEBUG=false

# Database
DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@localhost:3306/${DB_NAME}

# Security
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Session
SESSION_LIFETIME=60
COOKIE_SECURE=false
COOKIE_HTTPONLY=true
COOKIE_SAMESITE=lax

# OLT Connection
OLT_CONNECTION_TIMEOUT=10
OLT_COMMAND_TIMEOUT=30

# SNMP
SNMP_TIMEOUT=5
SNMP_RETRIES=3

# Server
HOST=0.0.0.0
PORT=8000
EOF
    print_success "Configuration file created"
    
    # Set permissions
    print_info "Setting file permissions..."
    chown -R "$GETOLS_USER:$GETOLS_GROUP" "$GETOLS_DIR"
    chmod 600 "$GETOLS_DIR/.env"
    print_success "File permissions set"
}

# Create CLI symlink
create_cli() {
    print_step "Creating CLI Tool"
    
    print_info "Creating getols command..."
    cat > /usr/local/bin/getols << EOF
#!/bin/bash
cd ${GETOLS_DIR}
${VENV_DIR}/bin/python ${GETOLS_DIR}/cli/getols_cli.py "\$@"
EOF
    
    chmod +x /usr/local/bin/getols
    print_success "CLI tool created: /usr/local/bin/getols"
}

# Create systemd service
create_service() {
    print_step "Creating Systemd Service"
    
    print_info "Creating service file..."
    cat > /etc/systemd/system/getols.service << EOF
[Unit]
Description=GETOLS - Gateway for Extended OLT Services
After=network.target mariadb.service

[Service]
Type=simple
User=${GETOLS_USER}
Group=${GETOLS_GROUP}
WorkingDirectory=${GETOLS_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    print_success "Service file created"
    
    print_info "Reloading systemd..."
    systemctl daemon-reload
    
    print_info "Enabling service..."
    systemctl enable getols
    
    print_info "Starting GETOLS service..."
    systemctl start getols
    
    # Wait for service to start
    sleep 3
    
    if systemctl is-active --quiet getols; then
        print_success "GETOLS service is running"
    else
        print_warning "Service may not have started correctly"
        print_info "Check logs with: journalctl -u getols -f"
    fi
}

# Initialize database and create admin
init_database() {
    print_step "Initializing Database"
    
    cd "$GETOLS_DIR"
    
    print_info "Creating database tables..."
    "$VENV_DIR/bin/python" -c "
from app.core.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
    print_success "Database tables created"
    
    # Generate admin password
    ADMIN_PASSWORD=$(generate_password 16)
    
    # Create default admin with generated password
    print_info "Creating admin user..."
    "$VENV_DIR/bin/python" << EOF
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

db = SessionLocal()

# Check if admin exists
existing = db.query(User).filter(User.username == 'admin').first()
if existing:
    print('Admin user already exists')
else:
    admin = User(
        username='admin',
        password_hash=hash_password('${ADMIN_PASSWORD}'),
        role=UserRole.ADMIN,
        full_name='System Administrator',
        must_change_password=True,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print('Admin user created successfully')

db.close()
EOF
    print_success "Admin user created"
}

# Print completion message
print_completion() {
    get_server_ip
    
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║          GETOLS Installation Complete!                       ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}┌──────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│  ACCESS INFORMATION                                          │${NC}"
    echo -e "${CYAN}├──────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│${NC}  URL      : ${YELLOW}http://${SERVER_IP}:8000${NC}"
    echo -e "${CYAN}│${NC}  Username : ${YELLOW}admin${NC}"
    echo -e "${CYAN}│${NC}  Password : ${YELLOW}${ADMIN_PASSWORD}${NC}"
    echo -e "${CYAN}└──────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠  IMPORTANT SECURITY NOTICE                               ║${NC}"
    echo -e "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${RED}║  • Save the password above - it will NOT be shown again!     ║${NC}"
    echo -e "${RED}║  • You MUST change this password on first login              ║${NC}"
    echo -e "${RED}║  • Keep these credentials secure                             ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  ${CYAN}systemctl status getols${NC}      - Check service status"
    echo -e "  ${CYAN}systemctl restart getols${NC}     - Restart service"
    echo -e "  ${CYAN}journalctl -u getols -f${NC}      - View live logs"
    echo -e "  ${CYAN}getols --help${NC}                - CLI help"
    echo -e "  ${CYAN}getols reset-password -u admin${NC} - Reset admin password"
    echo ""
    echo -e "${BLUE}Installation Details:${NC}"
    echo -e "  Directory     : ${GETOLS_DIR}"
    echo -e "  Configuration : ${GETOLS_DIR}/.env"
    echo -e "  Service       : /etc/systemd/system/getols.service"
    echo ""
    echo -e "${CYAN}Repository: https://github.com/Iyankz/GETOLS${NC}"
    echo -e "${CYAN}Built with ❤️ & ☕ by Iyankz and Brother${NC}"
    echo ""
}

# Save credentials to file
save_credentials() {
    local creds_file="${GETOLS_DIR}/CREDENTIALS.txt"
    
    cat > "$creds_file" << EOF
================================================
GETOLS Installation Credentials
Generated: $(date)
================================================

Web Interface:
  URL      : http://${SERVER_IP}:8000
  Username : admin
  Password : ${ADMIN_PASSWORD}

Database:
  Host     : localhost
  Database : ${DB_NAME}
  Username : ${DB_USER}
  Password : ${DB_PASSWORD}

================================================
⚠ SECURITY WARNING:
  Delete this file after saving the credentials!
  Run: sudo rm ${creds_file}
================================================
EOF
    
    chmod 600 "$creds_file"
    chown root:root "$creds_file"
    
    print_info "Credentials saved to: ${creds_file}"
    print_warning "Delete this file after saving the credentials!"
}

# Main installation
main() {
    print_banner
    
    check_root
    detect_os
    
    echo ""
    print_warning "This script will install GETOLS and its dependencies."
    print_warning "Make sure you have a backup of any existing data."
    echo ""
    read -p "Continue with installation? [y/N] " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo ""
    print_info "Starting installation..."
    echo ""
    
    install_dependencies
    setup_database
    create_user
    install_getols
    create_cli
    init_database
    create_service
    save_credentials
    
    print_completion
}

# Run main
main "$@"
