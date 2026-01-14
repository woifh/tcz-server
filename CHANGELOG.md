# Changelog

All notable changes to this project will be documented in this file.

## [3.7.0] - 2026-01-14

### Performance
- Court availability overview loads significantly faster (up to 95% less data transfer)

### Fixed
- Court number now displays correctly in the active reservations list ("Platz 1" instead of "Platz undefined")

## [3.6.0] - 2026-01-14

### Fixed
- Block edit: updated blocks no longer disappear when date is changed beyond original 30-day view range
- Admin endpoints now use session-only authentication (not accessible via mobile JWT)
- Block reason create/update/delete operations now properly logged in audit log
- Member notification preferences now included in API responses for proper form population
- Notification settings now properly saved when creating new members (previously ignored and defaulted to true)

### Improved
- Audit log now shows full details for block operations (date, time, courts, reason)
- Block batch updates now log single entry per batch instead of individual entries per court
- Member updates now correctly track only actual changes (fixed false change detection for notification settings)
- Removed redundant "Ausgeführt als: Administrator" from audit log

## [3.5.0] - 2026-01-14

### Added
- Complete mobile API for reservations, members, and admin features

## [3.4.0] - 2026-01-14

### Added
- Mobile app login support

## [3.3.0] - 2026-01-13

### Performance
- Flicker-free date navigation in court grid (static table structure)
- Server-side pre-computation of slot styles and content
- Smooth CSS transitions on slot state changes

## [3.2.0] - 2026-01-13

### Security
- Added CSRF protection for all form submissions and API requests

## [3.1.1] - 2026-01-13

### Fixed
- Booking form validation failed due to UUID parsing issue

### Improved
- Notification settings now available when creating new members (not just editing)
- Email validation required before enabling notifications
- Sub-options are visually unchecked when master notification toggle is disabled
- Improved spacing in notification settings section
- Added "Back to overview" link on login page for easier navigation

### Performance
- Faster loading of members list and court availability pages

## [3.1.0] - 2026-01-13

### Added
- Member profile page for editing personal information
- Email notification preferences - members can control which notifications they receive:
  - Master toggle to enable/disable all notifications
  - Own bookings (create/cancel)
  - Bookings by other members
  - Court blocking notifications
  - Booking override notifications
- Admin can now edit member notification preferences

### Technical
- Member IDs changed from integer to UUID for better security
- Profile and admin member edit pages now fetch data via API
- Email service respects member notification preferences before sending

## [3.0.2] - 2026-01-11

### Improved
- Simplified navigation for anonymous users - login link now directly visible instead of hamburger menu

## [3.0.1] - 2026-01-09

### Improved
- Smoother UI when creating or cancelling bookings - table no longer flickers

### Technical
- Partial slot updates instead of full table reload after booking changes

## [3.0.0] - 2026-01-09

### Performance
- Significantly improved booking performance with optimized database queries
- Reduced database queries per booking from ~10 to ~7 using eager loading
- Added request-scoped caching for system settings
- Emails are now sent asynchronously in background threads for faster API responses

### Technical
- SQLAlchemy eager loading with `joinedload` for reservation relationships
- Member object passed through validation to avoid redundant lookups
- Settings cache using Flask's `g` object for request-scoped storage

## [2.2.5] - 2026-01-09

### Improved
- Court slots now show only the member name for own bookings instead of redundant "Name (von Name)"

## [2.2.4] - 2026-01-09

### Fixed
- Supporting members are no longer visible in member search or favorites for booking

## [2.2.3] - 2026-01-09

### Added
- New "Bookings for others" section on dashboard and reservations page
- Bookings made for other members are now displayed separately from your own bookings

### Fixed
- Booking limit validation now correctly excludes bookings made for others

## [2.2.2] - 2026-01-09

### Fixed
- When a member creates a booking for another member, it no longer counts toward their own booking limit

## [2.2.1] - 2026-01-09

### Fixed
- Dashboard now loads court availability only once instead of twice

## [2.2.0] - 2026-01-07

### Added
- Unified activity log for blocks, members, and blocking reasons
- Filter options in activity log (All/Blocks/Members/Blocking Reasons)
- Tracking of changes to blocking reasons

### Improved
- Cleaner member list without email column
- Consistent icons for edit, delete, and cancel actions
- Better activity log display

## [2.1.0] - 2026-01-07

### Fixed
- Member search in booking dialog now works in production

## [2.0.0] - 2026-01-07

### Added
- Version history with dedicated page in admin area
- Clickable version display in admin panel

### Fixed
- Version display now shows the correct version

## [1.0.0] - 2026-01-07

### Added
- Member search in booking dialog with automatic favorites
- Bulk import of members via CSV file
- Password confirmation during registration
- Address information in member management
- Payment reminder for members
- Filter in member management with booking count

### Improved
- Extended and improved member management
- Consistent "Team Leader" terminology in the interface
- Blocking reasons management extended for team leaders
- Better mobile navigation
- Navigation adjusted for team leader role

### Fixed
- Timezone display corrected
