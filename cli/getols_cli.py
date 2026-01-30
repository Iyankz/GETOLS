#!/usr/bin/env python3
"""
GETOLS CLI Tool
Command-line interface for GETOLS administration.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="GETOLS")
def cli():
    """GETOLS - Gateway for Extended OLT Services CLI"""
    pass


@cli.command()
@click.option("--username", "-u", required=True, help="Username to reset password for")
def reset_password(username: str):
    """Reset a user's password."""
    from app.core.database import SessionLocal
    from app.services.user_service import UserService
    from app.core.security import validate_password_policy
    
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user = user_service.get_by_username(username)
        
        if not user:
            console.print(f"[red]Error:[/red] User '{username}' not found.")
            sys.exit(1)
        
        console.print(f"\nResetting password for user: [cyan]{username}[/cyan]")
        console.print(f"Role: [yellow]{user.role.value}[/yellow]\n")
        
        # Get new password
        while True:
            new_password = Prompt.ask("Enter new password", password=True)
            confirm_password = Prompt.ask("Confirm new password", password=True)
            
            if new_password != confirm_password:
                console.print("[red]Passwords do not match. Try again.[/red]\n")
                continue
            
            is_valid, error = validate_password_policy(new_password)
            if not is_valid:
                console.print(f"[red]{error}[/red]\n")
                continue
            
            break
        
        # Reset password
        success, error = user_service.reset_password(user.id, new_password)
        
        if success:
            console.print(f"\n[green]✓ Password reset successfully for {username}[/green]")
            console.print("[yellow]Note: User will be required to change password on next login.[/yellow]")
        else:
            console.print(f"\n[red]Error: {error}[/red]")
            sys.exit(1)
            
    finally:
        db.close()


@cli.command()
def list_users():
    """List all users."""
    from app.core.database import SessionLocal
    from app.services.user_service import UserService
    
    db = SessionLocal()
    try:
        user_service = UserService(db)
        users = user_service.get_all()
        
        if not users:
            console.print("[yellow]No users found.[/yellow]")
            return
        
        table = Table(title="GETOLS Users")
        table.add_column("ID", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("Role", style="yellow")
        table.add_column("Active", style="blue")
        table.add_column("Must Change Password", style="magenta")
        table.add_column("Last Login")
        
        for user in users:
            table.add_row(
                str(user.id),
                user.username,
                user.role.value,
                "Yes" if user.is_active else "No",
                "Yes" if user.must_change_password else "No",
                str(user.last_login) if user.last_login else "Never",
            )
        
        console.print(table)
        
    finally:
        db.close()


@cli.command()
def list_olts():
    """List all OLTs."""
    from app.core.database import SessionLocal
    from app.services.olt_service import OLTService
    
    db = SessionLocal()
    try:
        olt_service = OLTService(db)
        olts = olt_service.get_all()
        
        if not olts:
            console.print("[yellow]No OLTs configured.[/yellow]")
            return
        
        table = Table(title="GETOLS OLTs")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("IP Address", style="blue")
        table.add_column("Connection", style="magenta")
        table.add_column("Enabled")
        
        for olt in olts:
            table.add_row(
                str(olt.id),
                olt.name,
                olt.type_display,
                olt.ip_address,
                olt.connection_type.value.upper(),
                "[green]Yes[/green]" if olt.is_enabled else "[red]No[/red]",
            )
        
        console.print(table)
        
    finally:
        db.close()


@cli.command()
def create_admin():
    """Create a new admin user."""
    from app.core.database import SessionLocal
    from app.services.user_service import UserService
    from app.models.user import UserRole
    from app.core.security import validate_password_policy
    
    db = SessionLocal()
    try:
        user_service = UserService(db)
        
        console.print("\n[cyan]Create New Admin User[/cyan]\n")
        
        # Get username
        while True:
            username = Prompt.ask("Username")
            if user_service.get_by_username(username):
                console.print("[red]Username already exists. Try another.[/red]\n")
                continue
            break
        
        # Get password
        while True:
            password = Prompt.ask("Password", password=True)
            confirm = Prompt.ask("Confirm password", password=True)
            
            if password != confirm:
                console.print("[red]Passwords do not match.[/red]\n")
                continue
            
            is_valid, error = validate_password_policy(password)
            if not is_valid:
                console.print(f"[red]{error}[/red]\n")
                continue
            
            break
        
        # Optional fields
        email = Prompt.ask("Email (optional)", default="")
        full_name = Prompt.ask("Full name (optional)", default="")
        
        # Create user
        user, error = user_service.create(
            username=username,
            password=password,
            role=UserRole.ADMIN,
            email=email if email else None,
            full_name=full_name if full_name else None,
            must_change_password=False,
        )
        
        if user:
            console.print(f"\n[green]✓ Admin user '{username}' created successfully![/green]")
        else:
            console.print(f"\n[red]Error: {error}[/red]")
            sys.exit(1)
            
    finally:
        db.close()


@cli.command()
def db_init():
    """Initialize database tables."""
    from app.core.database import engine, Base
    from app.models import *  # noqa - Import all models
    
    console.print("[cyan]Initializing database...[/cyan]")
    
    Base.metadata.create_all(bind=engine)
    
    console.print("[green]✓ Database tables created successfully![/green]")


@cli.command()
def cleanup_sessions():
    """Cleanup expired sessions."""
    from app.core.database import SessionLocal
    from app.services.auth_service import AuthService
    
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        deleted = auth_service.cleanup_expired_sessions()
        
        console.print(f"[green]✓ Cleaned up {deleted} expired sessions.[/green]")
        
    finally:
        db.close()


@cli.command()
@click.option("--days", "-d", default=90, help="Delete logs older than this many days")
@click.confirmation_option(prompt="Are you sure you want to delete old activity logs?")
def cleanup_logs(days: int):
    """Cleanup old activity logs."""
    from app.core.database import SessionLocal
    from app.services.activity_service import ActivityService
    
    db = SessionLocal()
    try:
        activity_service = ActivityService(db)
        deleted = activity_service.cleanup_old_logs(days)
        
        console.print(f"[green]✓ Deleted {deleted} activity logs older than {days} days.[/green]")
        
    finally:
        db.close()


@cli.command()
def version():
    """Show GETOLS version information."""
    console.print("\n[cyan]GETOLS - Gateway for Extended OLT Services[/cyan]")
    console.print("Version: [green]1.0.0[/green]")
    console.print("Release: Initial Stable Release")
    console.print("\nSupported OLT Models:")
    console.print("  • ZTE ZXA10 C300 (GPON)")
    console.print("  • ZTE ZXA10 C320 (GPON)")
    console.print("\n[dim]Built with ❤️ & ☕ by Iyankz and Brother[/dim]")
    console.print("[dim]https://Iyankz.github.io[/dim]\n")


if __name__ == "__main__":
    cli()
