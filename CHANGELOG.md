# Changelog

All notable changes to this project will be documented in this file.

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
