"""Database models for Tennis Club Reservation System."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


# Association table for many-to-many self-referential favourites relationship
favourites = db.Table('favourite',
    db.Column('member_id', db.Integer, db.ForeignKey('member.id'), primary_key=True),
    db.Column('favourite_id', db.Integer, db.ForeignKey('member.id'), primary_key=True),
    db.CheckConstraint('member_id != favourite_id', name='check_not_self_favourite')
)


class Member(db.Model, UserMixin):
    """Member model representing club members with authentication."""
    
    __tablename__ = 'member'
    
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
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
    booked_for_id = db.Column(db.Integer, db.ForeignKey('member.id', ondelete='CASCADE'), nullable=False)
    booked_by_id = db.Column(db.Integer, db.ForeignKey('member.id', ondelete='CASCADE'), nullable=False)
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
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('Member', backref='block_reasons_created')
    blocks = db.relationship('Block', backref='reason_obj', lazy='dynamic')
    templates = db.relationship('BlockTemplate', backref='reason_obj', lazy='dynamic')
    sub_reason_templates = db.relationship('SubReasonTemplate', backref='reason_obj', lazy='dynamic')
    
    def __repr__(self):
        return f'<BlockReason {self.name}>'


class BlockSeries(db.Model):
    """BlockSeries model for recurring block patterns."""
    
    __tablename__ = 'block_series'
    __table_args__ = (
        db.Index('idx_block_series_dates', 'start_date', 'end_date'),
        db.Index('idx_block_series_reason', 'reason_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    recurrence_pattern = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    recurrence_days = db.Column(db.JSON, nullable=True)  # JSON array for weekly pattern
    reason_id = db.Column(db.Integer, db.ForeignKey('block_reason.id'), nullable=False)
    sub_reason = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    blocks = db.relationship('Block', backref='series', lazy='dynamic')
    reason = db.relationship('BlockReason', backref='series_list')
    created_by = db.relationship('Member', backref='block_series_created')
    
    def __init__(self, **kwargs):
        """Initialize block series with validation."""
        super(BlockSeries, self).__init__(**kwargs)
        valid_patterns = ['daily', 'weekly', 'monthly']
        if self.recurrence_pattern and self.recurrence_pattern not in valid_patterns:
            raise ValueError(f"Recurrence pattern must be one of: {', '.join(valid_patterns)}")
    
    def __repr__(self):
        return f'<BlockSeries {self.name} ({self.recurrence_pattern})>'


class SubReasonTemplate(db.Model):
    """SubReasonTemplate model for predefined sub-reason options."""
    
    __tablename__ = 'sub_reason_template'
    __table_args__ = (
        db.Index('idx_sub_reason_template_reason', 'reason_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    reason_id = db.Column(db.Integer, db.ForeignKey('block_reason.id', ondelete='CASCADE'), nullable=False)
    template_name = db.Column(db.String(100), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('Member', backref='sub_reason_templates_created')
    
    def __repr__(self):
        return f'<SubReasonTemplate {self.template_name}>'


class BlockTemplate(db.Model):
    """BlockTemplate model for reusable block configurations."""
    
    __tablename__ = 'block_template'
    __table_args__ = (
        db.Index('idx_block_template_name', 'name'),
        db.Index('idx_block_template_reason', 'reason_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    court_selection = db.Column(db.JSON, nullable=False)  # JSON array of court IDs
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason_id = db.Column(db.Integer, db.ForeignKey('block_reason.id'), nullable=False)
    sub_reason = db.Column(db.String(255), nullable=True)
    recurrence_pattern = db.Column(db.String(20), nullable=True)  # 'daily', 'weekly', 'monthly', or null
    recurrence_days = db.Column(db.JSON, nullable=True)  # JSON array for weekly pattern
    created_by_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('Member', backref='block_templates_created')
    
    def __init__(self, **kwargs):
        """Initialize block template with validation."""
        super(BlockTemplate, self).__init__(**kwargs)
        if self.recurrence_pattern:
            valid_patterns = ['daily', 'weekly', 'monthly']
            if self.recurrence_pattern not in valid_patterns:
                raise ValueError(f"Recurrence pattern must be one of: {', '.join(valid_patterns)}")
    
    def __repr__(self):
        return f'<BlockTemplate {self.name}>'


class BlockAuditLog(db.Model):
    """BlockAuditLog model for tracking block operations."""
    
    __tablename__ = 'block_audit_log'
    __table_args__ = (
        db.Index('idx_block_audit_timestamp', 'timestamp'),
        db.Index('idx_block_audit_admin', 'admin_id'),
        db.Index('idx_block_audit_operation', 'operation'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(20), nullable=False)  # 'create', 'update', 'delete', 'bulk_delete'
    block_id = db.Column(db.Integer, nullable=True)  # for single block operations
    series_id = db.Column(db.Integer, nullable=True)  # for series operations
    operation_data = db.Column(db.JSON, nullable=True)  # JSON data about the operation
    admin_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('Member', backref='block_audit_logs')
    
    def __init__(self, **kwargs):
        """Initialize audit log with validation."""
        super(BlockAuditLog, self).__init__(**kwargs)
        valid_operations = ['create', 'update', 'delete', 'bulk_delete']
        if self.operation and self.operation not in valid_operations:
            raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")
    
    def __repr__(self):
        return f'<BlockAuditLog {self.operation} by {self.admin_id}>'


class Block(db.Model):
    """Block model representing court availability blocks."""
    
    __tablename__ = 'block'
    __table_args__ = (
        db.Index('idx_block_date', 'date'),
        db.Index('idx_block_court_date', 'court_id', 'date'),
        db.Index('idx_block_series', 'series_id'),
        db.Index('idx_block_reason', 'reason_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason_id = db.Column(db.Integer, db.ForeignKey('block_reason.id'), nullable=False)
    sub_reason = db.Column(db.String(255), nullable=True)
    series_id = db.Column(db.Integer, db.ForeignKey('block_series.id', ondelete='CASCADE'), nullable=True)
    is_modified = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
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
    recipient_id = db.Column(db.Integer, db.ForeignKey('member.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read = db.Column(db.Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f'<Notification {self.type} for Member {self.recipient_id}>'
