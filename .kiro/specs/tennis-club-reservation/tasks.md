^# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create Flask application factory pattern with `app/__init__.py`
  - Set up virtual environment and install dependencies (Flask, SQLAlchemy, Flask-Login, Flask-Mail, PyMySQL)
  - Create configuration module with environment variable loading
  - Set up directory structure for routes, services, models, templates, and static files
  - Initialize Tailwind CSS configuration
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 2. Implement database models
  - [x] 2.1 Create Member model with authentication fields
    - Implement Member model with id, name, email, password_hash, role, created_at
    - Add password hashing and verification methods
    - Implement Flask-Login UserMixin integration
    - Add many-to-many self-referential favourites relationship
    - _Requirements: 6.1, 13.3_
  
  - [x] 2.2 Write property test for password hashing
    - **Property 17: Member creation stores all fields**
    - **Validates: Requirements 6.1, 13.3**
  
  - [x] 2.3 Create Court model
    - Implement Court model with id, number (1-6), status
    - Add validation for court number range
    - _Requirements: 4.1_
  
  - [x] 2.4 Create Reservation model with relationships
    - Implement Reservation model with all fields (court_id, date, start_time, end_time, booked_for_id, booked_by_id, status, reason)
    - Add foreign key relationships to Member and Court
    - Add unique constraint on (court_id, date, start_time)
    - Add indexes for date and member queries
    - _Requirements: 1.1, 1.2, 11.5_
  
  - [x] 2.5 Write property test for reservation field storage
    - **Property 1: Reservation creation stores all required fields**
    - **Validates: Requirements 1.1, 1.2**
  
  - [x] 2.6 Create Block model
    - Implement Block model with court_id, date, start_time, end_time, reason, created_by_id
    - Add foreign key relationships
    - Add validation for reason enum values
    - _Requirements: 5.4, 5.5_
  
  - [x] 2.7 Write property test for block field storage
    - **Property 16: Block creation stores all fields**
    - **Validates: Requirements 5.4**
  
  - [x] 2.8 Create Notification model
    - Implement Notification model with recipient_id, type, message, timestamp, read
    - Add foreign key to Member
    - _Requirements: 8.1_
  
  - [x] 2.9 Create database migration scripts
    - Set up Flask-Migrate
    - Generate initial migration for all models
    - _Requirements: 12.2_

- [x] 3. Implement validation service
  - [x] 3.1 Create ValidationService class
    - Implement validate_booking_time() to check 06:00-21:00 range
    - Implement validate_member_reservation_limit() to check 2-reservation limit
    - Implement validate_no_conflict() to check for existing reservations
    - Implement validate_not_blocked() to check for blocks
    - Implement validate_all_booking_constraints() as comprehensive validator
    - _Requirements: 1.3, 11.1, 11.2, 14.1_
  
  - [x] 3.2 Write property test for time slot validation
    - **Property 32: Time slot validation**
    - **Validates: Requirements 14.1, 14.3**
  
  - [x] 3.3 Write property test for two-reservation limit
    - **Property 2: Two-reservation limit enforcement**
    - **Validates: Requirements 1.3, 11.3**
  
  - [x] 3.4 Write property test for reservation conflicts
    - **Property 27: Reservation conflicts are rejected**
    - **Validates: Requirements 11.1, 11.5**
  
  - [x] 3.5 Write property test for block enforcement
    - **Property 13: Blocks prevent new reservations**
    - **Validates: Requirements 5.1, 11.2**
  
  - [ ]* 3.6 Write property test for password minimum length
    - **Property 36: Password minimum length enforcement**
    - **Validates: Requirements 13.6**

- [x] 4. Implement email service
  - [x] 4.1 Create EmailService class with Flask-Mail integration
    - Set up Flask-Mail configuration
    - Create German email templates for all notification types
    - Implement send_booking_created() method
    - Implement send_booking_modified() method
    - Implement send_booking_cancelled() method
    - Implement send_admin_override() method
    - Add error handling for email failures (log but don't fail operations)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 4.2 Write property test for German email language
    - **Property 24: All email notifications use German language**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.5**
  
  - [x] 4.3 Write property test for booking notifications
    - **Property 3: Booking notifications sent to both parties**
    - **Validates: Requirements 1.4**
  
  - [x] 4.4 Write property test for modification notifications
    - **Property 5: Modification notifications sent to both parties**
    - **Validates: Requirements 2.4**
  
  - [x] 4.5 Write property test for cancellation notifications
    - **Property 6: Cancellation notifications sent to both parties**
    - **Validates: Requirements 2.5**
  
  - [ ]* 4.6 Write property test for email failure resilience
    - **Property 37: Email failures do not block operations**
    - **Validates: Requirements 16.1, 16.2, 16.3**

- [x] 5. Implement reservation service
  - [x] 5.1 Create ReservationService class
    - Implement create_reservation() with validation and email sending
    - Implement update_reservation() with validation and email sending
    - Implement cancel_reservation() with email sending
    - Implement get_member_active_reservations() query
    - Implement check_availability() query
    - Implement get_reservations_by_date() query
    - Add transaction management for all operations
    - Add timezone conversion utilities (Europe/Berlin <-> UTC)
    - Convert user input times from Europe/Berlin to UTC before storing
    - Convert database times from UTC to Europe/Berlin when displaying
    - _Requirements: 1.1, 1.3, 1.4, 2.2, 2.3, 2.4, 2.5, 17.1, 17.2, 17.3, 17.4_
  
  - [x] 5.2 Write property test for one-hour duration
    - **Property 33: One-hour duration enforcement**
    - **Validates: Requirements 14.2**
  
  - [ ]* 5.3 Write property test for UTC storage
    - **Property 38: Times stored in UTC**
    - **Validates: Requirements 17.1**
  
  - [ ]* 5.4 Write property test for timezone display
    - **Property 39: Times displayed in Europe/Berlin timezone**
    - **Validates: Requirements 17.2, 17.4**

- [x] 6. Implement block service
  - [x] 6.1 Create BlockService class
    - Implement create_block() method
    - Implement cancel_conflicting_reservations() to handle cascade cancellations
    - Implement get_blocks_by_date() query
    - Add email notifications for cancelled reservations with block reason
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 6.2 Write property test for cascade cancellation
    - **Property 14: Blocks cascade-cancel existing reservations**
    - **Validates: Requirements 5.2**
  
  - [x] 6.3 Write property test for block cancellation notifications
    - **Property 15: Block cancellations include reason in notification**
    - **Validates: Requirements 5.3**

- [x] 7. Implement authentication routes
  - [x] 7.1 Create auth routes module
    - Implement GET /auth/login route with German login form
    - Implement POST /auth/login with credential validation
    - Implement GET /auth/logout route
    - Set up Flask-Login login_manager
    - Add user_loader callback
    - _Requirements: 13.1, 13.2, 13.4_
  
  - [x] 7.2 Write property test for valid login
    - **Property 28: Valid login creates session**
    - **Validates: Requirements 13.1**
  
  - [x] 7.3 Write property test for invalid login
    - **Property 29: Invalid login is rejected**
    - **Validates: Requirements 13.2**
  
  - [x] 7.4 Write property test for logout
    - **Property 30: Logout terminates session**
    - **Validates: Requirements 13.4**

- [x] 8. Implement member management routes
  - [x] 8.1 Create members routes module
    - Implement GET /members route (admin only) to list all members
    - Implement POST /members route (admin only) to create member
    - Implement PUT /members/<id> route to update member
    - Implement DELETE /members/<id> route (admin only) to delete member
    - Implement POST /members/<id>/favourites to add favourite
    - Implement DELETE /members/<id>/favourites/<fav_id> to remove favourite
    - Add authorization checks for admin-only routes
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 3.1, 3.2_
  
  - [x] 8.2 Write property test for member updates
    - **Property 18: Member updates modify stored data**
    - **Validates: Requirements 6.2**
  
  - [x] 8.3 Write property test for member deletion
    - **Property 19: Member deletion removes from database**
    - **Validates: Requirements 6.3**
  
  - [x] 8.4 Write property test for favourites operations
    - **Property 7: Favourites add and remove operations**
    - **Validates: Requirements 3.1, 3.2**
  
  - [ ]* 8.5 Write property test for self-favouriting prevention
    - **Property 8a: Self-favouriting is prevented**
    - **Validates: Requirements 3.4**
  
  - [ ]* 8.6 Write property test for favourites independence
    - **Property 8b: Favourites are independent many-to-many relationships**
    - **Validates: Requirements 3.5**
  
  - [ ]* 8.7 Write property test for booking any member
    - **Property 8c: Booking allowed for any member**
    - **Validates: Requirements 3.6**

- [x] 9. Implement court and availability routes
  - [x] 9.1 Create courts routes module
    - Implement GET /courts route to return all courts
    - Implement GET /courts/availability?date=YYYY-MM-DD to return grid data
    - Build availability grid with status (available/reserved/blocked) for each cell
    - Include reservation details (booked_for, booked_by) for reserved cells
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 10. Implement reservation routes
  - [x] 10.1 Create reservations routes module
    - Implement GET /reservations to list user's reservations
    - Implement GET /reservations?date=YYYY-MM-DD to list all reservations for date
    - Implement POST /reservations to create new reservation
    - Implement PUT /reservations/<id> to update reservation
    - Implement DELETE /reservations/<id> to cancel reservation
    - Add authorization checks (only booked_for or booked_by can modify/cancel)
    - _Requirements: 1.1, 2.1, 2.2, 2.3_
  
  - [x] 10.2 Write property test for dual-member access control
    - **Property 4: Dual-member access control**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 11. Implement admin block routes
  - [x] 11.1 Create admin routes module for blocks
    - Implement GET /blocks?date=YYYY-MM-DD to list blocks (admin only)
    - Implement POST /blocks to create block (admin only)
    - Implement DELETE /blocks/<id> to remove block (admin only)
    - Add authorization checks for admin-only access
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 12. Implement admin override functionality
  - [x] 12.1 Add admin reservation deletion
    - Implement DELETE /admin/reservations/<id> route
    - Add reason parameter for deletion
    - Send notifications with override reason
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 12.2 Write property test for admin deletion
    - **Property 21: Admin deletion removes reservation**
    - **Validates: Requirements 7.1**
  
  - [x] 12.3 Write property test for admin notifications
    - **Property 22: Admin deletion sends notifications**
    - **Validates: Requirements 7.2**
  
  - [x] 12.4 Write property test for admin override reason
    - **Property 23: Admin override includes reason in notification**
    - **Validates: Requirements 7.3, 8.4**

- [x] 13. Create base HTML template with German text
  - Create base.html with navigation, header, footer
  - Add Tailwind CSS responsive classes
  - Include German labels for all navigation items (Übersicht, Meine Buchungen, Favoriten, Abmelden)
  - Add mobile-responsive navigation menu
  - _Requirements: 9.1, 9.2, 9.3, 10.1_

- [x] 14. Create login page template
  - Create login.html with German form labels
  - Add email and password fields with German placeholders
  - Add "Anmelden" button
  - Add error message display area
  - Make form responsive for mobile devices
  - _Requirements: 10.1, 13.1, 13.2_

- [x] 15. Create dashboard with court availability grid
  - [x] 15.1 Create dashboard.html template
    - Build 15-row (06:00-21:00) by 6-column (courts 1-6) grid
    - Add date selector with German labels
    - Implement color coding: green (available), red (reserved), grey (blocked)
    - Display "Gebucht für X von Y" text in reserved cells
    - Add click handlers to open booking form for available cells
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 15.2 Write property test for available cell rendering
    - **Property 9: Available slots render green**
    - **Validates: Requirements 4.2**
  
  - [x] 15.3 Write property test for reserved cell rendering
    - **Property 10: Reserved slots render red with member names**
    - **Validates: Requirements 4.3**
  
  - [x] 15.4 Write property test for blocked cell rendering
    - **Property 11: Blocked slots render grey**
    - **Validates: Requirements 4.4**
  
  - [x] 15.5 Write property test for cell click behavior
    - **Property 12: Clicking available cell opens pre-filled form**
    - **Validates: Requirements 4.5**
  
  - [x] 15.6 Add responsive design for tablet and mobile
    - Implement horizontal scrolling for tablet view
    - Implement vertical list with 1-2 courts visible for mobile
    - Use Tailwind responsive classes (sm:, md:, lg:)
    - Ensure touch-friendly button sizes
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 16. Create booking form modal
  - Create booking_form.html component
  - Add fields: Datum (date), Platz (court), Uhrzeit (time), Gebucht für (dropdown)
  - Populate "Gebucht für" dropdown with user's favourites list
  - Add "Buchung bestätigen" and "Abbrechen" buttons
  - Display validation errors in German
  - Make form responsive for mobile
  - _Requirements: 1.1, 3.3, 10.1_

- [x] 16.1 Write property test for favourites in dropdown
  - **Property 8: Favourites displayed in booking dropdown**
  - **Validates: Requirements 3.3**

- [x] 17. Create user reservations page
  - Create my_reservations.html template
  - Display list of user's active reservations
  - Show reservations where user is booked_for or booked_by
  - Add "Ändern" and "Löschen" buttons for each reservation
  - Format dates in German convention (DD.MM.YYYY)
  - Make responsive for mobile devices
  - _Requirements: 2.1, 10.1, 10.4_

- [x] 17.1 Write property test for German date formatting
  - **Property 26: Dates formatted in German convention**
  - **Validates: Requirements 10.4**

- [x] 18. Create admin panel template
  - Create admin_panel.html with tabs for different admin functions
  - Add court blocking interface with date, time, court, and reason selectors
  - Add member management section
  - Display same court grid as dashboard with admin controls
  - Add German labels for all admin functions
  - _Requirements: 5.1, 6.5, 10.1_

- [x] 19. Create member list template
  - Create member_list.html for admin view
  - Display table with member name, email, role, created date
  - Add "Bearbeiten" and "Löschen" buttons for each member
  - Add "Neues Mitglied" button to create new member
  - Make responsive for mobile devices
  - _Requirements: 6.5, 10.1_

- [x] 19.1 Write property test for member list display
  - **Property 20: Member list displays all members**
  - **Validates: Requirements 6.5**

- [x] 20. Implement frontend JavaScript for interactivity
  - Add click handlers for grid cells to open booking modal
  - Implement AJAX calls for creating/updating/deleting reservations
  - Add form validation with German error messages
  - Implement date picker with German locale
  - Add loading indicators for async operations
  - Handle error responses and display German error messages
  - Implement toast notifications for success messages (auto-dismiss after 3 seconds)
  - Implement confirmation dialogs for delete actions
  - _Requirements: 4.5, 10.1, 15.1, 15.2, 15.3, 15.4, 15.5_
  
  - [ ]* 20.1 Write property test for create action toast
    - **Property 35: Create action toast notifications**
    - **Validates: Requirements 15.1**
  
  - [ ]* 20.2 Write property test for update action toast
    - **Property 35a: Update action toast notifications**
    - **Validates: Requirements 15.2**
  
  - [ ]* 20.3 Write property test for delete confirmation dialog
    - **Property 34: Delete actions require confirmation**
    - **Validates: Requirements 15.3**
  
  - [ ]* 20.4 Write property test for delete action toast
    - **Property 35b: Delete action toast notifications**
    - **Validates: Requirements 15.4**
  
  - [ ]* 20.5 Write property test for delete cancellation
    - **Property 35c: Delete cancellation closes dialog**
    - **Validates: Requirements 15.5**

- [x] 21. Add authorization middleware
  - Create login_required decorator
  - Create admin_required decorator
  - Apply decorators to protected routes
  - Redirect unauthenticated users to login page
  - _Requirements: 13.5_

- [x] 21.1 Write property test for unauthenticated access restriction
  - **Property 31: Unauthenticated access is restricted**
  - **Validates: Requirements 13.5**

- [x] 22. Implement German error messages throughout application
  - Create error message constants in German
  - Update all validation errors to use German messages
  - Update all flash messages to German
  - Create custom error pages (404, 403, 500) in German
  - _Requirements: 10.1_

- [x] 22.1 Write property test for German interface text
  - **Property 25: All interface text is German**
  - **Validates: Requirements 10.1, 10.3, 10.5**

- [x] 23. Create Flask CLI commands
  - Implement `flask create-admin` command to create initial admin user
  - Implement `flask init-courts` command to populate 6 courts
  - Implement `flask test-email` command to verify email configuration
  - _Requirements: 6.1_

- [x] 24. Set up PythonAnywhere deployment configuration
  - Create wsgi.py entry point
  - Create requirements.txt with all dependencies
  - Document environment variables needed
  - Create deployment guide with step-by-step instructions
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 25. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 26. Create database initialization script
  - Write script to create all tables
  - Add script to populate initial data (6 courts)
  - Add script to create first admin user
  - Test on MySQL database
  - _Requirements: 12.2_

- [x] 27. Configure Hypothesis for property-based testing
  - Install Hypothesis library
  - Create custom strategies for domain objects (members, courts, times, dates)
  - Configure Hypothesis settings (min 100 iterations)
  - Create test fixtures and helpers
  - _Requirements: Testing Strategy_

- [x] 28. Final integration testing
  - Test complete booking workflow end-to-end
  - Test admin blocking workflow end-to-end
  - Test favourites workflow end-to-end
  - Verify all emails are sent correctly
  - Test responsive design on multiple devices
  - Verify all German text displays correctly
  - _Requirements: All_

- [x] 29. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 30. Implement short notice booking feature
  - [x] 30.1 Add database migration for short notice booking field
    - Create migration to add `is_short_notice` boolean field to reservation table
    - Add index on `is_short_notice` field for performance
    - Set default value to FALSE for existing reservations
    - _Requirements: 18.1_
  
  - [x] 30.2 Update Reservation model for short notice bookings
    - Add `is_short_notice` field to Reservation model
    - Update model relationships and constraints
    - _Requirements: 18.1_
  
  - [x] 30.3 Enhance ReservationService for short notice logic
    - Implement `is_short_notice_booking()` method to classify bookings based on timing
    - Implement `classify_booking_type()` method to determine regular vs short notice
    - Update `get_member_regular_reservations()` to exclude short notice bookings
    - Modify `create_reservation()` to automatically set `is_short_notice` flag
    - _Requirements: 18.1, 18.2_
  
  - [x] 30.4 Write property test for short notice classification
    - **Property 40: Short notice booking classification**
    - **Validates: Requirements 18.1**
  
  - [x] 30.5 Update ValidationService for short notice booking limits
    - Modify `validate_member_reservation_limit()` to accept `is_short_notice` parameter
    - Update limit validation to only count regular reservations (exclude short notice)
    - Update `validate_all_booking_constraints()` to handle short notice bookings
    - Allow booking slots that have started but not ended for short notice bookings
    - _Requirements: 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_
  
  - [x] 30.6 Write property test for short notice reservation limit exclusion
    - **Property 41: Short notice bookings excluded from reservation limit**
    - **Validates: Requirements 18.2, 18.3**
  
  - [x] 30.7 Write property test for regular limit with short notice allowed
    - **Property 42: Regular reservation limit with short notice bookings allowed**
    - **Validates: Requirements 18.4**
  
  - [x] 30.8 Implement short notice booking limit validation
    - Add `validate_member_short_notice_limit()` method to ValidationService
    - Check that member has fewer than 1 active short notice booking
    - Update `validate_all_booking_constraints()` to include short notice limit check
    - Add German error message for short notice limit exceeded
    - _Requirements: 18.5, 18.6_
  
  - [x] 30.9 Write property test for short notice booking limit
    - **Property 42a: Short notice booking limit enforcement**
    - **Validates: Requirements 18.5, 18.6**
  
  - [x] 30.10 Implement enhanced cancellation validation
    - Update `validate_cancellation_allowed()` to check both 15-minute window and slot start time
    - Add logic to prevent cancellation within 15 minutes of start time
    - Add logic to prevent cancellation once slot has started
    - Update error messages to explain combined restriction
    - _Requirements: 2.3, 2.4_
  
  - [x] 30.11 Write property test for short notice booking time window
    - **Property 43: Short notice booking time window**
    - **Validates: Requirements 18.7, 18.8, 18.9**
  
  - [x] 30.12 Write property test for enhanced cancellation restrictions
    - **Property 46: Cancellation prevented within 15 minutes and during slot time**
    - **Validates: Requirements 2.3, 2.4**
  
  - [x] 30.13 Write property test for short notice booking non-cancellable nature
    - **Property 47: Short notice bookings cannot be cancelled**
    - **Validates: Requirements 18.12**

- [x] 31. Update frontend for short notice booking display
  - [x] 31.1 Update court grid CSS for orange short notice booking cells
    - Add inline CSS styling for orange background color for short notice bookings
    - Update grid rendering logic to apply orange styling when `is_short_notice` is true
    - Ensure orange color (#f97316) is distinct from green (available), red (regular), and grey (blocked)
    - Update dashboard legend to include orange color indicator for "Kurzfristig gebucht"
    - _Requirements: 18.9, 4.4_
  
  - [x] 31.2 Write property test for short notice booking visual display
    - **Property 45: Short notice bookings display with orange background**
    - **Validates: Requirements 18.9, 4.4**
  
  - [x] 31.3 Update booking form to handle short notice classification
    - Backend automatically detects and classifies short notice bookings based on timing
    - Update success messages to differentiate between regular and short notice bookings
    - Add "Kurzfristige Buchung erfolgreich erstellt!" message for short notice bookings
    - _Requirements: 18.1_
  
  - [x] 31.4 Update reservation list to show short notice booking indicators
    - Short notice bookings display with orange background in court grid
    - Add `showShortNoticeInfo()` function to explain non-cancellable nature when clicked
    - Disable effective cancellation for short notice bookings (show info message instead)
    - _Requirements: 18.9, 18.10_
  
  - [x] 31.5 Update cancellation UI to respect new time restrictions
    - Enhanced validation prevents cancellation within 15 minutes of start time
    - Enhanced validation prevents cancellation once slot has started
    - Update cancellation error messages to explain both time restrictions
    - Short notice bookings show info message explaining non-cancellable policy
    - _Requirements: 2.3, 2.4_

- [x] 32. Update API endpoints for short notice booking support
  - [x] 32.1 Update reservation creation endpoint
    - Modify POST /reservations to automatically classify and set `is_short_notice` flag
    - Update response to include short notice status
    - Update success messages to differentiate booking types
    - _Requirements: 18.1_
  
  - [x] 32.2 Update reservation listing endpoints
    - Modify GET /reservations to include `is_short_notice` field in response
    - Update GET /courts/availability to include short notice status in grid data
    - Return 'short_notice' status for short notice bookings in availability grid
    - _Requirements: 18.9_
  
  - [x] 32.3 Update cancellation endpoint with enhanced validation
    - Modify DELETE /reservations/<id> to use enhanced cancellation validation
    - Return appropriate error messages for both time restrictions
    - Ensure short notice bookings always return cancellation error
    - _Requirements: 2.3, 2.4, 18.10_

- [x] 33. Update email notifications for short notice bookings
  - [x] 33.1 Enhance email templates for short notice bookings
    - Email notifications work with existing templates for short notice bookings
    - Short notice bookings use same email templates as regular bookings
    - Email service handles short notice bookings transparently
    - _Requirements: 8.1, 18.1_
  
  - [x] 33.2 Write property test for short notice booking constraints
    - **Property 44: Short notice bookings follow all other constraints**
    - **Validates: Requirements 18.8**

- [x] 34. Update German language text for short notice features
  - [x] 34.1 Add German text constants for short notice bookings
    - Add "Kurzfristig gebucht für [Name] von [Name]" text for short notice booking display
    - Add "Kurzfristige Buchungen können nicht storniert werden" for cancellation restrictions
    - Add "Diese Buchung wurde innerhalb von 15 Minuten vor Spielbeginn erstellt" for explanations
    - Update all error messages to use proper German grammar
    - _Requirements: 10.1, 10.3_
  
  - [x] 34.2 Update success message examples
    - Add "Kurzfristige Buchung erfolgreich erstellt!" for short notice booking creation
    - Maintain "Buchung erfolgreich erstellt!" for regular bookings
    - Update existing success messages to maintain consistency
    - _Requirements: 15.1_

- [x] 35. Update documentation and help text
  - [x] 35.1 Update user interface help text
    - Dashboard legend includes "Kurzfristig gebucht" with orange color indicator
    - Short notice bookings show info message when clicked explaining non-cancellable policy
    - Visual distinction through orange background color provides clear user feedback
    - _Requirements: 18.1, 18.10_
  
  - [x] 35.2 Update admin documentation
    - Short notice bookings appear with orange background in admin views
    - Short notice bookings follow all other constraints (court availability, authentication, time slots)
    - Admin can see short notice status in reservation details
    - _Requirements: 18.8_

- [x] 36. Integration testing for short notice booking feature
  - [x] 36.1 Test short notice booking creation workflow
    - Test booking creation within 15 minutes of start time
    - Verify automatic classification as short notice booking
    - Verify orange display in court grid
    - Verify appropriate email notifications
    - _Requirements: 18.1, 18.9_
  
  - [x] 36.2 Test reservation limit behavior with short notice bookings
    - Test that members with 2 regular reservations can still make short notice bookings
    - Test that short notice bookings don't count toward the 2-reservation limit
    - Verify error messages for regular reservation limit exceeded
    - _Requirements: 18.2, 18.3, 18.4_
  
  - [x] 36.3 Test enhanced cancellation restrictions
    - Test cancellation prevention within 15 minutes of start time
    - Test cancellation prevention once slot has started
    - Test that short notice bookings can never be cancelled
    - Verify appropriate error messages for all scenarios
    - _Requirements: 2.3, 2.4, 18.10_
  
  - [x] 36.4 Test visual display of short notice bookings
    - Verify orange background color in court grid
    - Verify short notice indicators in reservation lists
    - Verify disabled cancellation buttons for short notice bookings
    - Test responsive design with new visual elements
    - _Requirements: 18.9, 9.1, 9.2, 9.3_

- [x] 37. Final checkpoint for short notice booking feature
  - Ensure all new tests pass, ask the user if questions arise.
  - Verify all existing functionality still works correctly
  - Test complete short notice booking workflow end-to-end
  - Verify German language text is correct and consistent
