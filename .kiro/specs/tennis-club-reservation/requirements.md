# Requirements Document

## Introduction

This document specifies the requirements for a responsive web application that enables tennis club members to reserve courts online and allows the club board to manage members, reservations, and court availability. The system will be deployed on PythonAnywhere using Flask, MySQL, and Tailwind CSS, with all user-facing content localized in German.

## Glossary

- **System**: The tennis club court reservation web application
- **Member**: A registered club member with login credentials who can make court reservations, identified by firstname, lastname, and email
- **Administrator**: A club board member with elevated privileges to manage members, block courts, and override reservations
- **Court**: One of six clay tennis courts numbered 1 through 6
- **Reservation**: A booking record linking a court, time slot, and member(s)
- **Block**: An administrative restriction preventing court bookings for specified time periods
- **Block Reason**: A customizable category explaining why a court is blocked (e.g., Maintenance, Championship, Tennis Course)
- **Block Sub-reason**: An optional additional detail providing specific information about a block (e.g., "Team A vs Team B" for Championship, "Beginner Course" for Tennis Course)
- **Recurring Block**: A series of blocks that repeat according to a specified pattern (daily, weekly, monthly) with defined start and end dates
- **Block Template**: A saved configuration of block settings that can be reused for creating new blocks
- **Block Series**: A group of related recurring blocks created from a single recurring block definition, where individual instances can be modified independently while maintaining series relationship
- **Booking Slot**: A one-hour time period between 06:00 and 22:00
- **Active Reservation**: A future reservation that has not been cancelled or completed
- **Short Notice Booking**: A reservation created within 15 minutes of the slot start time that does not count toward the member's active reservation limit
- **Favourites List**: A member's curated list of preferred playing partners
- **Booked For**: The member who will use the court
- **Booked By**: The member who created the reservation

## Requirements

### Requirement 1

**User Story:** As a club member, I want to create court reservations for myself or other members, so that I can secure playing time and coordinate with partners.

#### Acceptance Criteria

1. WHEN a member selects an available court and time slot, THE System SHALL create a reservation linking the court, date, time, booked_for member, and booked_by member
2. WHERE a member books for another member, THE System SHALL record both the booked_for member and the booked_by member identities
3. WHEN a member attempts to create a regular reservation, THE System SHALL verify the member has fewer than 2 active regular reservations before allowing the booking
4. WHEN a member creates a reservation, THE System SHALL send email notifications to both the booked_by member and the booked_for member
5. WHEN a member has 2 active regular reservations, THE System SHALL prevent creation of additional regular reservations until one becomes inactive

### Requirement 2

**User Story:** As a club member, I want to view, modify, and cancel my reservations, so that I can adjust my playing schedule as needed.

#### Acceptance Criteria

1. WHEN a member is the booked_for member or the booked_by member, THE System SHALL allow that member to view the reservation details
2. WHEN a member is the booked_for member or the booked_by member, THE System SHALL allow that member to modify the reservation time or court
3. WHEN a member is the booked_for member or the booked_by member AND the current time is more than 15 minutes before the reservation start time, THE System SHALL allow that member to cancel the reservation
4. WHEN the current time is within 15 minutes of the reservation start time OR at or after the reservation start time, THE System SHALL prevent cancellation of the reservation regardless of reservation type
5. WHEN a reservation is modified, THE System SHALL send email notifications to both the booked_by member and the booked_for member
6. WHEN a reservation is cancelled, THE System SHALL send email notifications to both the booked_by member and the booked_for member

### Requirement 3

**User Story:** As a club member, I want to maintain a favourites list of preferred playing partners, so that I can quickly book courts for frequent partners.

#### Acceptance Criteria

1. WHEN a member adds another member to favourites, THE System SHALL store the relationship in the member's favourites list
2. WHEN a member removes a member from favourites, THE System SHALL delete the relationship from the favourites list
3. WHEN a member creates a reservation, THE System SHALL display the member's favourites list in the booked_for dropdown
4. WHEN a member attempts to add themselves to favourites, THE System SHALL reject the operation and display an error message
5. THE System SHALL allow many-to-many relationships in favourites lists where Member A can favourite Member B independently of Member B favouriting Member A
6. WHEN a member creates a reservation, THE System SHALL allow booking for any registered member regardless of favourites list membership

### Requirement 4

**User Story:** As a club member, I want to view court availability in a visual grid, so that I can quickly identify open time slots.

#### Acceptance Criteria

1. WHEN a member views the overview page, THE System SHALL display a grid with rows representing hours from 06:00 to 21:00 and columns representing courts 1 through 6
2. WHEN a time slot is available, THE System SHALL display the cell in green
3. WHEN a time slot has a regular reservation, THE System SHALL display the cell in red with text showing booked_for and booked_by member names
4. WHEN a time slot has a short notice booking, THE System SHALL display the cell in orange with text showing booked_for and booked_by member names
5. WHEN a time slot is blocked, THE System SHALL display the cell in grey
6. WHEN a member clicks an available cell, THE System SHALL open the booking form pre-filled with the selected court, date, and time

### Requirement 5

**User Story:** As an administrator, I want to block courts for maintenance, weather, or events, so that members cannot book unavailable courts.

#### Acceptance Criteria

1. WHEN an administrator creates a block for a court and time period, THE System SHALL prevent members from creating reservations for that court during the blocked period
2. WHEN an administrator blocks a court with existing reservations, THE System SHALL cancel those reservations automatically
3. WHEN a reservation is cancelled due to a block, THE System SHALL send email notifications to the booked_by member and booked_for member including the block reason
4. WHEN an administrator creates a block, THE System SHALL store the court_id, date, start_time, end_time, and reason
5. THE System SHALL support block reasons including rain, maintenance, tournament, and championship

### Requirement 6

**User Story:** As an administrator, I want to manage member accounts, so that I can control system access and maintain accurate member information.

#### Acceptance Criteria

1. WHEN an administrator creates a member account, THE System SHALL store the member firstname, lastname, email, password_hash, and role
2. WHEN an administrator updates a member account, THE System SHALL modify the stored member information
3. WHEN an administrator deletes a member account, THE System SHALL remove the member from the database
4. THE System SHALL support two roles: member and administrator
5. WHEN an administrator views the member list, THE System SHALL display all registered members with their firstname, lastname, email, and role

### Requirement 7

**User Story:** As an administrator, I want to override or delete member reservations, so that I can resolve conflicts and manage court usage.

#### Acceptance Criteria

1. WHEN an administrator deletes a member reservation, THE System SHALL remove the reservation from the database
2. WHEN an administrator deletes a reservation, THE System SHALL send email notifications to the booked_by member and booked_for member
3. WHEN an administrator overrides a reservation, THE System SHALL include the override reason in the notification email

### Requirement 8

**User Story:** As a system user, I want to receive email notifications for all booking events, so that I stay informed about my reservations.

#### Acceptance Criteria

1. WHEN a reservation is created, THE System SHALL send an email to the booked_by member and the booked_for member in German
2. WHEN a reservation is modified, THE System SHALL send an email to the booked_by member and the booked_for member in German
3. WHEN a reservation is cancelled, THE System SHALL send an email to the booked_by member and the booked_for member in German
4. WHEN an administrator cancels a reservation, THE System SHALL include the cancellation reason in the email
5. THE System SHALL use German language for all email subject lines and body content

### Requirement 9

**User Story:** As a system user, I want to access the application on any device, so that I can manage reservations from desktop, tablet, or mobile.

#### Acceptance Criteria

1. WHEN the application is viewed on desktop, THE System SHALL display the complete 6-column by 15-row court grid
2. WHEN the application is viewed on tablet, THE System SHALL display a compressed view with horizontal scrolling
3. WHEN the application is viewed on mobile, THE System SHALL display a vertical list by time with 1-2 courts visible simultaneously
4. THE System SHALL use Tailwind CSS responsive classes for all layout components
5. WHEN touch input is used, THE System SHALL provide buttons and text in sufficient size for touch interaction

### Requirement 10

**User Story:** As a German-speaking user, I want all interface text in German, so that I can use the application in my native language.

#### Acceptance Criteria

1. THE System SHALL display all static interface text in German
2. THE System SHALL display all dynamic messages and notifications in German
3. THE System SHALL use German labels for all form fields and buttons
4. THE System SHALL format dates and times according to German conventions
5. THE System SHALL use German terminology for all court-related concepts

### Requirement 11

**User Story:** As a member, I want the system to prevent booking conflicts, so that I can trust my reservations are valid.

#### Acceptance Criteria

1. WHEN a member attempts to book a time slot that is already reserved, THE System SHALL reject the booking and display an error message
2. WHEN a member attempts to book a blocked time slot, THE System SHALL reject the booking and display an error message
3. WHEN a member attempts to book a regular reservation while having 2 active regular reservations, THE System SHALL reject the booking and display an error message
4. THE System SHALL validate all reservation constraints before persisting to the database
5. THE System SHALL ensure each court has at most one reservation per time slot

### Requirement 12

**User Story:** As a system administrator, I want the application to run reliably on PythonAnywhere, so that members have consistent access.

#### Acceptance Criteria

1. THE System SHALL use Flask as the web framework
2. THE System SHALL use MySQL as the database
3. THE System SHALL use WSGI for application deployment
4. THE System SHALL store database credentials and SMTP settings in environment variables
5. THE System SHALL serve static files from configured static file paths

### Requirement 13

**User Story:** As a member, I want to authenticate securely, so that my account and reservations are protected.

#### Acceptance Criteria

1. WHEN a member logs in with valid credentials, THE System SHALL create an authenticated session
2. WHEN a member logs in with invalid credentials, THE System SHALL reject the login and display an error message
3. THE System SHALL store passwords as hashed values using a secure hashing algorithm
4. WHEN a member logs out, THE System SHALL terminate the authenticated session
5. THE System SHALL restrict access to reservation and member management features to authenticated users
6. WHEN a member creates a password, THE System SHALL require a minimum length of 8 characters

### Requirement 14

**User Story:** As a member, I want reservations to be limited to one-hour slots during operating hours, so that court access is fairly distributed.

#### Acceptance Criteria

1. THE System SHALL allow reservations only for time slots between 06:00 and 21:00
2. THE System SHALL enforce one-hour duration for all reservations
3. WHEN a member attempts to book outside operating hours, THE System SHALL reject the booking
4. THE System SHALL define booking slots at hourly intervals: 06:00-07:00, 07:00-08:00, through 21:00-22:00

### Requirement 15

**User Story:** As a user, I want clear feedback on my actions without unnecessary interruptions, so that I can work efficiently while staying informed.

#### Acceptance Criteria

1. WHEN a user successfully completes a create action, THE System SHALL display a non-blocking toast notification that auto-dismisses after 3 seconds
2. WHEN a user successfully completes an update action, THE System SHALL display a non-blocking toast notification that auto-dismisses after 3 seconds
3. WHEN a user initiates a delete action, THE System SHALL display a confirmation dialog requiring explicit user approval before proceeding
4. WHEN a user successfully completes a delete action after confirmation, THE System SHALL display a non-blocking toast notification that auto-dismisses after 3 seconds
5. WHEN a user cancels a delete action, THE System SHALL close the confirmation dialog without performing the deletion

### Requirement 16

**User Story:** As a system operator, I want the application to handle email delivery failures gracefully, so that booking operations are not disrupted by email server issues.

#### Acceptance Criteria

1. WHEN an email notification fails to send, THE System SHALL log the error with details of the failed notification
2. WHEN an email notification fails to send, THE System SHALL complete the reservation operation successfully
3. WHEN an email notification fails to send, THE System SHALL not display an error to the user
4. THE System SHALL attempt to send email notifications asynchronously to avoid blocking user operations

### Requirement 17

**User Story:** As a club member, I want all times displayed in the local timezone, so that I can accurately schedule my court reservations.

#### Acceptance Criteria

1. THE System SHALL store all reservation times in UTC in the database
2. THE System SHALL display all times to users in the Europe/Berlin timezone
3. WHEN a user creates a reservation, THE System SHALL convert the selected time from Europe/Berlin to UTC before storing
4. WHEN displaying reservation times, THE System SHALL convert from UTC to Europe/Berlin timezone

### Requirement 18

**User Story:** As a club member, I want to make short notice bookings without affecting my regular reservation limit, so that I can take advantage of last-minute court availability while maintaining my planned reservations.

#### Acceptance Criteria

1. WHEN a member creates a reservation within 15 minutes of the slot start time, THE System SHALL classify it as a short notice booking
2. WHEN a member creates a short notice booking, THE System SHALL not count it toward the member's active reservation limit of 2 reservations
3. WHEN calculating active reservations for the 2-reservation limit, THE System SHALL exclude all short notice bookings from the count
4. WHEN a member has 2 regular active reservations, THE System SHALL still allow creation of short notice bookings
5. WHEN a member attempts to create a short notice booking AND already has 1 active short notice booking, THE System SHALL reject the booking and display an error message
6. WHEN a member has 1 active short notice booking AND attempts to create another short notice booking, THE System SHALL prevent the creation until the existing short notice booking is completed or cancelled
7. WHEN a time slot can be booked as short notice, THE System SHALL allow booking from 15 minutes before start time until the end of the slot
8. WHEN a member attempts to book a slot for 10:00-11:00 at 9:45 or later, THE System SHALL classify this as a short notice booking
9. WHEN a member attempts to book a slot for 10:00-11:00 at 10:59, THE System SHALL still allow the short notice booking
10. THE System SHALL apply all other booking constraints to short notice bookings including court availability, member authentication, and time slot validity
11. WHEN displaying reservations in the court grid, THE System SHALL highlight short notice bookings with a distinct background color to differentiate them from regular reservations
12. WHEN a short notice booking is created, THE System SHALL prevent cancellation of that booking since it is created within the 15-minute cancellation prohibition window

### Requirement 19

**User Story:** As an administrator, I want advanced block management capabilities, so that I can efficiently manage court availability for recurring events, maintenance schedules, and complex blocking scenarios.

#### Acceptance Criteria

1. WHEN an administrator creates a recurring block, THE System SHALL require a start date, end date, recurrence pattern (daily, weekly, monthly), and time range and generate individual block instances for each occurrence
2. WHEN an administrator creates a weekly recurring block, THE System SHALL allow selection of specific days of the week (e.g., "every Saturday") and generate blocks for those days only between the start and end dates
3. WHEN an administrator creates a recurring block series (e.g., "Court 5, every Saturday 10:00-12:00, June 1-30 for tennis course"), THE System SHALL generate individual block instances for each occurrence and link them as part of the same series
4. WHEN an administrator attempts to create a recurring block without an end date, THE System SHALL reject the operation and display an error message requiring an end date
5. WHEN an administrator edits an entire recurring block series, THE System SHALL provide options to modify the time range, courts, reason, or recurrence pattern and apply changes to all future instances in the series
6. WHEN an administrator shifts an entire recurring block series time (e.g., from 10:00-12:00 to 9:00-11:00), THE System SHALL update all future instances in the series with the new time range
7. WHEN an administrator edits a single instance of a recurring block series, THE System SHALL allow modification of that specific occurrence without affecting other instances in the series
8. WHEN an administrator modifies a single recurring block instance, THE System SHALL clearly indicate that the instance has been modified and is no longer following the original series pattern
9. WHEN an administrator views the block management interface, THE System SHALL display a calendar view showing all existing blocks with visual indicators for different block types and series relationships
10. WHEN an administrator selects multiple courts, THE System SHALL allow creation of blocks for all selected courts simultaneously with the same time period, dates, and reason
11. WHEN an administrator creates a block template, THE System SHALL store the template with a name, default time range, reason, court selection, and recurrence settings for future reuse
12. WHEN an administrator applies a block template, THE System SHALL pre-fill the block creation form with the template's saved values including start date, end date, and recurrence pattern
13. WHEN an administrator views existing blocks, THE System SHALL provide filtering options by date range, court, reason, and block type (single vs recurring series)
14. WHEN an administrator selects multiple existing blocks, THE System SHALL allow bulk deletion of the selected blocks with a single confirmation
15. WHEN an administrator deletes a recurring block series, THE System SHALL offer options to delete the single occurrence, all future occurrences, or the entire series
16. WHEN displaying blocks in the calendar view, THE System SHALL use different colors or patterns to distinguish between maintenance, weather, tournament, and championship blocks
17. WHEN an administrator hovers over a block in the calendar view, THE System SHALL display a tooltip with block details including time, reason, affected courts, series information, and any individual modifications
18. WHEN an administrator creates a block that conflicts with existing reservations, THE System SHALL display a preview of affected reservations before confirming the block creation
19. THE System SHALL maintain an audit log of all block operations including creation, modification, and deletion with timestamps and administrator identification

### Requirement 20

**User Story:** As an administrator, I want to manage custom block reasons and sub-reasons, so that I can accurately categorize and track why courts are blocked with specific details.

#### Acceptance Criteria

1. WHEN an administrator accesses the block reason management interface, THE System SHALL display all existing block reasons with options to add, edit, or delete reasons
2. WHEN an administrator creates a new block reason, THE System SHALL store the reason name and make it available for selection when creating blocks
3. WHEN an administrator edits an existing block reason, THE System SHALL update the reason name and apply the change to future block selections while preserving historical block data
4. WHEN an administrator deletes a block reason that is currently in use by existing blocks, THE System SHALL require confirmation and display a warning message explaining that historical blocks will retain the reason but all future blocks using this reason will be deleted
5. WHEN an administrator confirms deletion of a block reason in use, THE System SHALL preserve all past blocks with that reason, delete all future blocks using that reason, and remove the reason from future block creation options
6. WHEN an administrator deletes an unused block reason, THE System SHALL remove it from the system and future block creation options after confirmation
7. WHEN an administrator creates a block, THE System SHALL allow selection of an optional sub-reason or category to provide additional detail
8. WHEN an administrator selects "Championship" as a block reason, THE System SHALL allow entry of a sub-reason such as "Team A vs Team B" or "Junior Championship"
9. WHEN an administrator selects "Tennis Course" as a block reason, THE System SHALL allow entry of a sub-reason such as "Beginner Course" or "Advanced Training"
10. WHEN an administrator creates a block with a sub-reason, THE System SHALL store both the main reason and sub-reason and display both in block details
11. WHEN displaying blocks in lists or calendar views, THE System SHALL show both the main reason and sub-reason (e.g., "Championship - Team A vs Team B")
12. WHEN an administrator manages sub-reasons, THE System SHALL allow creation of predefined sub-reason templates for common scenarios
13. WHEN filtering blocks, THE System SHALL allow filtering by both main reason and sub-reason categories
14. THE System SHALL provide default block reasons including "Maintenance", "Weather", "Tournament", "Championship", and "Tennis Course" that can be modified by administrators
15. WHEN an administrator creates a block template, THE System SHALL include the selected reason and sub-reason in the template for future reuse
