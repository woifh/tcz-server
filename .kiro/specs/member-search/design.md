# Design Document: Member Search for Favourites

## Overview

This design document describes the implementation of a member search feature that enables club members to search for and add other members to their favourites list. The feature will be implemented as an enhancement to the existing member management system, providing a responsive search interface with real-time results and one-click favourite additions.

The search functionality will be implemented using:
- **Backend**: Flask route with SQLAlchemy queries for efficient member searching
- **Frontend**: JavaScript with fetch API for asynchronous search requests
- **UI**: Tailwind CSS for responsive, mobile-friendly interface
- **Localization**: All text in German

## Architecture

### Component Structure

```
┌─────────────────────────────────────────┐
│         Frontend (Browser)              │
│  ┌───────────────────────────────────┐  │
│  │   Search Input Component          │  │
│  │   - Debounced input handler       │  │
│  │   - Loading state management      │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Search Results Component        │  │
│  │   - Result list rendering         │  │
│  │   - Add to favourites buttons     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    │ AJAX (fetch)
                    ▼
┌─────────────────────────────────────────┐
│         Backend (Flask)                 │
│  ┌───────────────────────────────────┐  │
│  │   /members/search Route           │  │
│  │   - Query parameter validation    │  │
│  │   - Authentication check          │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   MemberService                   │  │
│  │   - search_members()              │  │
│  │   - Filter logic                  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Database (MySQL)                │
│  ┌───────────────────────────────────┐  │
│  │   Member Table                    │  │
│  │   - name (indexed)                │  │
│  │   - email (indexed)               │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Favourites Association Table    │  │
│  │   - member_id                     │  │
│  │   - favourite_id                  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Backend Route: `/members/search`

**Endpoint**: `GET /members/search`

**Query Parameters**:
- `q` (required): Search query string (minimum 1 character)

**Response Format**:
```json
{
  "results": [
    {
      "id": 123,
      "name": "Max Mustermann",
      "email": "max.mustermann@example.com"
    }
  ],
  "count": 1
}
```

**Error Responses**:
- `400 Bad Request`: Missing or invalid query parameter
- `401 Unauthorized`: User not authenticated
- `500 Internal Server Error`: Database or server error

### 2. MemberService Methods

**New Method**: `search_members(query: str, current_member_id: int) -> List[Member]`

**Purpose**: Search for members by name or email, excluding current member and existing favourites

**Parameters**:
- `query`: Search string (case-insensitive)
- `current_member_id`: ID of the member performing the search

**Returns**: List of Member objects matching the search criteria

**Logic**:
1. Query members where firstname OR lastname OR email contains the search query (case-insensitive)
2. Exclude the current member
3. Exclude members already in current member's favourites
4. Order results alphabetically by lastname, then firstname
5. Limit results to 50 members to prevent performance issues

### 3. Frontend JavaScript Component

**File**: `app/static/js/member-search.js`

**Key Functions**:

```javascript
// Debounced search function
function debounceSearch(query, delay = 300)

// Fetch search results from API
async function searchMembers(query)

// Render search results in DOM
function renderSearchResults(results)

// Add member to favourites
async function addToFavourites(memberId)

// Clear search results
function clearSearchResults()
```

**Event Handlers**:
- Input event on search field (debounced)
- Click event on "Add to Favourites" buttons
- Clear button click event

### 4. UI Components

**Search Input**:
- Text input field with placeholder "Mitglied suchen..."
- Clear button (X icon) when input has text
- Loading spinner during search

**Search Results List**:
- Scrollable container (max-height with overflow)
- Each result shows:
  - Member name (bold)
  - Member email (smaller, gray text)
  - "Hinzufügen" button (Add button)
- Empty state message: "Keine Mitglieder gefunden"
- Loading state: Spinner with "Suche läuft..."

## Data Models

### Existing Models (No Changes Required)

**Member Model**: Already exists with name, email, and favourites relationship

**Favourites Association**: Already exists as many-to-many relationship

### Database Indexes

**Recommended Indexes** (for performance):
```sql
CREATE INDEX idx_member_firstname ON member(firstname);
CREATE INDEX idx_member_lastname ON member(lastname);
CREATE INDEX idx_member_email ON member(email);
```

These indexes will significantly improve search query performance, especially as the member count grows.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptence Criteria Testing Prework:

1.1 WHEN a member enters a search query containing at least one character, THE System SHALL return all members whose names contain the query text (case-insensitive)
Thoughts: This is a rule that should apply to all search queries. We can generate random member names (firstname/lastname) and search queries, perform the search, and verify that all returned results contain the query text in either their firstname or lastname (case-insensitive). This is testable across many inputs.
Testable: yes - property

1.2 WHEN a member submits an empty search query, THE System SHALL return an empty result set
Thoughts: This is testing a specific edge case - what happens with empty input. This is a single specific scenario.
Testable: yes - edge case

1.3 WHEN a search query matches multiple members, THE System SHALL return all matching members ordered alphabetically by name
Thoughts: This is about the ordering of results. We can generate random members, search for a query that matches multiple, and verify the results are sorted alphabetically by lastname then firstname. This should hold for all searches.
Testable: yes - property

1.4 WHEN a search query matches no members, THE System SHALL return an empty result set with a message indicating no results found
Thoughts: This is testing what happens when there are no matches. We can generate a random query that doesn't match any members and verify we get an empty result.
Testable: yes - edge case

1.5 WHEN displaying search results, THE System SHALL show each member's name and email address
Thoughts: This is about what information is included in results. For any search result, we can verify it contains firstname, lastname, and email fields (name is displayed as "firstname lastname").
Testable: yes - property

2.1 WHEN a member enters a search query containing an email pattern, THE System SHALL return all members whose email addresses contain the query text (case-insensitive)
Thoughts: Similar to 1.1 but for email. We can generate random emails and queries, and verify all results contain the query in their email.
Testable: yes - property

2.2 WHEN a search query matches both names and email addresses, THE System SHALL return all matching members without duplicates
Thoughts: This is testing that when a query matches both name (firstname or lastname) and email of the same member, that member appears only once. We can create members where firstname/lastname and email both match a query and verify no duplicates.
Testable: yes - property

2.3 WHEN a member searches using a partial email address, THE System SHALL return members whose email contains that partial text
Thoughts: This is essentially the same as 2.1 - partial matching is already covered by "contains". This is redundant with 2.1 and will be consolidated into Property 1.
Testable: yes - property (redundant with 2.1, consolidated into Property 1)

3.1 WHEN displaying search results, THE System SHALL exclude members who are already in the searching member's favourites list
Thoughts: For any member with favourites, when they search, none of their existing favourites should appear in results. We can create random favourites lists and verify exclusion.
Testable: yes - property

3.2 WHEN displaying search results, THE System SHALL exclude the searching member from the results
Thoughts: For any search, the member performing the search should never appear in their own results. This is a universal rule.
Testable: yes - property

3.3 WHEN a member adds a search result to favourites, THE System SHALL immediately remove that member from the displayed search results
Thoughts: This is about UI behavior after an action. We can test that after adding to favourites, re-running the same search excludes the newly added member.
Testable: yes - property

4.1 WHEN a member clicks an add button next to a search result, THE System SHALL add that member to the searching member's favourites list
Thoughts: This is testing the core add functionality. For any member and any search result, clicking add should result in that member being in the favourites list.
Testable: yes - property

4.2 WHEN a member is added to favourites from search results, THE System SHALL provide immediate visual feedback confirming the addition
Thoughts: This is about UI feedback, which is subjective and not easily testable programmatically.
Testable: no

4.3 WHEN a member is added to favourites, THE System SHALL update the favourites list without requiring a page reload
Thoughts: This is testing that the UI updates dynamically. We can verify the favourites list is updated without a full page reload by checking the DOM.
Testable: yes - property

4.4 WHEN adding a member to favourites fails, THE System SHALL display an error message explaining the failure reason
Thoughts: This is testing error handling. We can simulate failures and verify error messages are displayed.
Testable: yes - property

5.1 WHEN a member types in the search field, THE System SHALL debounce the search input to avoid excessive server requests
Thoughts: This is testing that rapid typing doesn't cause too many requests. We can simulate rapid input and count server requests.
Testable: yes - property

5.2 WHEN a search is in progress, THE System SHALL display a loading indicator to provide feedback
Thoughts: This is UI feedback that's hard to test programmatically.
Testable: no

5.3 WHEN search results are returned, THE System SHALL display them within 500 milliseconds for queries matching fewer than 100 members
Thoughts: This is a performance requirement with a specific time constraint. We can measure response times.
Testable: yes - property

5.4 WHEN a member clears the search field, THE System SHALL clear the search results immediately
Thoughts: This is testing that clearing input clears results. This is a specific UI interaction.
Testable: yes - example

6.1 WHEN a member accesses the search interface, THE System SHALL display a clearly labeled search input field
Thoughts: This is about UI design and is subjective.
Testable: no

6.2 WHEN a member uses the search on a mobile device, THE System SHALL provide a touch-friendly interface with appropriately sized buttons
Thoughts: This is about responsive design and is subjective/visual.
Testable: no

6.3 WHEN a member uses keyboard navigation, THE System SHALL allow navigating through search results using arrow keys
Thoughts: This is testing keyboard accessibility. We can simulate keyboard events and verify navigation works.
Testable: yes - property

6.4 WHEN displaying search results, THE System SHALL use German language for all labels and messages
Thoughts: For any displayed text, we can verify it's in German by checking for specific German keywords.
Testable: yes - property

6.5 WHEN the search field receives focus, THE System SHALL provide visual feedback indicating the field is active
Thoughts: This is about visual styling which is subjective.
Testable: no

### Property Reflection

After reviewing all properties, I've identified the following redundancies:

- **Property 2.3 is redundant with Property 2.1**: Both test partial email matching. Property 2.1 already covers "contains" which includes partial matches.
- **Properties 1.1 and 2.1 can be combined**: Both test the same "contains" logic, just on different fields. We can create one comprehensive property that tests searching across both name and email fields.

**Consolidated Properties**:
- Combine 1.1, 2.1, and 2.3 into Property 1: "Search returns all members where firstname OR lastname OR email contains query (case-insensitive)"
- Property 2.3 is redundant because "contains" already covers partial matching

### Correctness Properties

Property 1: Search returns matching members
*For any* search query and member database, all returned results should have either their firstname, lastname, or email containing the query text (case-insensitive)
**Validates: Requirements 1.1, 2.1, 2.3**

Property 2: Search results are alphabetically ordered
*For any* search query that returns multiple results, the results should be ordered alphabetically by lastname, then firstname
**Validates: Requirements 1.3**

Property 3: Search results include required fields
*For any* search result, the result should contain the member's firstname, lastname, and email address
**Validates: Requirements 1.5**

Property 4: Search excludes duplicates
*For any* search query that matches both a member's name (firstname or lastname) and email, that member should appear exactly once in the results
**Validates: Requirements 2.2**

Property 5: Search excludes existing favourites
*For any* member with favourites, when that member searches, none of their existing favourites should appear in the search results
**Validates: Requirements 3.1**

Property 6: Search excludes self
*For any* member performing a search, that member should never appear in their own search results
**Validates: Requirements 3.2**

Property 7: Adding to favourites removes from search results
*For any* search result that is added to favourites, performing the same search again should not include that member in the results
**Validates: Requirements 3.3**

Property 8: Add to favourites succeeds
*For any* valid member in search results, clicking add should result in that member being added to the searching member's favourites list
**Validates: Requirements 4.1**

Property 9: Favourites list updates without reload
*For any* member added to favourites, the favourites list should be updated in the UI without requiring a full page reload
**Validates: Requirements 4.3**

Property 10: Error messages displayed on failure
*For any* failed add-to-favourites operation, an error message should be displayed to the user
**Validates: Requirements 4.4**

Property 11: Search is debounced
*For any* rapid sequence of keystrokes in the search field, the number of server requests should be significantly less than the number of keystrokes
**Validates: Requirements 5.1**

Property 12: Search performance meets threshold
*For any* search query matching fewer than 100 members, the results should be returned and displayed within 500 milliseconds
**Validates: Requirements 5.3**

Property 13: Keyboard navigation works
*For any* search results list, pressing arrow keys should navigate through the results
**Validates: Requirements 6.3**

Property 14: German language used
*For any* displayed text in the search interface, the text should be in German (contains German keywords like "suchen", "hinzufügen", "keine", etc.)
**Validates: Requirements 6.4**

## Error Handling

### Backend Error Scenarios

1. **Empty or Invalid Query**
   - Validation: Check query parameter exists and has minimum length
   - Response: 400 Bad Request with message "Suchbegriff erforderlich"

2. **Unauthenticated Request**
   - Validation: Check user is logged in
   - Response: 401 Unauthorized, redirect to login

3. **Database Connection Error**
   - Handling: Log error, return generic error message
   - Response: 500 Internal Server Error with message "Suchfehler. Bitte versuchen Sie es erneut."

4. **Query Timeout**
   - Handling: Set query timeout limit (5 seconds)
   - Response: 500 Internal Server Error with message "Suche dauert zu lange. Bitte verfeinern Sie Ihre Suche."

### Frontend Error Scenarios

1. **Network Error**
   - Display: "Netzwerkfehler. Bitte überprüfen Sie Ihre Verbindung."
   - Action: Allow retry

2. **Add to Favourites Fails**
   - Display: Error message from server or generic "Fehler beim Hinzufügen"
   - Action: Keep member in search results, allow retry

3. **Search Takes Too Long**
   - Display: Loading indicator with timeout after 10 seconds
   - Action: Show message "Suche dauert länger als erwartet..."

## Testing Strategy

### Unit Tests

1. **MemberService.search_members()**
   - Test with various query strings
   - Test exclusion of current member
   - Test exclusion of existing favourites
   - Test case-insensitive matching
   - Test alphabetical ordering
   - Test result limit (50 members)

2. **Route /members/search**
   - Test authentication requirement
   - Test query parameter validation
   - Test response format
   - Test error responses

### Property-Based Tests

Using **Hypothesis** for Python property-based testing:

1. **Property 1**: Generate random member names/emails and queries, verify all results contain query
2. **Property 2**: Generate random members, verify results are sorted
3. **Property 3**: Verify all results have name and email
4. **Property 4**: Generate members with matching name and email, verify no duplicates
5. **Property 5**: Generate random favourites lists, verify exclusion
6. **Property 6**: Verify self-exclusion for any member
7. **Property 7**: Add to favourites, re-search, verify exclusion
8. **Property 8**: Add any result to favourites, verify it's in favourites list
9. **Property 11**: Simulate rapid typing, count requests, verify debouncing

### Integration Tests

1. **End-to-End Search Flow**
   - Login as member
   - Enter search query
   - Verify results displayed
   - Add member to favourites
   - Verify member removed from results
   - Verify member in favourites list

2. **Mobile Responsiveness**
   - Test on various screen sizes
   - Verify touch targets are appropriately sized
   - Verify scrolling works on mobile

### Performance Tests

1. **Search Performance**
   - Create database with 1000+ members
   - Measure search response time
   - Verify < 500ms for queries matching < 100 members

2. **Debounce Effectiveness**
   - Simulate rapid typing (10 keystrokes in 1 second)
   - Verify only 1-2 server requests made

## Implementation Notes

### Security Considerations

1. **SQL Injection Prevention**: Use parameterized queries (SQLAlchemy ORM handles this)
2. **XSS Prevention**: Escape all user-generated content in search results
3. **Rate Limiting**: Apply rate limiting to search endpoint to prevent abuse
4. **Authentication**: Require login for all search operations

### Performance Optimizations

1. **Database Indexes**: Create indexes on member.firstname, member.lastname, and member.email
2. **Result Limiting**: Limit search results to 50 members
3. **Query Optimization**: Use single query with OR condition instead of multiple queries
4. **Frontend Debouncing**: Wait 300ms after last keystroke before searching
5. **Caching**: Consider caching search results for identical queries (short TTL)

### Accessibility

1. **ARIA Labels**: Add appropriate ARIA labels to search input and results
2. **Keyboard Navigation**: Support Tab, Enter, and Arrow keys
3. **Screen Reader Support**: Announce search results count and loading states
4. **Focus Management**: Maintain logical focus order

### Localization

All text strings in German:
- Search placeholder: "Mitglied suchen..."
- Add button: "Hinzufügen"
- No results: "Keine Mitglieder gefunden"
- Loading: "Suche läuft..."
- Error messages: "Fehler beim Hinzufügen", "Netzwerkfehler", etc.
