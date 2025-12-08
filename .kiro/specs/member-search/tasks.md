# Implementation Plan: Member Search for Favourites

- [x] 1. Add database indexes for search performance
  - Create migration to add index on member.firstname
  - Create migration to add index on member.lastname
  - Create migration to add index on member.email
  - _Requirements: 5.3_

- [x] 2. Implement backend search functionality
  - [x] 2.1 Add search_members() method to MemberService
    - Implement case-insensitive search on firstname, lastname, and email
    - Exclude current member from results
    - Exclude existing favourites from results
    - Order results alphabetically by lastname, then firstname
    - Limit results to 50 members
    - _Requirements: 1.1, 1.3, 2.1, 2.2, 3.1, 3.2_
  
  - [ ]* 2.2 Write property test for search_members()
    - **Property 1: Search returns matching members**
    - **Validates: Requirements 1.1, 2.1, 2.3**
  
  - [ ]* 2.3 Write property test for alphabetical ordering
    - **Property 2: Search results are alphabetically ordered**
    - **Validates: Requirements 1.3**
  
  - [ ]* 2.4 Write property test for duplicate exclusion
    - **Property 4: Search excludes duplicates**
    - **Validates: Requirements 2.2**
  
  - [ ]* 2.5 Write property test for favourites exclusion
    - **Property 5: Search excludes existing favourites**
    - **Validates: Requirements 3.1**
  
  - [ ]* 2.6 Write property test for self-exclusion
    - **Property 6: Search excludes self**
    - **Validates: Requirements 3.2**

- [x] 3. Create search API endpoint
  - [x] 3.1 Implement GET /members/search route
    - Add route in app/routes/member_routes.py
    - Validate query parameter (minimum 1 character)
    - Require authentication
    - Call MemberService.search_members()
    - Return JSON response with results
    - Handle errors (400, 401, 500)
    - _Requirements: 1.1, 1.2, 1.4, 1.5_
  
  - [ ]* 3.2 Write unit tests for /members/search endpoint
    - Test authentication requirement
    - Test query parameter validation
    - Test response format
    - Test error responses
    - _Requirements: 1.1, 1.2, 1.4_

- [x] 4. Implement frontend search UI
  - [x] 4.1 Create member search HTML template
    - Add search input field with placeholder "Mitglied suchen..."
    - Add clear button (X icon)
    - Add loading spinner element
    - Add search results container
    - Add empty state message
    - Use Tailwind CSS for styling
    - _Requirements: 6.1, 6.4_
  
  - [x] 4.2 Create member-search.js JavaScript module
    - Implement debounced search function (300ms delay)
    - Implement searchMembers() to call API
    - Implement renderSearchResults() to display results
    - Implement clearSearchResults() function
    - Add event listeners for input, clear button
    - _Requirements: 5.1, 5.4_
  
  - [ ]* 4.3 Write property test for debouncing
    - **Property 11: Search is debounced**
    - **Validates: Requirements 5.1**

- [x] 5. Implement add to favourites from search
  - [x] 5.1 Add "Hinzufügen" button to each search result
    - Add button with member ID data attribute
    - Style button with Tailwind CSS
    - _Requirements: 4.1_
  
  - [x] 5.2 Implement addToFavourites() JavaScript function
    - Call POST /members/{id}/favourites API
    - Handle success: remove from search results, show confirmation
    - Handle errors: display error message
    - Update favourites list in UI without reload
    - _Requirements: 4.1, 4.3, 4.4_
  
  - [ ]* 5.3 Write property test for add to favourites
    - **Property 8: Add to favourites succeeds**
    - **Validates: Requirements 4.1**
  
  - [ ]* 5.4 Write property test for search result removal
    - **Property 7: Adding to favourites removes from search results**
    - **Validates: Requirements 3.3**

- [x] 6. Add keyboard navigation support
  - [x] 6.1 Implement arrow key navigation in search results
    - Add keydown event listener
    - Highlight current result on arrow up/down
    - Add to favourites on Enter key
    - _Requirements: 6.3_
  
  - [ ]* 6.2 Write property test for keyboard navigation
    - **Property 13: Keyboard navigation works**
    - **Validates: Requirements 6.3**

- [x] 7. Implement error handling and loading states
  - [x] 7.1 Add loading indicator during search
    - Show spinner while API request is in progress
    - Hide spinner when results arrive or error occurs
    - _Requirements: 5.2_
  
  - [x] 7.2 Add error message display
    - Show error messages for network failures
    - Show error messages for add to favourites failures
    - Use German error messages
    - _Requirements: 4.4, 6.4_
  
  - [ ]* 7.3 Write property test for error messages
    - **Property 10: Error messages displayed on failure**
    - **Validates: Requirements 4.4**

- [x] 8. Integrate search into favourites management page
  - [x] 8.1 Add search component to favourites page template
    - Include search input at top of favourites list
    - Position search results below input
    - Ensure responsive layout on mobile
    - _Requirements: 6.2_
  
  - [x] 8.2 Update favourites page route
    - Ensure page loads with search component
    - Test on various screen sizes
    - _Requirements: 6.2_

- [x] 9. Add accessibility features
  - [x] 9.1 Add ARIA labels and roles
    - Add aria-label to search input
    - Add role="listbox" to results container
    - Add role="option" to each result
    - Add aria-live region for result count
    - _Requirements: 6.1_
  
  - [x] 9.2 Implement focus management
    - Maintain logical tab order
    - Return focus to search input after adding favourite
    - _Requirements: 6.3_

- [x] 10. Performance optimization and testing
  - [ ]* 10.1 Write property test for search performance
    - **Property 12: Search performance meets threshold**
    - **Validates: Requirements 5.3**
  
  - [ ]* 10.2 Write property test for German localization
    - **Property 14: German language used**
    - **Validates: Requirements 6.4**
  
  - [ ]* 10.3 Write integration test for end-to-end search flow
    - Login as member
    - Enter search query
    - Verify results displayed
    - Add member to favourites
    - Verify member removed from results
    - Verify member in favourites list
    - _Requirements: 1.1, 3.3, 4.1, 4.3_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
