# Implementation Plan

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

- [ ] 5. Implement reservation service
  - [ ] 5.1 Create ReservationService class
    - Implement create_reservation() with validation and email sending
    - Implement update_reservation() with validation and email sending
    - Implement cancel_reservation() with email sending
    - Implement get_member_active_reservations() query
    - Implement check_availability() query
    - Implement get_reservations_by_date() query
    - Add transaction management for all operations
    - _Requirements: 1.1, 1.3, 1.4, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 5.2 Write property test for one-hour duration
    - **Property 33: One-hour duration enforcement**
    - **Validates: Requirements 14.2**

- [ ] 6. Implement block service
  - [ ] 6.1 Create BlockService class
    - Implement create_block() method
    - Implement cancel_conflicting_reservations() to handle cascade cancellations
    - Implement get_blocks_by_date() query
    - Add email notifications for cancelled reservations with block reason
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ] 6.2 Write property test for cascade cancellation
    - **Property 14: Blocks cascade-cancel existing reservations**
    - **Validates: Requirements 5.2**
  
  - [ ] 6.3 Write property test for block cancellation notifications
    - **Property 15: Block cancellations include reason in notification**
    - **Validates: Requirements 5.3**

- [ ] 7. Implement authentication routes
  - [ ] 7.1 Create auth routes module
    - Implement GET /auth/login route with German login form
    - Implement POST /auth/login with credential validation
    - Implement GET /auth/logout route
    - Set up Flask-Login login_manager
    - Add user_loader callback
    - _Requirements: 13.1, 13.2, 13.4_
  
  - [ ] 7.2 Write property test for valid login
    - **Property 28: Valid login creates session**
    - **Validates: Requirements 13.1**
  
  - [ ] 7.3 Write property test for invalid login
    - **Property 29: Invalid login is rejected**
    - **Validates: Requirements 13.2**
  
  - [ ] 7.4 Write property test for logout
    - **Property 30: Logout terminates session**
    - **Validates: Requirements 13.4**

- [ ] 8. Implement member management routes
  - [ ] 8.1 Create members routes module
    - Implement GET /members route (admin only) to list all members
    - Implement POST /members route (admin only) to create member
    - Implement PUT /members/<id> route to update member
    - Implement DELETE /members/<id> route (admin only) to delete member
    - Implement POST /members/<id>/favourites to add favourite
    - Implement DELETE /members/<id>/favourites/<fav_id> to remove favourite
    - Add authorization checks for admin-only routes
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 3.1, 3.2_
  
  - [ ] 8.2 Write property test for member updates
    - **Property 18: Member updates modify stored data**
    - **Validates: Requirements 6.2**
  
  - [ ] 8.3 Write property test for member deletion
    - **Property 19: Member deletion removes from database**
    - **Validates: Requirements 6.3**
  
  - [ ] 8.4 Write property test for favourites operations
    - **Property 7: Favourites add and remove operations**
    - **Validates: Requirements 3.1, 3.2**

- [ ] 9. Implement court and availability routes
  - [ ] 9.1 Create courts routes module
    - Implement GET /courts route to return all courts
    - Implement GET /courts/availability?date=YYYY-MM-DD to return grid data
    - Build availability grid with status (available/reserved/blocked) for each cell
    - Include reservation details (booked_for, booked_by) for reserved cells
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 10. Implement reservation routes
  - [ ] 10.1 Create reservations routes module
    - Implement GET /reservations to list user's reservations
    - Implement GET /reservations?date=YYYY-MM-DD to list all reservations for date
    - Implement POST /reservations to create new reservation
    - Implement PUT /reservations/<id> to update reservation
    - Implement DELETE /reservations/<id> to cancel reservation
    - Add authorization checks (only booked_for or booked_by can modify/cancel)
    - _Requirements: 1.1, 2.1, 2.2, 2.3_
  
  - [ ] 10.2 Write property test for dual-member access control
    - **Property 4: Dual-member access control**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [ ] 11. Implement admin block routes
  - [ ] 11.1 Create admin routes module for blocks
    - Implement GET /blocks?date=YYYY-MM-DD to list blocks (admin only)
    - Implement POST /blocks to create block (admin only)
    - Implement DELETE /blocks/<id> to remove block (admin only)
    - Add authorization checks for admin-only access
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 12. Implement admin override functionality
  - [ ] 12.1 Add admin reservation deletion
    - Implement DELETE /admin/reservations/<id> route
    - Add reason parameter for deletion
    - Send notifications with override reason
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 12.2 Write property test for admin deletion
    - **Property 21: Admin deletion removes reservation**
    - **Validates: Requirements 7.1**
  
  - [ ] 12.3 Write property test for admin notifications
    - **Property 22: Admin deletion sends notifications**
    - **Validates: Requirements 7.2**
  
  - [ ] 12.4 Write property test for admin override reason
    - **Property 23: Admin override includes reason in notification**
    - **Validates: Requirements 7.3, 8.4**

- [ ] 13. Create base HTML template with German text
  - Create base.html with navigation, header, footer
  - Add Tailwind CSS responsive classes
  - Include German labels for all navigation items (Übersicht, Meine Buchungen, Favoriten, Abmelden)
  - Add mobile-responsive navigation menu
  - _Requirements: 9.1, 9.2, 9.3, 10.1_

- [ ] 14. Create login page template
  - Create login.html with German form labels
  - Add email and password fields with German placeholders
  - Add "Anmelden" button
  - Add error message display area
  - Make form responsive for mobile devices
  - _Requirements: 10.1, 13.1, 13.2_

- [ ] 15. Create dashboard with court availability grid
  - [ ] 15.1 Create dashboard.html template
    - Build 15-row (06:00-21:00) by 6-column (courts 1-6) grid
    - Add date selector with German labels
    - Implement color coding: green (available), red (reserved), grey (blocked)
    - Display "Gebucht für X von Y" text in reserved cells
    - Add click handlers to open booking form for available cells
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 15.2 Write property test for available cell rendering
    - **Property 9: Available slots render green**
    - **Validates: Requirements 4.2**
  
  - [ ] 15.3 Write property test for reserved cell rendering
    - **Property 10: Reserved slots render red with member names**
    - **Validates: Requirements 4.3**
  
  - [ ] 15.4 Write property test for blocked cell rendering
    - **Property 11: Blocked slots render grey**
    - **Validates: Requirements 4.4**
  
  - [ ] 15.5 Write property test for cell click behavior
    - **Property 12: Clicking available cell opens pre-filled form**
    - **Validates: Requirements 4.5**
  
  - [ ] 15.6 Add responsive design for tablet and mobile
    - Implement horizontal scrolling for tablet view
    - Implement vertical list with 1-2 courts visible for mobile
    - Use Tailwind responsive classes (sm:, md:, lg:)
    - Ensure touch-friendly button sizes
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 16. Create booking form modal
  - Create booking_form.html component
  - Add fields: Datum (date), Platz (court), Uhrzeit (time), Gebucht für (dropdown)
  - Populate "Gebucht für" dropdown with user's favourites list
  - Add "Buchung bestätigen" and "Abbrechen" buttons
  - Display validation errors in German
  - Make form responsive for mobile
  - _Requirements: 1.1, 3.3, 10.1_

- [ ] 16.1 Write property test for favourites in dropdown
  - **Property 8: Favourites displayed in booking dropdown**
  - **Validates: Requirements 3.3**

- [ ] 17. Create user reservations page
  - Create my_reservations.html template
  - Display list of user's active reservations
  - Show reservations where user is booked_for or booked_by
  - Add "Ändern" and "Löschen" buttons for each reservation
  - Format dates in German convention (DD.MM.YYYY)
  - Make responsive for mobile devices
  - _Requirements: 2.1, 10.1, 10.4_

- [ ] 17.1 Write property test for German date formatting
  - **Property 26: Dates formatted in German convention**
  - **Validates: Requirements 10.4**

- [ ] 18. Create admin panel template
  - Create admin_panel.html with tabs for different admin functions
  - Add court blocking interface with date, time, court, and reason selectors
  - Add member management section
  - Display same court grid as dashboard with admin controls
  - Add German labels for all admin functions
  - _Requirements: 5.1, 6.5, 10.1_

- [ ] 19. Create member list template
  - Create member_list.html for admin view
  - Display table with member name, email, role, created date
  - Add "Bearbeiten" and "Löschen" buttons for each member
  - Add "Neues Mitglied" button to create new member
  - Make responsive for mobile devices
  - _Requirements: 6.5, 10.1_

- [ ] 19.1 Write property test for member list display
  - **Property 20: Member list displays all members**
  - **Validates: Requirements 6.5**

- [ ] 20. Implement frontend JavaScript for interactivity
  - Add click handlers for grid cells to open booking modal
  - Implement AJAX calls for creating/updating/deleting reservations
  - Add form validation with German error messages
  - Implement date picker with German locale
  - Add loading indicators for async operations
  - Handle error responses and display German error messages
  - _Requirements: 4.5, 10.1_

- [ ] 21. Add authorization middleware
  - Create login_required decorator
  - Create admin_required decorator
  - Apply decorators to protected routes
  - Redirect unauthenticated users to login page
  - _Requirements: 13.5_

- [ ] 21.1 Write property test for unauthenticated access restriction
  - **Property 31: Unauthenticated access is restricted**
  - **Validates: Requirements 13.5**

- [ ] 22. Implement German error messages throughout application
  - Create error message constants in German
  - Update all validation errors to use German messages
  - Update all flash messages to German
  - Create custom error pages (404, 403, 500) in German
  - _Requirements: 10.1_

- [ ] 22.1 Write property test for German interface text
  - **Property 25: All interface text is German**
  - **Validates: Requirements 10.1, 10.3, 10.5**

- [ ] 23. Create Flask CLI commands
  - Implement `flask create-admin` command to create initial admin user
  - Implement `flask init-courts` command to populate 6 courts
  - Implement `flask test-email` command to verify email configuration
  - _Requirements: 6.1_

- [ ] 24. Set up PythonAnywhere deployment configuration
  - Create wsgi.py entry point
  - Create requirements.txt with all dependencies
  - Document environment variables needed
  - Create deployment guide with step-by-step instructions
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 25. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 26. Create database initialization script
  - Write script to create all tables
  - Add script to populate initial data (6 courts)
  - Add script to create first admin user
  - Test on MySQL database
  - _Requirements: 12.2_

- [ ] 27. Configure Hypothesis for property-based testing
  - Install Hypothesis library
  - Create custom strategies for domain objects (members, courts, times, dates)
  - Configure Hypothesis settings (min 100 iterations)
  - Create test fixtures and helpers
  - _Requirements: Testing Strategy_

- [ ] 28. Final integration testing
  - Test complete booking workflow end-to-end
  - Test admin blocking workflow end-to-end
  - Test favourites workflow end-to-end
  - Verify all emails are sent correctly
  - Test responsive design on multiple devices
  - Verify all German text displays correctly
  - _Requirements: All_

- [ ] 29. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
