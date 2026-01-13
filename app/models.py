"""Database models for Tennis Club Reservation System."""
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


# Association table for many-to-many self-referential favourites relationship
favourites = db.Table('favourite',
    db.Column('member_id', db.String(36), db.ForeignKey('member.id'), primary_key=True),
    db.Column('favourite_id', db.String(36), db.ForeignKey('member.id'), primary_key=True),
    db.CheckConstraint('member_id != favourite_id', name='check_not_self_favourite')
)


class Member(db.Model, UserMixin):
    """Member model representing club members with authentication."""

    __tablename__ = 'member'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    deactivated_by_id = db.Column(db.String(36), db.ForeignKey('member.id'), nullable=True)

    # Membership type: 'full' (can reserve courts) or 'sustaining' (no access to booking system)
    membership_type = db.Column(db.String(20), nullable=False, default='full')
    # Annual fee payment tracking
    fee_paid = db.Column(db.Boolean, nullable=False, default=False)
    fee_paid_date = db.Column(db.Date, nullable=True)
    fee_paid_by_id = db.Column(db.String(36), db.ForeignKey('member.id'), nullable=True)

    # Address fields
    street = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    # Contact
    phone = db.Column(db.String(20), nullable=True)

    # Notification preferences (email)
    notifications_enabled = db.Column(db.Boolean, nullable=False, default=True)
    notify_own_bookings = db.Column(db.Boolean, nullable=False, default=True)
    notify_other_bookings = db.Column(db.Boolean, nullable=False, default=True)
    notify_court_blocked = db.Column(db.Boolean, nullable=False, default=True)
    notify_booking_overridden = db.Column(db.Boolean, nullable=False, default=True)
    
    @property
    def name(self):
        """Return full name for backward compatibility."""
        return f"{self.firstname} {self.lastname}"
    
    # Relationships
    reservations_made = db.relationship('Reservation', 
                                       foreign_keys='Reservation.booked_by_id',
                                       backref='booked_by', 
                                       lazy='dynamic',
                                       cascade='all, delete-orphan')
    
    reservations_for = db.relationship('Reservation',
                                      foreign_keys='Reservation.booked_for_id',
                                      backref='booked_for',
                                      lazy='dynamic',
                                      cascade='all, delete-orphan')
    
    favourites = db.relationship('Member',
                                secondary=favourites,
                                primaryjoin=(favourites.c.member_id == id),
                                secondaryjoin=(favourites.c.favourite_id == id),
                                backref=db.backref('favourited_by', lazy='dynamic'),
                                lazy='dynamic')
    
    notifications = db.relationship('Notification',
                                   backref='recipient',
                                   lazy='dynamic',
                                   cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if the member has administrator role."""
        return self.role == 'administrator'

    def is_teamster(self):
        """Check if the member has teamster role."""
        from app.constants import UserRole
        return self.role == UserRole.TEAMSTER

    def is_teamster_or_admin(self):
        """Check if the member has teamster or administrator role."""
        from app.constants import UserRole
        return self.role in [UserRole.TEAMSTER, UserRole.ADMINISTRATOR]

    def can_manage_blocks(self):
        """Check if the member can manage court blocks (teamster or admin)."""
        return self.is_teamster_or_admin()

    def can_edit_block(self, block):
        """
        Check if the member can edit a specific block.

        Admins can edit any block.
        Teamsters can only edit blocks they created.
        Regular members cannot edit blocks.
        """
        if self.is_admin():
            return True
        if self.is_teamster():
            return block.created_by_id == self.id
        return False

    def is_full_member(self):
        """Check if the member has full membership (can reserve courts)."""
        return self.membership_type == 'full'

    def is_sustaining_member(self):
        """Check if the member has sustaining membership (no access to booking system)."""
        return self.membership_type == 'sustaining'

    def can_reserve_courts(self):
        """Check if the member is allowed to make court reservations."""
        return self.is_active and self.is_full_member()

    def has_unpaid_fee(self):
        """Check if the member has an unpaid membership fee."""
        return not self.fee_paid

    def is_payment_restricted(self):
        """Check if member is restricted from booking due to unpaid fee past deadline."""
        if self.fee_paid:
            return False  # Paid members are never restricted
        from app.services.settings_service import SettingsService
        return SettingsService.is_past_payment_deadline()

    def __repr__(self):
        return f'<Member {self.name} ({self.email})>'



class Court(db.Model):
    """Court model representing tennis courts."""
    
    __tablename__ = 'court'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    
    # Relationships
    reservations = db.relationship('Reservation',
                                  backref='court',
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')
    
    blocks = db.relationship('Block',
                           backref='court',
                           lazy='dynamic',
                           cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """Initialize court with validation."""
        super(Court, self).__init__(**kwargs)
        if self.number is not None and (self.number < 1 or self.number > 6):
            raise ValueError("Court number must be between 1 and 6")
    
    def __repr__(self):
        return f'<Court {self.number}>'



class Reservation(db.Model):
    """Reservation model representing court bookings.
    
    Note: The unique constraint on (court_id, date, start_time) is implemented
    as a partial unique index (unique_active_booking) that only applies to 
    active reservations. This allows cancelled reservations to exist without
    blocking new bookings for the same slot.
    
    The is_short_notice field indicates if the booking was made within 15 minutes
    of the slot start time. Short notice bookings don't count toward the member's
    2-reservation limit and cannot be cancelled.
    """
    
    __tablename__ = 'reservation'
    __table_args__ = (
        # Note: unique_booking constraint removed in favor of partial index
        # See migration for unique_active_booking partial index
        db.Index('idx_reservation_date', 'date'),
        db.Index('idx_reservation_booked_for', 'booked_for_id'),
        db.Index('idx_reservation_booked_by', 'booked_by_id'),
        db.Index('idx_reservation_short_notice', 'is_short_notice'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    booked_for_id = db.Column(db.String(36), db.ForeignKey('member.id', ondelete='CASCADE'), nullable=False)
    booked_by_id = db.Column(db.String(36), db.ForeignKey('member.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_short_notice = db.Column(db.Boolean, nullable=False, default=False)
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Reservation Court {self.court_id} on {self.date} at {self.start_time}>'



class BlockReason(db.Model):
    """BlockReason model for customizable block reasons."""

    __tablename__ = 'block_reason'
    __table_args__ = (
        db.Index('idx_block_reason_name', 'name'),
        db.Index('idx_block_reason_active', 'is_active'),
        db.Index('idx_block_reason_teamster_usable', 'teamster_usable'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    teamster_usable = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.String(36), db.ForeignKey('member.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    created_by = db.relationship('Member', backref='block_reasons_created')
    blocks = db.relationship('Block', backref='reason_obj', lazy='dynamic')

    def to_dict(self):
        """Convert reason to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
            'teamster_usable': self.teamster_usable,
            'created_by': self.created_by.name,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<BlockReason {self.name}>'

class BlockAuditLog(db.Model):
    """BlockAuditLog model for tracking block operations."""
    
    __tablename__ = 'block_audit_log'
    __table_args__ = (
        db.Index('idx_block_audit_timestamp', 'timestamp'),
        db.Index('idx_block_audit_admin', 'admin_id'),
        db.Index('idx_block_audit_operation', 'operation'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(20), nullable=False)  # 'create', 'update', 'delete'
    block_id = db.Column(db.Integer, nullable=True)  # for single block operations
    operation_data = db.Column(db.JSON, nullable=True)  # JSON data about the operation
    admin_id = db.Column(db.String(36), db.ForeignKey('member.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    admin = db.relationship('Member', backref='block_audit_logs')
    
    def __init__(self, **kwargs):
        """Initialize audit log with validation."""
        super(BlockAuditLog, self).__init__(**kwargs)
        valid_operations = ['create', 'update', 'delete']
        if self.operation and self.operation not in valid_operations:
            raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")
    
    def __repr__(self):
        return f'<BlockAuditLog {self.operation} by {self.admin_id}>'


class MemberAuditLog(db.Model):
    """MemberAuditLog model for tracking member operations."""

    __tablename__ = 'member_audit_log'
    __table_args__ = (
        db.Index('idx_member_audit_timestamp', 'timestamp'),
        db.Index('idx_member_audit_admin', 'performed_by_id'),
        db.Index('idx_member_audit_operation', 'operation'),
        db.Index('idx_member_audit_member', 'member_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(36), nullable=False)  # Not FK because member might be deleted
    operation = db.Column(db.String(20), nullable=False)  # 'create', 'update', 'delete', 'role_change', 'deactivate', 'reactivate'
    operation_data = db.Column(db.JSON, nullable=True)  # JSON data about the operation
    performed_by_id = db.Column(db.String(36), db.ForeignKey('member.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    performed_by = db.relationship('Member', backref='member_audit_logs')

    def __init__(self, **kwargs):
        """Initialize audit log with validation."""
        super(MemberAuditLog, self).__init__(**kwargs)
        valid_operations = ['create', 'update', 'delete', 'role_change', 'deactivate', 'reactivate', 'membership_change', 'payment_update']
        if self.operation and self.operation not in valid_operations:
            raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")

    def __repr__(self):
        return f'<MemberAuditLog {self.operation} on member {self.member_id} by {self.performed_by_id}>'


class ReasonAuditLog(db.Model):
    """ReasonAuditLog model for tracking block reason operations."""

    __tablename__ = 'reason_audit_log'
    __table_args__ = (
        db.Index('idx_reason_audit_timestamp', 'timestamp'),
        db.Index('idx_reason_audit_admin', 'performed_by_id'),
        db.Index('idx_reason_audit_operation', 'operation'),
        db.Index('idx_reason_audit_reason', 'reason_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    reason_id = db.Column(db.Integer, nullable=False)  # Not FK because reason might be deleted
    operation = db.Column(db.String(20), nullable=False)  # 'create', 'update', 'delete', 'deactivate'
    operation_data = db.Column(db.JSON, nullable=True)  # JSON data about the operation
    performed_by_id = db.Column(db.String(36), db.ForeignKey('member.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    performed_by = db.relationship('Member', backref='reason_audit_logs')

    def __init__(self, **kwargs):
        """Initialize audit log with validation."""
        super(ReasonAuditLog, self).__init__(**kwargs)
        valid_operations = ['create', 'update', 'delete', 'deactivate']
        if self.operation and self.operation not in valid_operations:
            raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")

    def __repr__(self):
        return f'<ReasonAuditLog {self.operation} on reason {self.reason_id} by {self.performed_by_id}>'


class Block(db.Model):
    """Block model representing court availability blocks."""
    
    __tablename__ = 'block'
    __table_args__ = (
        db.Index('idx_block_date', 'date'),
        db.Index('idx_block_court_date', 'court_id', 'date'),
        db.Index('idx_block_reason', 'reason_id'),
        db.Index('idx_block_batch', 'batch_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason_id = db.Column(db.Integer, db.ForeignKey('block_reason.id'), nullable=False)
    details = db.Column(db.String(255), nullable=True)
    batch_id = db.Column(db.String(36), nullable=True, index=True)  # UUID for grouping multi-court blocks
    is_modified = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.String(36), db.ForeignKey('member.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    created_by = db.relationship('Member', backref='blocks_created')
    
    # Legacy property for backward compatibility
    @property
    def reason(self):
        """Return reason name for backward compatibility."""
        return self.reason_obj.name if self.reason_obj else None
    
    def __repr__(self):
        return f'<Block Court {self.court_id} on {self.date} ({self.reason})>'



class Notification(db.Model):
    """Notification model for member notifications."""

    __tablename__ = 'notification'
    __table_args__ = (
        db.Index('idx_notification_recipient', 'recipient_id'),
        db.Index('idx_notification_timestamp', 'timestamp'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.String(36), db.ForeignKey('member.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'<Notification {self.type} for Member {self.recipient_id}>'


class SystemSetting(db.Model):
    """SystemSetting model for storing application-wide settings."""

    __tablename__ = 'system_setting'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SystemSetting {self.key}={self.value}>'
