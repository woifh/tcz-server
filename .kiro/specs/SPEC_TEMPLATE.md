# Feature Spec Template

This template incorporates best practices for creating comprehensive, testable feature specifications.

## Directory Structure

```
.kiro/specs/{feature-name}/
├── requirements.md    # EARS-compliant requirements
├── design.md         # Architecture and correctness properties
└── tasks.md          # Implementation plan
```

---

# requirements.md Template

```markdown
# Requirements Document

## Introduction

[1-2 paragraph summary of the feature/system. Include the business problem being solved and the target users.]

## Glossary

Define ALL technical terms and system names used in requirements. Every capitalized term in acceptance criteria should be defined here.

- **System**: [The application/system name]
- **[Entity]**: [Definition with key attributes]
- **[Action]**: [Definition of what this means]
- **[State]**: [Definition of this state]

## Requirements

### Requirement 1: [Category] - [Short Name]

**User Story:** As a [role], I want to [action], so that [benefit].

**Business Context:** [Optional: Why this requirement exists, business rules, constraints]

#### Acceptance Criteria

**Functional Criteria:**
1. WHEN [trigger], THE System SHALL [response]
2. WHERE [optional feature], THE System SHALL [response]
3. WHILE [state], THE System SHALL [response]

**Data Criteria:**
4. WHEN [action], THE System SHALL store [fields] with [constraints]
5. THE System SHALL validate [field] against [rules]

**Integration Criteria:**
6. WHEN [action], THE System SHALL send [notification/message] to [recipient]

**Error Handling:**
7. WHEN [invalid input], THE System SHALL reject with error [code/message]
8. WHEN [constraint violation], THE System SHALL [rollback/compensate]

**Edge Cases:**
9. WHEN [edge case scenario], THE System SHALL [expected behavior]

---

## Requirement Categories to Consider

### Core Functional Requirements
- Create/Read/Update/Delete operations
- Business rule enforcement
- State transitions

### Data Requirements
- What gets stored
- Data validation rules
- Data retention policies

### Integration Requirements
- External system calls
- Email/notification sending
- API contracts

### Security Requirements
- Authentication
- Authorization
- Data protection

### Performance Requirements
- Response time constraints
- Throughput requirements
- Scalability targets

### UI/UX Requirements
- User feedback mechanisms
- Responsive design
- Accessibility

### Error Handling Requirements
- Validation errors
- System errors
- Compensation logic

### Non-Functional Requirements
- Availability targets
- Data backup/recovery
- Monitoring/logging
```

---

# design.md Template

```markdown
# Design Document

## Overview

[2-3 paragraph summary of the design approach, key architectural decisions, and technology choices.]

## Architecture

### System Architecture Diagram

```
[Include ASCII or Mermaid diagram showing components and data flow]
```

### Technology Stack

- **Backend**: [Framework + version]
- **Database**: [Database + version]
- **Frontend**: [Framework/library + version]
- **Testing**: [Testing frameworks]
- **Deployment**: [Platform]

### Key Architectural Decisions

1. **[Decision Name]**
   - **Context**: [Why this decision was needed]
   - **Decision**: [What was decided]
   - **Rationale**: [Why this approach]
   - **Alternatives Considered**: [Other options and why rejected]

## System Invariants

These properties must ALWAYS be true, regardless of operations:

1. **[Invariant Name]**: [Description]
   - Example: "A court can have at most one active reservation per time slot"
   
2. **[Invariant Name]**: [Description]
   - Example: "All reservation times are on hour boundaries (00 minutes)"

## State Machines

### [Entity] State Machine

```
[Initial State] → [State 1] → [State 2] → [Final State]
                      ↓
                  [Error State]
```

**Valid Transitions:**
- `[State A] → [State B]`: Triggered by [action], requires [conditions]
- `[State B] → [State C]`: Triggered by [action], requires [conditions]

**Invalid Transitions:**
- `[State A] → [State C]`: Not allowed because [reason]

## Components and Interfaces

### Models (Data Layer)

#### [Entity] Model
```python
class Entity:
    # Fields
    id: int (primary key)
    field1: type (constraints)
    field2: type (constraints)
    
    # Relationships
    related_entities: List[RelatedEntity]
    
    # Computed Properties
    @property
    computed_field: type
    
    # Methods
    def method_name(params) -> return_type
```

**Validation Rules:**
- field1: [validation rules]
- field2: [validation rules]

### Services (Business Logic Layer)

#### [Service] Service
```python
class ServiceName:
    def operation_name(params) -> return_type
        """
        Purpose: [What this does]
        
        Preconditions:
        - [Condition that must be true before calling]
        
        Postconditions:
        - [Condition that will be true after calling]
        
        Side Effects:
        - [Database changes]
        - [External calls]
        - [Notifications sent]
        
        Error Cases:
        - Raises [ErrorType] when [condition]
        """
```

### Routes (API Layer)

#### [Resource] Routes

**Endpoint**: `[METHOD] /path`

**Authentication**: Required/Optional/None

**Authorization**: [Who can access]

**Request:**
```json
{
  "field": "type (constraints)"
}
```

**Response (Success):**
```json
{
  "field": "type"
}
```

**Response (Error):**
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message"
}
```

**Error Codes:**
- `ERROR_CODE_1`: [When this occurs]
- `ERROR_CODE_2`: [When this occurs]

## Data Models

### Database Schema

```sql
CREATE TABLE entity (
    id INT PRIMARY KEY,
    field1 TYPE CONSTRAINTS,
    field2 TYPE CONSTRAINTS,
    INDEX idx_field1 (field1),
    CONSTRAINT constraint_name CHECK (condition)
);
```

**Indexes:**
- `idx_field1`: For [query pattern]
- `idx_field2`: For [query pattern]

**Constraints:**
- `constraint_name`: Ensures [business rule]

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptance Criteria Testing Prework

[For each acceptance criterion, analyze testability]

X.Y [Criterion text]
Thoughts: [Step-by-step analysis of whether this is testable and how]
Testable: yes - property | yes - example | yes - edge case | no

### Property Reflection

[After prework, identify redundancies]

**Redundancies Found:**
- Property X and Property Y both test [same thing]
- Property Z is subsumed by Property W

**Consolidation Plan:**
- Combine X and Y into comprehensive property
- Remove Z as redundant

### Correctness Properties by Category

#### Data Integrity Properties

Property 1: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**

#### Business Rule Properties

Property 2: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**

#### Authorization Properties

Property 3: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**

#### Integration Properties

Property 4: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**

#### UI/UX Properties

Property 5: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**

## Error Handling

### Error Categories

1. **Validation Errors**
   - User input doesn't meet constraints
   - Response: 400 Bad Request with specific error
   - Example: "Email format invalid"

2. **Authorization Errors**
   - User lacks permission
   - Response: 403 Forbidden
   - Example: "Only administrators can delete members"

3. **Resource Not Found**
   - Requested resource doesn't exist
   - Response: 404 Not Found
   - Example: "Reservation not found"

4. **Conflict Errors**
   - Operation violates business rules
   - Response: 409 Conflict
   - Example: "Time slot already reserved"

5. **System Errors**
   - Database failures, external service failures
   - Response: 500 Internal Server Error
   - Action: Log error, rollback transaction
   - Example: "Database connection failed"

### Compensation Logic

**Operation**: [Operation name]
**Failure Point**: [Where it can fail]
**Compensation**: [How to rollback/compensate]

Example:
- Operation: Create reservation with email notification
- Failure Point: Email sending fails after reservation created
- Compensation: Log failure, complete reservation, retry email async

## Testing Strategy

### Unit Tests

Test individual functions and methods in isolation.

**Coverage:**
- All service methods
- All validation functions
- All model methods

**Example Tests:**
- `test_validate_booking_time_accepts_valid_times()`
- `test_validate_booking_time_rejects_invalid_times()`

### Property-Based Tests

Using **[Hypothesis/QuickCheck/fast-check]** library.

**Configuration:**
- Minimum 100 iterations per property
- Custom strategies for domain objects

**Test Data Strategies:**
```python
# Generate valid entities
entity_strategy = st.fixed_dictionaries({
    'field1': st.integers(min=1, max=100),
    'field2': st.text(min_size=1, max_size=50)
})
```

**Property Test Format:**
```python
@given(entity=entity_strategy)
def test_property_name(entity):
    """
    Feature: {feature-name}, Property {number}: {property-text}
    Validates: Requirements X.Y
    """
    # Arrange
    # Act
    result = operation(entity)
    # Assert
    assert expected_property(result)
```

### Integration Tests

Test complete workflows end-to-end.

**Test Scenarios:**
1. Happy path: [Description]
2. Error path: [Description]
3. Edge case: [Description]

### Performance Tests

**Targets:**
- [Operation]: < [time] for [percentile]
- [Query]: < [time] for [data size]

## Security Considerations

1. **Authentication**: [How users are authenticated]
2. **Authorization**: [How permissions are checked]
3. **Data Protection**: [How sensitive data is protected]
4. **Input Validation**: [How inputs are sanitized]
5. **SQL Injection Prevention**: [ORM usage, parameterized queries]
6. **XSS Prevention**: [Output escaping, CSP]

## Performance Optimizations

1. **Database Indexes**: [Which indexes and why]
2. **Caching**: [What is cached and for how long]
3. **Query Optimization**: [N+1 prevention, eager loading]
4. **Async Operations**: [What runs asynchronously]

## Deployment Considerations

### Environment Variables

```
REQUIRED_VAR=description
OPTIONAL_VAR=description (default: value)
```

### Database Migrations

Migration strategy: [How schema changes are handled]

### Monitoring

**Metrics to Track:**
- [Metric 1]: [Why important]
- [Metric 2]: [Why important]

**Alerts:**
- [Alert condition]: [Action to take]

## Future Enhancements

[Optional features or improvements to consider later]

1. **[Enhancement Name]**
   - Description: [What it would do]
   - Benefit: [Why it would be valuable]
   - Complexity: [Effort estimate]
```

---

# tasks.md Template

```markdown
# Implementation Plan

## Overview

This plan breaks down the feature into discrete, testable implementation steps. Each task builds incrementally on previous tasks.

## Task Structure Rules

- Top-level tasks are major implementation milestones
- Sub-tasks are specific coding activities
- Property-based tests are marked with `*` as optional
- Each task references specific requirements
- Tasks are ordered to validate core functionality early

---

- [ ] 1. [Setup/Infrastructure Task]
  - [Specific action 1]
  - [Specific action 2]
  - _Requirements: X.Y_

- [ ] 2. [Core Model Implementation]
  - [ ] 2.1 Create [Entity] model
    - Implement fields: [list fields]
    - Add validation: [list validations]
    - Add relationships: [list relationships]
    - _Requirements: X.Y_
  
  - [ ]* 2.2 Write property test for [property name]
    - **Property N: [Property text]**
    - **Validates: Requirements X.Y**

- [ ] 3. [Service Layer Implementation]
  - [ ] 3.1 Create [Service] class
    - Implement [method1]() with [behavior]
    - Implement [method2]() with [behavior]
    - Add transaction management
    - Add error handling
    - _Requirements: X.Y_
  
  - [ ]* 3.2 Write property test for [property name]
    - **Property N: [Property text]**
    - **Validates: Requirements X.Y**

- [ ] 4. [API/Routes Implementation]
  - [ ] 4.1 Create [resource] routes
    - Implement GET /path
    - Implement POST /path
    - Add authentication checks
    - Add authorization checks
    - _Requirements: X.Y_
  
  - [ ]* 4.2 Write property test for [property name]
    - **Property N: [Property text]**
    - **Validates: Requirements X.Y**

- [ ] 5. [Frontend/UI Implementation]
  - [ ] 5.1 Create [component] template
    - Add [UI element]
    - Add [interaction]
    - Add responsive design
    - _Requirements: X.Y_
  
  - [ ]* 5.2 Write property test for [property name]
    - **Property N: [Property text]**
    - **Validates: Requirements X.Y**

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. [Integration Task]
  - [ ] 7.1 Wire components together
    - Connect [component A] to [component B]
    - Add error handling
    - _Requirements: X.Y_

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Task Ordering Principles

1. **Models First**: Data structures before logic
2. **Services Second**: Business logic before API
3. **Routes Third**: API before UI
4. **UI Fourth**: Interface after backend is solid
5. **Integration Last**: Wire everything together

## Property Test Placement

- Place property tests immediately after implementing the functionality they test
- This enables early bug detection
- Mark as optional (`*`) to allow MVP without full test coverage

## Checkpoint Strategy

- Add checkpoints after major milestones
- Checkpoints ensure all tests pass before proceeding
- Prevents accumulating technical debt
```

---

Now let me create the best practices guide:

<function_calls>
<invoke name="fsWrite">
<parameter name="path">.kiro/specs/SPEC_BEST_PRACTICES.md