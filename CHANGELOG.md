# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] - 2026-01-07

### Added
- Unified audit log combining block and member operations
- Filter functionality in audit log (All/Blocks/Members)
- Human-readable audit log details with formatted timestamps and actions

### Changed
- Removed email column from member list view for cleaner layout
- Harmonized action icons (edit/delete/cancel) across all list views using consistent SVG icons
- Harmonized sort icons in blocking reasons list to match member list pattern
- Improved audit log UI with type badges and color-coded action indicators

## [2.1.0] - 2026-01-07

### Fixed
- Member search in booking dialog not showing on production

## [2.0.0] - 2026-01-07

### Added
- Version history (changelog) with dedicated admin page
- Clickable version display in admin panel

### Fixed
- Version calculation now correctly shows tag version

## [1.0.0] - 2026-01-07

### Added
- Member search in booking dialog with auto-favorites
- Member bulk import via CSV file
- Password confirmation field during registration
- Address information in member management
- Payment reminder for members
- Filter in member management with booking count
- Database seeding script for initial data
- Database recreation script

### Changed
- Member management extended and improved
- Team leader terminology unified in UI
- Suspension reasons management extended for team leader usage
- Mobile navigation improved
- Navigation adjusted for team leader role
- Project structure reorganized for better maintainability

### Fixed
- Timezone display corrected
- Version info timezone corrected
