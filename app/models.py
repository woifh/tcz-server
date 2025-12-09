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



class Block(db.Model):
    """Block model representing court availability blocks."""
    
    __tablename__ = 'block'
    __table_args__ = (
        db.Index('idx_block_date', 'date'),
        db.Index('idx_block_court_date', 'court_id', 'date'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('Member', backref='blocks_created')
    
    def __init__(self, **kwargs):
        """Initialize block with validation."""
        super(Block, self).__init__(**kwargs)
        valid_reasons = ['rain', 'maintenance', 'tournament', 'championship']
        if self.reason and self.reason not in valid_reasons:
            raise ValueError(f"Block reason must be one of: {', '.join(valid_reasons)}")
    
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
