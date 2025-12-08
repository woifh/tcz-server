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
- **Booking Slot**: A one-hour time period between 06:00 and 22:00
- **Active Reservation**: A future reservation that has not been cancelled or completed
- **Favourites List**: A member's curated list of preferred playing partners
- **Booked For**: The member who will use the court
- **Booked By**: The member who created the reservation

## Requirements

### Requirement 1

**User Story:** As a club member, I want to create court reservations for myself or other members, so that I can secure playing time and coordinate with partners.

#### Acceptance Criteria

1. WHEN a member selects an available court and time slot, THE System SHALL create a reservation linking the court, date, time, booked_for member, and booked_by member
2. WHERE a member books for another member, THE System SHALL record both the booked_for member and the booked_by member identities
3. WHEN a member attempts to create a reservation, THE System SHALL verify the member has fewer than 2 active reservations before allowing the booking
4. WHEN a member creates a reservation, THE System SHALL send email notifications to both the booked_by member and the booked_for member
5. WHEN a member has 2 active reservations, THE System SHALL prevent creation of additional reservations until one becomes inactive

### Requirement 2

**User Story:** As a club member, I want to view, modify, and cancel my reservations, so that I can adjust my playing schedule as needed.

#### Acceptance Criteria

1. WHEN a member is the booked_for member or the booked_by member, THE System SHALL allow that member to view the reservation details
2. WHEN a member is the booked_for member or the booked_by member, THE System SHALL allow that member to modify the reservation time or court
3. WHEN a member is the booked_for member or the booked_by member, THE System SHALL allow that member to cancel the reservation
4. WHEN a reservation is modified, THE System SHALL send email notifications to both the booked_by member and the booked_for member
5. WHEN a reservation is cancelled, THE System SHALL send email notifications to both the booked_by member and the booked_for member

### Requirement 3

**User Story:** As a club member, I want to maintain a favourites list of preferred playing partners, so that I can quickly book courts for frequent partners.

#### Acceptance Criteria

1. WHEN a member adds another member to favourites, THE System SHALL store the relationship in the member's favourites list
2. WHEN a member removes a member from favourites, THE System SHALL delete the relationship from the favourites list
3. WHEN a member creates a reservation, THE System SHALL display the member's favourites list in the booked_for dropdown
4. THE System SHALL allow many-to-many relationships in favourites lists

### Requirement 4

**User Story:** As a club member, I want to view court availability in a visual grid, so that I can quickly identify open time slots.

#### Acceptance Criteria

1. WHEN a member views the overview page, THE System SHALL display a grid with rows representing hours from 06:00 to 21:00 and columns representing courts 1 through 6
2. WHEN a time slot is available, THE System SHALL display the cell in green
3. WHEN a time slot is reserved, THE System SHALL display the cell in red with text showing booked_for and booked_by member names
4. WHEN a time slot is blocked, THE System SHALL display the cell in grey
5. WHEN a member clicks an available cell, THE System SHALL open the booking form pre-filled with the selected court, date, and time

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
3. WHEN a member attempts to book while having 2 active reservations, THE System SHALL reject the booking and display an error message
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

1. WHEN a user successfully completes a create action, THE System SHALL display a non-blocking success message that auto-dismisses after 3 seconds
2. WHEN a user successfully completes an update action, THE System SHALL display a non-blocking success message that auto-dismisses after 3 seconds
3. WHEN a user initiates a delete action, THE System SHALL display a confirmation dialog requiring explicit user approval before proceeding
4. WHEN a user successfully completes a delete action after confirmation, THE System SHALL display a non-blocking success message that auto-dismisses after 3 seconds
5. THE System SHALL use toast notifications for all non-blocking success messages
