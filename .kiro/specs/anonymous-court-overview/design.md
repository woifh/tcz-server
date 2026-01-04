# Design Document: Anonymous Court Overview

## Overview

This design implements anonymous access to the tennis court overview functionality, allowing visitors to view court availability without authentication while protecting member privacy. The solution modifies the existing dashboard and court availability system to support both authenticated and anonymous users with appropriate data filtering.

## Architecture

### Current System
The current system requires authentication for all routes:
- Dashboard route (`/`) requires `@login_required` decorator
- Court availability API (`/courts/availability`) requires `@login_required` decorator
- All user data is exposed to authenticated users

### Proposed Changes
1. **Dual Route Strategy**: Create separate routes for anonymous and authenticated access
2. **Data Filtering Layer**: Implement server-side filtering to remove sensitive data for anonymous users
3. **Template Adaptation**: Modify templates to conditionally render features based on authentication status
4. **Security Preservation**: Maintain existing security for authenticated features

## Components and Interfaces

### 1. Route Modifications

#### New Anonymous Routes
```python
# New anonymous dashboard route
@bp.route('/overview')  # Public court overview
def anonymous_overview():
    """Public court overview for anonymous users."""
    return render_template('anonymous_overview.html')

# Modified court availability route
@bp.route('/courts/availability')
def get_availability():
    """Get court availability - supports both anonymous and authenticated users."""
    # Determine user type and filter data accordingly
```

#### Root Route Handler
```python
# New root route in main app
@app.route('/')
def index():
    """Root route - redirect based on authentication status."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    else:
        return redirect(url_for('dashboard.anonymous_overview'))
```

### 2. Data Filtering Service

#### AnonymousDataFilter Class
```python
class AnonymousDataFilter:
    """Service for filtering sensitive data for anonymous users."""
    
    @staticmethod
    def filter_availability_data(grid_data, is_authenticated):
        """Filter court availability data based on user authentication."""
        if is_authenticated:
            return grid_data
        
        # Filter out member information from reservations
        for court in grid_data:
            for slot in court['slots']:
                if slot['status'] in ['reserved', 'short_notice']:
                    slot['status'] = 'reserved'  # Normalize short_notice to reserved
                    slot['details'] = None  # Remove member details
                # Block details remain unchanged
        
        return grid_data
```

### 3. Template System

#### Template Structure
- `anonymous_overview.html` - Dedicated template for anonymous users
- `dashboard.html` - Existing template for authenticated users
- Shared components for common elements (grid, legend, date navigation)

#### Template Features for Anonymous Users
- Read-only court availability grid
- Date navigation controls
- Legend for court statuses
- Login prompt/link
- No booking functionality
- No "My Reservations" section

### 4. Frontend JavaScript Modifications

#### Dashboard Component Updates
```javascript
// Modified dashboard.js component
function dashboard() {
    return {
        isAuthenticated: window.isAuthenticated || false,
        
        handleSlotClick(courtId, time, slot) {
            if (!this.isAuthenticated) {
                // No action for anonymous users
                return;
            }
            // Existing booking logic for authenticated users
        },
        
        getSlotClass(slot, time) {
            // Same styling logic for both user types
            // Remove hover effects for anonymous users
            const baseClasses = this.getBaseSlotClasses(slot, time);
            if (!this.isAuthenticated) {
                return baseClasses; // No hover or click styles
            }
            return baseClasses + ' cursor-pointer hover:opacity-80';
        }
    }
}
```

## Data Models

No changes to existing data models are required. The filtering happens at the service layer, preserving the existing database schema and model relationships.

### Existing Models Used
- `Court` - Tennis court information
- `Reservation` - Booking data (filtered for anonymous users)
- `Block` - Court blocking information (fully visible)
- `Member` - User data (hidden from anonymous users)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Anonymous Data Privacy
*For any* court availability data served to anonymous users, all member names, member IDs, booking IDs, and personal identifiers should be filtered out, and short-notice bookings should appear as regular reservations.
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 2: Block Information Consistency  
*For any* blocked court slot, anonymous users should see identical block information (reason, details, and visual styling) as authenticated users.
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: Availability Data Consistency
*For any* court availability data, anonymous users should see the same availability status, time formatting, and visual indicators as authenticated users, differing only in the absence of private member details.
**Validates: Requirements 6.1, 6.4, 6.5**

### Property 4: Date Navigation Functionality
*For any* date change operation, anonymous users should receive updated availability grid data that correctly reflects the selected date, including proper marking of past time slots.
**Validates: Requirements 1.4, 1.5**

### Property 5: Read-Only Interface Enforcement
*For any* court slot (available or reserved) displayed to anonymous users, no interactive click handlers or hover effects should be present.
**Validates: Requirements 4.3, 4.4**

### Property 6: Server-Side Data Filtering
*For any* data response to anonymous users, sensitive information filtering should occur at the server level before the response is sent, ensuring no sensitive data reaches the client.
**Validates: Requirements 5.2**

## Error Handling

### Anonymous User Error Scenarios
1. **API Rate Limiting**: Anonymous users hitting rate limits receive appropriate HTTP 429 responses
2. **Invalid Date Parameters**: Same validation and error responses as authenticated users
3. **System Unavailability**: Graceful degradation with appropriate error messages

### Security Error Handling
1. **Data Leakage Prevention**: Server-side filtering ensures no sensitive data reaches anonymous users even in error conditions
2. **Authentication Bypass Attempts**: Proper validation prevents unauthorized access to authenticated-only features

## Testing Strategy

### Unit Testing
- Test data filtering service with various reservation and block scenarios
- Test route handlers for both anonymous and authenticated access
- Test template rendering with different authentication states
- Test error handling for anonymous user scenarios

### Property-Based Testing
Property-based tests will validate the correctness properties using a Python testing framework (pytest with Hypothesis):

**Configuration**: Each property test runs minimum 100 iterations to ensure comprehensive coverage.

**Test Tags**: Each test references its corresponding design property:
- **Feature: anonymous-court-overview, Property 1**: Anonymous Data Privacy
- **Feature: anonymous-court-overview, Property 2**: Block Information Consistency  
- **Feature: anonymous-court-overview, Property 3**: Availability Data Accuracy
- **Feature: anonymous-court-overview, Property 4**: Navigation Functionality Parity
- **Feature: anonymous-court-overview, Property 5**: Read-Only Interface Enforcement
- **Feature: anonymous-court-overview, Property 6**: Authentication State Consistency

### Integration Testing
- End-to-end testing of anonymous user workflows
- Cross-browser testing for anonymous interface
- Performance testing under anonymous user load
- Security testing to verify no data leakage

### Testing Approach
The testing strategy employs both unit tests for specific examples and edge cases, and property-based tests for universal correctness validation. Unit tests focus on concrete scenarios like specific reservation filtering cases, while property tests verify that data filtering works correctly across all possible input combinations. Together, these approaches provide comprehensive coverage ensuring both functional correctness and security compliance.