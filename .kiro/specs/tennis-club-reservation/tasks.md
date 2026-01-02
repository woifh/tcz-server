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

- [x] 38. Implement enhanced database models for advanced block management
  - [x] 38.1 Create BlockReason model
    - Implement BlockReason model with id, name, is_active, created_by_id, created_at
    - Add unique constraint on name field
    - Add foreign key relationship to Member (created_by)
    - Add indexes for name and is_active fields
    - _Requirements: 20.1, 20.2_
  
  - [x] 38.2 Create BlockSeries model for recurring blocks
    - Implement BlockSeries model with id, name, start_date, end_date, start_time, end_time, recurrence_pattern, recurrence_days, reason_id, sub_reason, created_by_id, created_at
    - Add foreign key relationships to BlockReason and Member
    - Add JSON field for recurrence_days to store weekly pattern
    - Add indexes for date range and reason queries
    - _Requirements: 19.1, 19.2, 19.3_
  
  - [x] 38.3 Create SubReasonTemplate model
    - Implement SubReasonTemplate model with id, reason_id, template_name, created_by_id, created_at
    - Add foreign key relationships to BlockReason and Member
    - Add index for reason_id queries
    - _Requirements: 20.12_
  
  - [x] 38.4 Create BlockTemplate model
    - Implement BlockTemplate model with id, name, court_selection, start_time, end_time, reason_id, sub_reason, recurrence_pattern, recurrence_days, created_by_id, created_at
    - Add JSON field for court_selection array
    - Add foreign key relationships to BlockReason and Member
    - Add unique constraint on name field
    - _Requirements: 19.11, 20.15_
  
  - [x] 38.5 Create BlockAuditLog model
    - Implement BlockAuditLog model with id, operation, block_id, series_id, operation_data, admin_id, timestamp
    - Add JSON field for operation_data
    - Add foreign key relationship to Member (admin)
    - Add indexes for timestamp, admin, and operation queries
    - _Requirements: 19.19_
  
  - [x] 38.6 Update Block model for enhanced features
    - Add reason_id foreign key to BlockReason (replace reason enum)
    - Add sub_reason text field for additional details
    - Add series_id foreign key to BlockSeries for recurring blocks
    - Add is_modified boolean field for series instance modifications
    - Update indexes and constraints
    - _Requirements: 19.7, 20.7, 20.10_
  
  - [x] 38.7 Create database migration for enhanced block models
    - Create migration to add new tables (block_reason, block_series, sub_reason_template, block_template, block_audit_log)
    - Create migration to update existing block table with new fields
    - Migrate existing block reasons to new BlockReason table
    - Set up foreign key constraints and indexes
    - _Requirements: 19.1, 20.1_
  
  - [x] 38.8 Write property test for block reason storage
    - **Property 64: Block reason creation and availability**
    - **Validates: Requirements 20.2**
  
  - [x] 38.9 Write property test for recurring block series generation
    - **Property 48: Recurring block series generation**
    - **Validates: Requirements 19.1**
  
  - [ ] 38.10 Write property test for block template storage
    - **Property 55: Block template storage and retrieval**
    - **Validates: Requirements 19.11, 20.15**

- [x] 39. Implement BlockReasonService for customizable block reasons
  - [x] 39.1 Create BlockReasonService class
    - Implement create_block_reason() method with validation
    - Implement update_block_reason() method with historical preservation
    - Implement delete_block_reason() method with usage checking
    - Implement get_all_block_reasons() query method
    - Implement get_reason_usage_count() for deletion validation
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_
  
  - [x] 39.2 Implement sub-reason template management
    - Implement create_sub_reason_template() method
    - Implement get_sub_reason_templates() query method
    - Implement delete_sub_reason_template() method
    - _Requirements: 20.12_
  
  - [x] 39.3 Implement default reason initialization
    - Implement initialize_default_reasons() method
    - Create default reasons: Maintenance, Weather, Tournament, Championship, Tennis Course
    - Implement cleanup_future_blocks_with_reason() for reason deletion
    - _Requirements: 20.14, 20.5_
  
  - [ ]* 39.4 Write property test for block reason management
    - **Property 63: Block reason management interface**
    - **Validates: Requirements 20.1**
  
  - [ ]* 39.5 Write property test for reason editing with historical preservation
    - **Property 65: Block reason editing with historical preservation**
    - **Validates: Requirements 20.3**
  
  - [ ]* 39.6 Write property test for reason deletion with usage warning
    - **Property 66: Block reason deletion with usage warning**
    - **Validates: Requirements 20.4**
  
  - [ ]* 39.7 Write property test for reason deletion with historical preservation
    - **Property 67: Block reason deletion with historical preservation**
    - **Validates: Requirements 20.5**
  
  - [ ]* 39.8 Write property test for unused reason deletion
    - **Property 68: Unused block reason deletion**
    - **Validates: Requirements 20.6**
  
  - [ ]* 39.9 Write property test for sub-reason template management
    - **Property 70: Sub-reason template management**
    - **Validates: Requirements 20.12**
  
  - [ ]* 39.10 Write property test for default reasons initialization
    - **Property 72: Default block reasons initialization**
    - **Validates: Requirements 20.14**

- [x] 40. Enhance BlockService for advanced block management
  - [x] 40.1 Update BlockService for recurring block series
    - Implement create_recurring_block_series() method
    - Implement get_series_blocks() query method
    - Implement update_entire_series() method for series-wide edits
    - Implement update_future_series() method for partial series edits
    - Implement update_single_instance() method for individual modifications
    - Implement delete_series_options() method with multiple deletion options
    - _Requirements: 19.1, 19.2, 19.3, 19.5, 19.6, 19.7, 19.15_
  
  - [x] 40.2 Implement multi-court block operations
    - Implement create_multi_court_blocks() method
    - Implement bulk_delete_blocks() method for selected blocks
    - Add transaction management for bulk operations
    - _Requirements: 19.10, 19.14_
  
  - [x] 40.3 Implement block template operations
    - Implement create_block_template() method
    - Implement get_block_templates() query method
    - Implement apply_block_template() method for form pre-filling
    - Implement delete_block_template() method
    - _Requirements: 19.11, 19.12_
  
  - [x] 40.4 Implement filtering and search functionality
    - Implement filter_blocks() method with multiple criteria
    - Implement get_conflict_preview() method for reservation conflicts
    - Add support for date range, court, reason, and block type filtering
    - _Requirements: 19.13, 19.18_
  
  - [x] 40.5 Implement audit logging
    - Implement log_block_operation() method
    - Implement get_audit_log() query method with filtering
    - Add audit logging to all block operations
    - _Requirements: 19.19_
  
  - [x] 40.6 Update existing block methods for enhanced features
    - Update create_block() to use reason_id instead of reason enum
    - Add sub_reason parameter to block creation
    - Update cancel_conflicting_reservations() for enhanced reasons
    - _Requirements: 20.7, 20.10_
  
  - [ ]* 40.7 Write property test for weekly recurring blocks
    - **Property 49: Weekly recurring blocks respect day selection**
    - **Validates: Requirements 19.2**
  
  - [ ]* 40.8 Write property test for series linking
    - **Property 50: Recurring block series linking**
    - **Validates: Requirements 19.3**
  
  - [ ]* 40.9 Write property test for end date requirement
    - **Property 51: Recurring blocks require end date**
    - **Validates: Requirements 19.4**
  
  - [ ]* 40.10 Write property test for series-wide edits
    - **Property 52: Series-wide edits affect all future instances**
    - **Validates: Requirements 19.5, 19.6**
  
  - [ ]* 40.11 Write property test for single instance edits
    - **Property 53: Single instance edits don't affect other instances**
    - **Validates: Requirements 19.7**
  
  - [ ]* 40.12 Write property test for multi-court block creation
    - **Property 54: Multi-court block creation**
    - **Validates: Requirements 19.10**
  
  - [ ]* 40.13 Write property test for block template application
    - **Property 56: Block template application**
    - **Validates: Requirements 19.12**
  
  - [ ]* 40.14 Write property test for block filtering
    - **Property 57: Block filtering functionality**
    - **Validates: Requirements 19.13**
  
  - [ ]* 40.15 Write property test for bulk deletion
    - **Property 58: Bulk block deletion**
    - **Validates: Requirements 19.14**
  
  - [ ]* 40.16 Write property test for series deletion options
    - **Property 59: Series deletion options**
    - **Validates: Requirements 19.15**
  
  - [ ]* 40.17 Write property test for conflict preview
    - **Property 61: Conflict preview accuracy**
    - **Validates: Requirements 19.18**
  
  - [ ]* 40.18 Write property test for audit logging
    - **Property 62: Block operation audit logging**
    - **Validates: Requirements 19.19**
  
  - [ ]* 40.19 Write property test for sub-reason storage and display
    - **Property 69: Sub-reason storage and display**
    - **Validates: Requirements 20.7, 20.10, 20.11**
  
  - [ ]* 40.20 Write property test for filtering by reason and sub-reason
    - **Property 71: Filtering by reason and sub-reason**
    - **Validates: Requirements 20.13**

- [x] 41. Implement enhanced admin routes for advanced block management
  - [x] 41.1 Update existing admin block routes
    - Update GET /admin/blocks to support enhanced filtering (date_range, court_ids, reason_ids, block_type)
    - Update POST /admin/blocks to use reason_id and sub_reason
    - Update DELETE /admin/blocks/<id> for enhanced audit logging
    - _Requirements: 19.13, 20.7, 19.19_
  
  - [x] 41.2 Implement recurring block series routes
    - Implement POST /admin/blocks/series for creating recurring block series
    - Implement PUT /admin/blocks/series/<series_id> for updating entire series
    - Implement PUT /admin/blocks/series/<series_id>/future for updating future instances
    - Implement DELETE /admin/blocks/series/<series_id> with deletion options
    - _Requirements: 19.1, 19.5, 19.6, 19.15_
  
  - [x] 41.3 Implement multi-court and bulk operations routes
    - Implement POST /admin/blocks/multi-court for creating blocks on multiple courts
    - Implement POST /admin/blocks/bulk-delete for bulk deletion
    - Implement GET /admin/blocks/conflict-preview for reservation conflict preview
    - _Requirements: 19.10, 19.14, 19.18_
  
  - [x] 41.4 Implement block template routes
    - Implement GET /admin/block-templates for listing templates
    - Implement POST /admin/block-templates for creating templates
    - Implement PUT /admin/block-templates/<id> for updating templates
    - Implement DELETE /admin/block-templates/<id> for deleting templates
    - Implement POST /admin/block-templates/<id>/apply for applying templates
    - _Requirements: 19.11, 19.12_
  
  - [x] 41.5 Implement block reason management routes
    - Implement GET /admin/block-reasons for listing reasons
    - Implement POST /admin/block-reasons for creating reasons
    - Implement PUT /admin/block-reasons/<id> for updating reasons
    - Implement DELETE /admin/block-reasons/<id> for deleting reasons with usage check
    - Implement GET /admin/block-reasons/<id>/usage for usage count
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_
  
  - [x] 41.6 Implement sub-reason template routes
    - Implement GET /admin/block-reasons/<id>/sub-reason-templates for listing templates
    - Implement POST /admin/block-reasons/<id>/sub-reason-templates for creating templates
    - Implement DELETE /admin/sub-reason-templates/<id> for deleting templates
    - _Requirements: 20.12_
  
  - [x] 41.7 Implement audit log routes
    - Implement GET /admin/blocks/audit-log for retrieving audit history
    - Add filtering support for audit log queries
    - _Requirements: 19.19_

- [x] 42. Create enhanced admin panel UI components
  - [x] 42.1 Create calendar view component
    - Create calendar-based interface for visualizing blocks
    - Implement monthly calendar grid with day cells
    - Add color-coded block indicators by reason type
    - Add hover tooltips with detailed block information
    - Add click-to-edit functionality for individual blocks
    - _Requirements: 19.9, 19.17_
  
  - [x] 42.2 Create recurring block series management interface
    - Create form for recurring block series creation
    - Add start/end date selection with validation
    - Add recurrence pattern selection (daily, weekly, monthly)
    - Add day-of-week selection for weekly patterns
    - Add multi-court selection interface
    - _Requirements: 19.1, 19.2, 19.4_
  
  - [x] 42.3 Create series editing interface
    - Create options for editing entire series vs single instance
    - Add visual feedback showing which instances will be affected
    - Implement series deletion options (single, future, all)
    - Add confirmation dialogs for series operations
    - _Requirements: 19.5, 19.6, 19.7, 19.15_
  
  - [x] 42.4 Create block template management interface
    - Create template creation form with all block parameters
    - Create template listing with edit/delete options
    - Implement template application with date override
    - Add template preview functionality
    - _Requirements: 19.11, 19.12_
  
  - [x] 42.5 Create block reason management interface
    - Create reason management panel with add/edit/delete options
    - Add usage tracking display for each reason
    - Implement deletion warnings for reasons in use
    - Create sub-reason template management
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.12_
  
  - [x] 42.6 Create advanced filtering interface
    - Create filter panel with date range selection
    - Add court selection (single or multiple)
    - Add reason and sub-reason filtering
    - Add block type filtering (single vs recurring series)
    - Add administrator filtering
    - _Requirements: 19.13_
  
  - [x] 42.7 Create bulk operations interface
    - Add checkbox selection for multiple blocks
    - Create bulk deletion interface with confirmation
    - Add series-aware selection (entire series or individual instances)
    - Implement conflict preview for bulk operations
    - _Requirements: 19.14, 19.18_
  
  - [ ]* 42.8 Write property test for block tooltip information
    - **Property 60: Block tooltip information**
    - **Validates: Requirements 19.17**

- [x] 43. Update German language support for enhanced admin features
  - [x] 43.1 Add German text for recurring block features
    - Add "Wiederkehrende Sperrung" for recurring block
    - Add "Serie bearbeiten" for edit series
    - Add "Einzelne Instanz bearbeiten" for edit single instance
    - Add "Alle zukünftigen Instanzen" for all future instances
    - Add "Gesamte Serie löschen" for delete entire series
    - _Requirements: 10.1_
  
  - [x] 43.2 Add German text for template features
    - Add "Sperrungsvorlage" for block template
    - Add "Vorlage anwenden" for apply template
    - Add "Vorlage speichern" for save template
    - _Requirements: 10.1_
  
  - [x] 43.3 Add German text for reason management
    - Add "Sperrungsgrund verwalten" for manage block reason
    - Add "Untergrund" for sub-reason
    - Add "Grund wird verwendet" for reason is in use
    - Add "Historische Daten bleiben erhalten" for historical data preservation
    - _Requirements: 10.1_
  
  - [x] 43.4 Add German text for calendar and filtering
    - Add "Kalenderansicht" for calendar view
    - Add "Monatliche Ansicht" for monthly view
    - Add "Konflikt-Vorschau" for conflict preview
    - Add "Betroffene Buchungen" for affected reservations
    - _Requirements: 10.1_

- [x] 44. Implement frontend JavaScript for enhanced admin features
  - [x] 44.1 Implement calendar view functionality
    - Create calendar rendering with block indicators
    - Add hover tooltips with block details
    - Implement click handlers for block editing
    - Add color coding by reason type
    - _Requirements: 19.9, 19.17_
  
  - [x] 44.2 Implement recurring block series management
    - Create series creation form with validation
    - Add recurrence pattern selection logic
    - Implement day-of-week selection for weekly patterns
    - Add series editing options with visual feedback
    - _Requirements: 19.1, 19.2, 19.5, 19.6, 19.7_
  
  - [x] 44.3 Implement template management functionality
    - Create template creation and editing forms
    - Implement template application with form pre-filling
    - Add template preview functionality
    - _Requirements: 19.11, 19.12_
  
  - [x] 44.4 Implement advanced filtering
    - Create filter interface with multiple criteria
    - Add dynamic filtering with AJAX updates
    - Implement filter persistence across page loads
    - _Requirements: 19.13_
  
  - [x] 44.5 Implement bulk operations
    - Add checkbox selection for multiple blocks
    - Create bulk deletion with confirmation
    - Implement conflict preview before operations
    - _Requirements: 19.14, 19.18_
  
  - [x] 44.6 Implement reason management interface
    - Create reason CRUD operations
    - Add usage tracking display
    - Implement deletion warnings and confirmations
    - Create sub-reason template management
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.12_

- [x] 45. Integration testing for enhanced admin panel
  - [x] 45.1 Test recurring block series workflows
    - Test series creation with different recurrence patterns
    - Test series editing (entire series, future instances, single instance)
    - Test series deletion options
    - Verify proper series linking and modification tracking
    - _Requirements: 19.1, 19.2, 19.3, 19.5, 19.6, 19.7, 19.15_
  
  - [x] 45.2 Test multi-court and bulk operations
    - Test multi-court block creation
    - Test bulk deletion of selected blocks
    - Test conflict preview functionality
    - Verify proper transaction handling
    - _Requirements: 19.10, 19.14, 19.18_
  
  - [x] 45.3 Test template functionality
    - Test template creation and storage
    - Test template application and form pre-filling
    - Test template editing and deletion
    - _Requirements: 19.11, 19.12_
  
  - [x] 45.4 Test reason management
    - Test custom reason creation and editing
    - Test reason deletion with usage checking
    - Test historical preservation of reason data
    - Test sub-reason template management
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.12_
  
  - [x] 45.5 Test filtering and search functionality
    - Test all filter combinations
    - Test search functionality
    - Test filter persistence
    - _Requirements: 19.13_
  
  - [x] 45.6 Test audit logging
    - Test audit log creation for all operations
    - Test audit log filtering and retrieval
    - Verify proper operation data storage
    - _Requirements: 19.19_
  
  - [x] 45.7 Test calendar view functionality
    - Test calendar rendering with blocks
    - Test hover tooltips and click interactions
    - Test color coding and visual indicators
    - _Requirements: 19.9, 19.17_

- [ ] 46. Final checkpoint for enhanced admin panel
  - Ensure all new tests pass, ask the user if questions arise.
  - Verify all existing functionality still works correctly
  - Test complete enhanced admin workflows end-to-end
  - Verify German language text is correct and consistent
  - Test responsive design with new admin features
