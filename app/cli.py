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
@click.argument('recipient', required=False)
@with_appcontext
def test_email_command(recipient):
    """Test email configuration by sending a test email.

    Usage:
        flask test-email recipient@example.com
    """
    from flask import current_app
    from flask_mailman import EmailMessage
    from app import mail

    # Display current email configuration (without exposing password)
    click.echo('\nEmail Configuration:')
    click.echo(f'  Server: {current_app.config.get("MAIL_SERVER")}:{current_app.config.get("MAIL_PORT")}')
    click.echo(f'  TLS: {"Enabled" if current_app.config.get("MAIL_USE_TLS") else "Disabled"}')
    click.echo(f'  SSL: {"Enabled" if current_app.config.get("MAIL_USE_SSL") else "Disabled"}')

    username = current_app.config.get('MAIL_USERNAME')
    if username:
        click.echo(f'  Username: {username}')
    else:
        click.echo(f'  Username: Not configured')

    click.echo(f'  Default Sender: {current_app.config.get("MAIL_DEFAULT_SENDER")}')
    click.echo('')

    # Check if email is configured
    if not username or not current_app.config.get('MAIL_PASSWORD'):
        click.echo('⚠ Email is not configured')
        click.echo('  Set MAIL_USERNAME and MAIL_PASSWORD in your .env file to enable email notifications.')
        click.echo('  See docs/EMAIL_SETUP.md for instructions on setting up Gmail App Password.')
        return

    # Prompt for recipient if not provided
    if not recipient:
        recipient = click.prompt('Recipient email address')

    # Send test email
    try:
        msg = EmailMessage(
            subject='Tennis Club - Email Configuration Test',
            to=[recipient],
            body='''Hallo,

dies ist eine Test-E-Mail vom Tennisclub-Reservierungssystem.

Wenn du diese E-Mail erhältst, funktioniert die E-Mail-Konfiguration korrekt.

SMTP Server: {server}:{port}
TLS: {tls}
From: {sender}

Weitere Informationen zur E-Mail-Konfiguration findest du in docs/EMAIL_SETUP.md

Viele Grüße
Dein TCZ-Team
'''.format(
                server=current_app.config.get('MAIL_SERVER'),
                port=current_app.config.get('MAIL_PORT'),
                tls='Aktiviert' if current_app.config.get('MAIL_USE_TLS') else 'Deaktiviert',
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
        )

        msg.send()

        click.echo('✓ Email configuration test successful!')
        click.echo(f'  Test email sent to: {recipient}')
        click.echo('  Check your inbox to confirm receipt.')
        click.echo('')

    except Exception as e:
        click.echo(f'✗ Failed to send test email')
        click.echo(f'  Error: {str(e)}')
        click.echo('')
        click.echo('Troubleshooting tips:')
        click.echo('  1. Verify you are using a Gmail App Password (not your account password)')
        click.echo('  2. Check that MAIL_USERNAME and MAIL_PASSWORD are correct in .env')
        click.echo('  3. Ensure 2-Step Verification is enabled on your Gmail account')
        click.echo('  4. See docs/EMAIL_SETUP.md for detailed setup instructions')
        click.echo('')


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


@click.command('reset-payment-status')
@click.option('--confirm', is_flag=True, help='Confirm reset without prompt')
@click.option('--force', is_flag=True, help='Force reset even if already done this year')
@with_appcontext
def reset_payment_status_command(confirm, force):
    """Reset all members' payment status to unpaid.

    This command is intended to be run on January 1st each year,
    either manually or via a cron job.

    Example cron entry (run at midnight on Jan 1st):
        0 0 1 1 * cd /path/to/tcz && flask reset-payment-status --confirm
    """
    from datetime import date
    from flask import current_app
    from app.services.member_service import MemberService

    today = date.today()

    # Check if we should run (only on January 1st unless forced)
    if not force and (today.day != 1 or today.month != 1):
        click.echo(f'Payment reset should only run on January 1st.')
        click.echo(f'Today is {today.strftime("%d.%m.%Y")}.')
        click.echo('Use --force to run anyway.')
        return

    # Count members with paid status
    paid_count = Member.query.filter_by(fee_paid=True).count()
    total_count = Member.query.filter_by(is_active=True).count()

    if paid_count == 0:
        click.echo('No members have paid status to reset.')
        return

    click.echo(f'Found {paid_count} members with paid status (out of {total_count} active members).')

    if not confirm:
        if not click.confirm('Are you sure you want to reset all payment statuses to unpaid?'):
            click.echo('Reset cancelled.')
            return

    try:
        reset_count, error = MemberService.reset_all_payment_status()

        if error:
            click.echo(f'✗ Failed to reset payment status: {error}')
            return

        click.echo(f'✓ Reset payment status for {reset_count} members.')
        click.echo(f'  All members now have fee_paid=False')

    except Exception as e:
        click.echo(f'✗ Failed to reset payment status: {str(e)}')


def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(init_courts_command)
    app.cli.add_command(test_email_command)
    app.cli.add_command(delete_reservations_command)
    app.cli.add_command(reset_payment_status_command)
