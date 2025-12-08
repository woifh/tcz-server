# Spec-Driven Development Best Practices

This guide captures lessons learned from creating and reviewing feature specifications.

## Table of Contents

1. [Requirements Writing](#requirements-writing)
2. [Design Principles](#design-principles)
3. [Property-Based Testing](#property-based-testing)
4. [Common Pitfalls](#common-pitfalls)
5. [Checklist](#checklist)

---

## Requirements Writing

### Use EARS Patterns Consistently

Every acceptance criterion must follow one of these patterns:

1. **Ubiquitous**: `THE System SHALL [response]`
2. **Event-driven**: `WHEN [trigger], THE System SHALL [response]`
3. **State-driven**: `WHILE [condition], THE System SHALL [response]`
4. **Unwanted event**: `IF [condition], THEN THE System SHALL [response]`
5. **Optional feature**: `WHERE [option], THE System SHALL [response]`
6. **Complex**: `[WHERE] [WHILE] [WHEN/IF] THE System SHALL [response]`

### INCOSE Quality Rules

✅ **DO:**
- Use active voice ("System SHALL create" not "Reservation is created")
- Be specific and measurable ("< 500ms" not "quickly")
- Use defined terms from glossary
- One requirement per statement
- Focus on WHAT, not HOW

❌ **DON'T:**
- Use vague terms ("adequate", "sufficient", "quickly")
- Use escape clauses ("where possible", "if feasible")
- Use negatives ("SHALL NOT" - rephrase positively)
- Use pronouns ("it", "them" - use specific terms)
- Use absolutes ("never", "always", "100%" - unless truly absolute)

### Organize by Business Events

Instead of organizing by CRUD operations:

❌ **Bad:**
```
Requirement 1: Create Reservation
Requirement 2: Update Reservation
Requirement 3: Delete Reservation
```

✅ **Good:**
```
Requirement 1: Member Books Court for Self
Requirement 2: Member Books Court for Partner
Requirement 3: Admin Cancels Reservation Due to Weather
```

### Separate Concerns

Group acceptance criteria by type:

```markdown
#### Acceptance Criteria

**Functional:**
1. WHEN [action], THE System SHALL [behavior]

**Data:**
2. WHEN [action], THE System SHALL store [fields]

**Integration:**
3. WHEN [action], THE System SHALL send [notification]

**Error Handling:**
4. WHEN [invalid input], THE System SHALL reject with [error]

**Edge Cases:**
5. WHEN [edge case], THE System SHALL [behavior]
```

### Specify Error Behavior Explicitly

❌ **Bad:**
```
WHEN a member attempts to book a reserved slot, THE System SHALL reject the booking
```

✅ **Good:**
```
WHEN a member attempts to book a reserved slot, THE System SHALL reject the booking with error code SLOT_ALREADY_RESERVED and display message "Dieser Zeitslot ist bereits gebucht"
```

### Include Edge Cases

Don't forget to specify:
- Empty inputs
- Boundary values
- Concurrent operations
- System failures
- Invalid states

### Define All Terms

Every capitalized term in acceptance criteria should be in the glossary:

```markdown
## Glossary

- **Active Reservation**: A future reservation that has not been cancelled or completed
- **Booking Slot**: A one-hour time period between 06:00 and 22:00
- **Booked For**: The member who will use the court
- **Booked By**: The member who created the reservation
```

---

## Design Principles

### Start with Invariants

Before writing properties, list what must ALWAYS be true:

```markdown
## System Invariants

1. **Unique Active Reservations**: A court can have at most one active reservation per time slot
2. **Time Boundaries**: All reservation times are on hour boundaries (00 minutes)
3. **Member Limit**: A member can have at most 2 active reservations
4. **Court Range**: Court numbers are always between 1 and 6
```

These become your most important property tests.

### Define State Machines

For entities with lifecycle, draw the state machine:

```
pending → active → completed
            ↓
        cancelled
```

Specify:
- Valid transitions
- Invalid transitions (and why)
- Triggers for each transition
- Preconditions for transitions

### Separate Read and Write Operations

**Commands** (change state):
- create_reservation()
- cancel_reservation()
- update_member()

**Queries** (read state):
- get_reservations_by_date()
- check_availability()
- list_members()

This makes it clear what has side effects.

### Specify API Contracts

Define request/response schemas in design doc:

```markdown
### POST /reservations

**Request:**
```json
{
  "court_id": 1,
  "date": "2025-12-15",
  "start_time": "14:00",
  "booked_for_id": 42
}
```

**Success Response (201):**
```json
{
  "id": 123,
  "status": "active",
  "created_at": "2025-12-08T10:30:00Z"
}
```

**Error Responses:**
- `400 INVALID_TIME`: Time not on hour boundary
- `409 SLOT_TAKEN`: Court already reserved
- `409 LIMIT_EXCEEDED`: Member has 2 active reservations
```

### Document Compensation Logic

For operations that can partially fail:

```markdown
**Operation**: Create reservation with email notification

**Failure Scenarios:**
1. Database fails: Rollback, return error
2. Email fails after DB commit: Complete operation, log failure, retry async

**Rationale**: Email failures shouldn't block bookings
```

### Group Properties by Category

Instead of numbering 1-39, organize:

```markdown
### Data Integrity Properties (1-5)
Property 1: Reservation stores all fields
Property 2: Member stores hashed password
...

### Business Rule Properties (6-12)
Property 6: Two-reservation limit enforced
Property 7: Time slots validated
...

### Authorization Properties (13-18)
Property 13: Only booked_for/booked_by can cancel
...
```

---

## Property-Based Testing

### Property Patterns

#### 1. Round Trip Properties

For serialization, parsing, encoding:

```
Property: Parse then print equals identity
For any valid AST, printing then parsing should return equivalent AST
```

#### 2. Invariant Properties

For transformations that preserve something:

```
Property: Sorting preserves length
For any list, sorting should return a list of the same length
```

#### 3. Idempotence Properties

For operations where doing twice = doing once:

```
Property: Applying filter twice equals applying once
For any list, filtering twice should equal filtering once
```

#### 4. Metamorphic Properties

When you know relationships without knowing exact values:

```
Property: Filtered list is shorter or equal
For any list and filter, len(filtered) <= len(original)
```

#### 5. Model-Based Properties

Compare optimized implementation to simple reference:

```
Property: Fast sort equals naive sort
For any list, quicksort(list) should equal bubblesort(list)
```

#### 6. Error Condition Properties

Generate invalid inputs:

```
Property: Invalid times are rejected
For any time outside 06:00-21:00, validation should return false
```

### Writing Good Properties

✅ **DO:**
- Start with "For any..."
- Make the universal quantification explicit
- Test one property per test
- Use descriptive names
- Reference the requirement being validated

❌ **DON'T:**
- Test specific examples (that's unit tests)
- Combine multiple properties in one test
- Use magic numbers without explanation
- Forget edge cases in generators

### Property Test Structure

```python
@given(entity=entity_strategy)
def test_property_name(entity):
    """
    Feature: {feature-name}, Property {number}: {property-text}
    Validates: Requirements X.Y
    
    For any valid entity, [property description]
    """
    # Arrange: Set up preconditions
    setup_database()
    
    # Act: Perform operation
    result = operation(entity)
    
    # Assert: Check property holds
    assert property_holds(result)
    
    # Cleanup
    teardown_database()
```

### Test Data Strategies

Create smart generators that constrain to valid input space:

```python
# Bad: Too broad, generates invalid data
member_strategy = st.text()

# Good: Constrained to valid members
member_strategy = st.fixed_dictionaries({
    'firstname': st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L',))),
    'lastname': st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L',))),
    'email': st.emails(),
    'role': st.sampled_from(['member', 'administrator'])
})
```

### Property Reflection

After writing prework, look for redundancies:

**Questions to ask:**
- Does Property A imply Property B?
- Can Properties C and D be combined?
- Is Property E testing the same thing as Property F on different data?

**Example:**
```
Property 1: Adding task increases length by 1
Property 2: Added task appears in list

Analysis: Property 2 implies Property 1 (if task is in list, length increased)
Decision: Keep Property 2, remove Property 1 as redundant
```

---

## Common Pitfalls

### 1. Mixing Requirements and Design

❌ **Bad (in requirements.md):**
```
THE System SHALL use SQLAlchemy ORM to query the database
```

✅ **Good (in requirements.md):**
```
THE System SHALL retrieve all members matching the search query
```

✅ **Good (in design.md):**
```
Implementation will use SQLAlchemy ORM with case-insensitive LIKE queries
```

### 2. Vague Error Handling

❌ **Bad:**
```
WHEN validation fails, THE System SHALL display an error
```

✅ **Good:**
```
WHEN validation fails, THE System SHALL display a toast notification with the specific validation error message in German that auto-dismisses after 5 seconds
```

### 3. Missing Edge Cases

Don't forget:
- Empty inputs
- Null/None values
- Boundary values (0, 1, max)
- Concurrent operations
- System failures (DB down, email fails)
- Invalid state transitions

### 4. Untestable Requirements

❌ **Bad:**
```
THE System SHALL provide an intuitive user interface
```

✅ **Good:**
```
WHEN a user clicks a button, THE System SHALL provide visual feedback within 100ms
```

### 5. Implicit Assumptions

❌ **Bad:**
```
WHEN a member books a court, THE System SHALL create a reservation
```

✅ **Good:**
```
WHEN a member with fewer than 2 active reservations books an available court during operating hours, THE System SHALL create a reservation
```

### 6. Forgetting Timezone Handling

Always specify:
- What timezone times are stored in (usually UTC)
- What timezone times are displayed in
- How conversions happen

### 7. Ignoring Concurrency

What happens when two users do the same thing simultaneously?

```markdown
WHEN two members attempt to book the same slot concurrently, THE System SHALL use database-level locking to ensure only one succeeds and the other receives a SLOT_TAKEN error
```

### 8. Not Specifying Data Retention

```markdown
WHEN a reservation is cancelled, THE System SHALL mark it as cancelled and retain the record for 90 days for audit purposes
```

### 9. Unclear Authorization Rules

❌ **Bad:**
```
Only authorized users can delete reservations
```

✅ **Good:**
```
WHEN a member is the booked_for member OR the booked_by member, THE System SHALL allow that member to delete the reservation
AND
WHEN a member is an administrator, THE System SHALL allow that member to delete any reservation
```

### 10. Missing Compensation Logic

```markdown
WHEN email sending fails after reservation creation, THE System SHALL:
1. Complete the reservation successfully
2. Log the email failure with reservation ID and recipient
3. Queue the email for retry with exponential backoff
4. NOT display an error to the user
```

---

## Checklist

### Requirements Document

- [ ] Introduction explains the business problem
- [ ] Glossary defines all technical terms
- [ ] All acceptance criteria follow EARS patterns
- [ ] All acceptance criteria follow INCOSE quality rules
- [ ] Requirements organized by business events, not CRUD
- [ ] Error handling specified explicitly
- [ ] Edge cases included
- [ ] Concurrency behavior specified
- [ ] Timezone handling specified
- [ ] Data retention specified
- [ ] Authorization rules clear and complete

### Design Document

- [ ] Architecture diagram included
- [ ] Technology stack specified with versions
- [ ] System invariants listed
- [ ] State machines defined for stateful entities
- [ ] API contracts specified (request/response/errors)
- [ ] Database schema with indexes and constraints
- [ ] Compensation logic documented
- [ ] Prework analysis completed for all acceptance criteria
- [ ] Property reflection performed to eliminate redundancies
- [ ] Properties grouped by category
- [ ] Each property references specific requirements
- [ ] Test data strategies defined
- [ ] Security considerations addressed
- [ ] Performance optimizations documented
- [ ] Deployment considerations included

### Tasks Document

- [ ] Tasks ordered to validate core functionality early
- [ ] Each task is a discrete coding activity
- [ ] Each task references specific requirements
- [ ] Property tests marked as optional with `*`
- [ ] Property tests placed immediately after implementation
- [ ] Each property test references design doc property number
- [ ] Checkpoints included after major milestones
- [ ] No tasks for non-coding activities (deployment, user testing)
- [ ] Tasks build incrementally on previous tasks
- [ ] No orphaned code (everything wired together)

### Property Tests

- [ ] Each property starts with "For any..."
- [ ] Universal quantification is explicit
- [ ] Property name is descriptive
- [ ] Test includes feature name and property number in docstring
- [ ] Test references requirements being validated
- [ ] Test data generators constrain to valid input space
- [ ] Edge cases handled by generators
- [ ] Minimum 100 iterations configured
- [ ] No redundant properties (reflection completed)

---

## Examples of Good vs Bad

### Example 1: Booking Requirement

❌ **Bad:**
```markdown
### Requirement 1

**User Story:** As a member, I want to book courts.

#### Acceptance Criteria

1. Members can book courts
2. The system should prevent double bookings
3. Bookings should be saved
```

✅ **Good:**
```markdown
### Requirement 1: Court Reservation Creation

**User Story:** As a club member, I want to create court reservations for myself or other members, so that I can secure playing time and coordinate with partners.

**Business Context:** Members can book up to 2 active reservations at a time to ensure fair access. Reservations are for 1-hour slots during operating hours (06:00-21:00).

#### Acceptance Criteria

**Functional:**
1. WHEN a member with fewer than 2 active reservations selects an available court and time slot during operating hours, THE System SHALL create a reservation linking the court, date, time, booked_for member, and booked_by member

**Data:**
2. WHEN a reservation is created, THE System SHALL store court_id, date, start_time, end_time, booked_for_id, booked_by_id, status='active', and created_at timestamp

**Validation:**
3. WHEN a member with 2 active reservations attempts to create another reservation, THE System SHALL reject with error code RESERVATION_LIMIT_EXCEEDED and message "Sie haben bereits 2 aktive Buchungen"

4. WHEN a member attempts to book a time slot that is already reserved, THE System SHALL reject with error code SLOT_ALREADY_RESERVED and message "Dieser Zeitslot ist bereits gebucht"

**Integration:**
5. WHEN a reservation is created, THE System SHALL send email notifications in German to both the booked_by member and the booked_for member within 5 seconds

**Concurrency:**
6. WHEN two members attempt to book the same slot concurrently, THE System SHALL use database-level locking to ensure only one succeeds
```

### Example 2: Property Definition

❌ **Bad:**
```markdown
Property 1: Reservations work correctly
Test that reservations are created properly
```

✅ **Good:**
```markdown
Property 1: Reservation creation stores all required fields
*For any* valid court (1-6), date (future), time (06:00-21:00 on hour boundary), booked_for member, and booked_by member, creating a reservation should result in a database record containing all five fields with correct values and status='active'
**Validates: Requirements 1.1, 1.2**
```

### Example 3: Task Definition

❌ **Bad:**
```markdown
- [ ] 1. Implement reservations
  - Write code for reservations
  - Test it
```

✅ **Good:**
```markdown
- [ ] 1. Implement reservation service
  - [ ] 1.1 Create ReservationService class
    - Implement create_reservation() with validation
    - Implement cancel_reservation() with email sending
    - Add transaction management for atomicity
    - Add database-level locking for concurrency
    - Convert times from Europe/Berlin to UTC before storing
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 17.1, 17.3_
  
  - [ ]* 1.2 Write property test for reservation field storage
    - **Property 1: Reservation creation stores all required fields**
    - **Validates: Requirements 1.1, 1.2**
  
  - [ ]* 1.3 Write property test for two-reservation limit
    - **Property 2: Two-reservation limit enforcement**
    - **Validates: Requirements 1.3**
```

---

## Quick Reference

### EARS Pattern Cheat Sheet

| Pattern | Format | Example |
|---------|--------|---------|
| Ubiquitous | THE System SHALL [response] | THE System SHALL hash all passwords |
| Event-driven | WHEN [trigger], THE System SHALL [response] | WHEN a user logs in, THE System SHALL create a session |
| State-driven | WHILE [condition], THE System SHALL [response] | WHILE a room is muted, THE System SHALL prevent messages |
| Unwanted | IF [condition], THEN THE System SHALL [response] | IF login fails 3 times, THEN THE System SHALL lock the account |
| Optional | WHERE [option], THE System SHALL [response] | WHERE email is enabled, THE System SHALL send notifications |
| Complex | [WHERE] [WHILE] [WHEN/IF] THE System SHALL [response] | WHERE notifications are enabled, WHEN a booking is created, THE System SHALL send email |

### Property Pattern Cheat Sheet

| Pattern | Format | Example |
|---------|--------|---------|
| Round Trip | encode then decode = identity | parse(print(ast)) == ast |
| Invariant | transformation preserves property | len(sort(list)) == len(list) |
| Idempotence | f(x) == f(f(x)) | filter(filter(list)) == filter(list) |
| Metamorphic | relationship without exact value | len(filter(list)) <= len(list) |
| Model-Based | optimized == reference | quicksort(list) == bubblesort(list) |
| Error Condition | invalid input rejected | validate(invalid_time) == False |

---

## Conclusion

Good specs are:
- **Precise**: No ambiguity about what should happen
- **Testable**: Every requirement can be verified
- **Complete**: All edge cases and error conditions covered
- **Traceable**: Clear links from requirements → properties → tests
- **Maintainable**: Easy to update as requirements evolve

Follow these practices and your specs will guide you to correct, well-tested software.
