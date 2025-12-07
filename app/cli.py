"""Flask CLI commands for Tennis Club Reservation System."""
import click
from flask.cli import with_appcontext
from app import db
from app.models import Member, Court, Reservation


@click.command('create-admin')
@click.option('--firstname', prompt='Admin first name', help='Administrator first name')
@click.option('--lastname', prompt='Admin last name', help='Administrator last name')
@click.option('--email', prompt='Admin email', help='Administrator email')
@click.option('--password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='Administrator password')
@with_appcontext
def create_admin_command(firstname, lastname, email, password):
    """Create an administrator account."""
    # Check if admin already exists
    existing = Member.query.filter_by(email=email).first()
    if existing:
        click.echo(f'Error: User with email {email} already exists.')
        return
    
    # Create admin user
    admin = Member(firstname=firstname, lastname=lastname, email=email, role='administrator')
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'✓ Admin user created: {firstname} {lastname} ({email})')


@click.command('init-courts')
@with_appcontext
def init_courts_command():
    """Initialize 6 tennis courts."""
    # Check if courts already exist
    existing_count = Court.query.count()
    if existing_count > 0:
        click.echo(f'Courts already initialized ({existing_count} courts exist).')
        return
    
    # Create 6 courts
    for i in range(1, 7):
        court = Court(number=i, status='available')
        db.session.add(court)
    
    db.session.commit()
    click.echo('✓ Initialized 6 tennis courts (1-6)')


@click.command('test-email')
@click.option('--to', prompt='Recipient email', help='Test email recipient')
@with_appcontext
def test_email_command(to):
    """Test email configuration."""
    from flask_mail import Message
    from app import mail
    
    try:
        msg = Message(
            subject='Test Email - Tennis Club',
            recipients=[to],
            body='Dies ist eine Test-E-Mail vom Tennisclub-Reservierungssystem.\n\nWenn Sie diese E-Mail erhalten, funktioniert die E-Mail-Konfiguration korrekt.'
        )
        mail.send(msg)
        click.echo(f'✓ Test email sent to: {to}')
    except Exception as e:
        click.echo(f'✗ Failed to send email: {str(e)}')


@click.command('delete-reservations')
@click.option('--confirm', is_flag=True, help='Confirm deletion without prompt')
@with_appcontext
def delete_reservations_command(confirm):
    """Delete all reservations from the database."""
    count = Reservation.query.count()
    
    if count == 0:
        click.echo('No reservations to delete.')
        return
    
    if not confirm:
        if not click.confirm(f'Are you sure you want to delete all {count} reservations?'):
            click.echo('Deletion cancelled.')
            return
    
    try:
        Reservation.query.delete()
        db.session.commit()
        click.echo(f'✓ Deleted {count} reservations from the database.')
    except Exception as e:
        db.session.rollback()
        click.echo(f'✗ Failed to delete reservations: {str(e)}')


def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(init_courts_command)
    app.cli.add_command(test_email_command)
    app.cli.add_command(delete_reservations_command)
