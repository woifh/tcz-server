"""Flask CLI commands for Tennis Club Reservation System."""
import click
from flask.cli import with_appcontext


@click.command('create-admin')
@click.option('--name', prompt='Admin name', help='Administrator name')
@click.option('--email', prompt='Admin email', help='Administrator email')
@click.option('--password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='Administrator password')
@with_appcontext
def create_admin_command(name, email, password):
    """Create an administrator account - to be implemented."""
    click.echo(f'Creating admin user: {name} ({email})')
    click.echo('This command will be implemented in task 6.')


@click.command('init-courts')
@with_appcontext
def init_courts_command():
    """Initialize 6 tennis courts - to be implemented."""
    click.echo('Initializing 6 tennis courts...')
    click.echo('This command will be implemented in task 2.')


@click.command('test-email')
@click.option('--to', prompt='Recipient email', help='Test email recipient')
@with_appcontext
def test_email_command(to):
    """Test email configuration - to be implemented."""
    click.echo(f'Sending test email to: {to}')
    click.echo('This command will be implemented in task 4.')


def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(init_courts_command)
    app.cli.add_command(test_email_command)
