# Spec-Driven Development Quick Start Guide

This guide walks you through creating a new feature spec from scratch.

## Overview

Spec-driven development follows three phases:

1. **Requirements**: What the system should do (EARS format)
2. **Design**: How it will work (architecture + correctness properties)
3. **Tasks**: Step-by-step implementation plan

## Step-by-Step Process

### Phase 1: Requirements Gathering (30-60 minutes)

#### 1.1 Create the Spec Directory

```bash
mkdir -p .kiro/specs/{feature-name}
cd .kiro/specs/{feature-name}
touch requirements.md design.md tasks.md
```

#### 1.2 Write the Introduction

In `requirements.md`:

```markdown
# Requirements Document

## Introduction

[2-3 paragraphs explaining:]
- What problem does this solve?
- Who are the users?
- What's the business context?
```

#### 1.3 Build the Glossary

List every technical term you'll use:

```markdown
## Glossary

- **System**: The tennis club reservation application
- **Member**: A registered user who can book courts
- **Court**: One of six tennis courts numbered 1-6
- **Reservation**: A booking linking a court, time, and member
```

**Tip**: If you capitalize it in acceptance criteria, define it here.

#### 1.4 Write User Stories

For each major feature area:

```markdown
### Requirement 1: [Feature Name]

**User Story:** As a [role], I want to [action], so that [benefit].

**Business Context:** [Optional: Why this matters, constraints, rules]
```

#### 1.5 Write Acceptance Criteria

Use EARS patterns:

```markdown
#### Acceptance Criteria

**Functional:**
1. WHEN [trigger], THE System SHALL [response]

**Data:**
2. WHEN [action], THE System SHALL store [fields]

**Validation:**
3. WHEN [invalid input], THE System SHALL reject with error [code]

**Integration:**
4. WHEN [action], THE System SHALL send [notification]

**Edge Cases:**
5. WHEN [edge case], THE System SHALL [behavior]
```

**Checklist for each criterion:**
- [ ] Follows EARS pattern (WHEN/WHERE/WHILE/IF/THE/SHALL)
- [ ] Uses active voice
- [ ] Uses terms from glossary
- [ ] Is specific and measurable
- [ ] Focuses on WHAT, not HOW

#### 1.6 Review with User

Ask: "Do the requirements look good? If so, we can move on to the design."

Iterate until approved.

---

### Phase 2: Design (60-90 minutes)

#### 2.1 Write Overview

In `design.md`:

```markdown
# Design Document

## Overview

[2-3 paragraphs covering:]
- High-level approach
- Key architectural decisions
- Technology choices
```

#### 2.2 Create Architecture Diagram

```markdown
## Architecture

```
[ASCII or Mermaid diagram showing:]
- Components
- Data flow
- External systems
```
```

#### 2.3 Define System Invariants

```markdown
## System Invariants

1. **[Invariant Name]**: [What must always be true]
2. **[Invariant Name]**: [What must always be true]
```

**Examples:**
- "A court can have at most one active reservation per time slot"
- "All reservation times are on hour boundaries"

#### 2.4 Define State Machines (if applicable)

```markdown
## State Machines

### Reservation State Machine

```
pending → active → completed
            ↓
        cancelled
```

**Valid Transitions:**
- pending → active: When time slot begins
- active → completed: When time slot ends
- active → cancelled: When user cancels
```

#### 2.5 Document Models, Services, and Routes

```markdown
## Components and Interfaces

### Models
[Data structures]

### Services
[Business logic]

### Routes
[API endpoints with request/response schemas]
```

#### 2.6 Prework: Analyze Testability

For EACH acceptance criterion, analyze:

```markdown
## Correctness Properties

### Acceptance Criteria Testing Prework

1.1 [Criterion text]
Thoughts: [Can this be tested? How? Is it a property, example, or edge case?]
Testable: yes - property | yes - example | yes - edge case | no

1.2 [Criterion text]
Thoughts: [Analysis]
Testable: [classification]
```

#### 2.7 Property Reflection

Look for redundancies:

```markdown
### Property Reflection

**Redundancies Found:**
- Property X and Y both test [same thing]
- Property Z is subsumed by Property W

**Consolidation:**
- Combine X and Y into comprehensive property
- Remove Z
```

#### 2.8 Write Correctness Properties

```markdown
### Correctness Properties

Property 1: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**

Property 2: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**
```

**Checklist for each property:**
- [ ] Starts with "For any..."
- [ ] Universal quantification is explicit
- [ ] References specific requirements
- [ ] Is testable with property-based testing
- [ ] Not redundant with other properties

#### 2.9 Document Testing Strategy

```markdown
## Testing Strategy

### Unit Tests
[What to unit test]

### Property-Based Tests
- Library: [Hypothesis/QuickCheck/fast-check]
- Minimum iterations: 100
- Test data strategies: [How to generate test data]

### Integration Tests
[End-to-end scenarios]
```

#### 2.10 Review with User

Ask: "Does the design look good? If so, we can move on to the implementation plan."

Iterate until approved.

---

### Phase 3: Implementation Plan (30-45 minutes)

#### 3.1 Break Down into Tasks

In `tasks.md`:

```markdown
# Implementation Plan

- [ ] 1. [Setup/Infrastructure]
  - [Specific action]
  - _Requirements: X.Y_

- [ ] 2. [Core Implementation]
  - [ ] 2.1 [Specific coding task]
    - [Detail]
    - [Detail]
    - _Requirements: X.Y_
  
  - [ ]* 2.2 Write property test
    - **Property N: [Property text]**
    - **Validates: Requirements X.Y**

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
```

**Task Ordering:**
1. Models (data structures)
2. Services (business logic)
3. Routes (API)
4. UI (frontend)
5. Integration (wire together)

**Property Test Placement:**
- Place immediately after implementing the functionality
- Mark as optional with `*`
- Reference property number from design doc

#### 3.2 Review with User

Ask: "Does the task list look good? Should tests be optional or required?"

Options:
- Keep optional tasks (faster MVP)
- Make all tasks required (comprehensive from start)

#### 3.3 Finalize

Once approved, the spec is complete!

---

## Quick Tips

### Requirements Phase

✅ **DO:**
- Define all terms in glossary
- Use EARS patterns consistently
- Specify error behavior explicitly
- Include edge cases
- Think about concurrency

❌ **DON'T:**
- Mix requirements and design
- Use vague terms ("quickly", "adequate")
- Forget error handling
- Assume implicit behavior

### Design Phase

✅ **DO:**
- Start with invariants
- Define state machines for stateful entities
- Analyze testability of every criterion
- Look for redundant properties
- Group properties by category

❌ **DON'T:**
- Skip prework analysis
- Write untestable properties
- Forget compensation logic
- Ignore timezone handling

### Tasks Phase

✅ **DO:**
- Order tasks to validate core functionality early
- Place property tests after implementation
- Add checkpoints after milestones
- Reference specific requirements

❌ **DON'T:**
- Include non-coding tasks (deployment, user testing)
- Create orphaned code
- Skip property tests entirely
- Forget to wire components together

---

## Example: Simple Feature

Let's walk through a simple example: "Add a search bar to find members by name"

### Requirements (10 minutes)

```markdown
# Requirements Document

## Introduction

Add a search feature to help members quickly find other members by name when adding them to favourites.

## Glossary

- **System**: The tennis club application
- **Member**: A registered user
- **Search Query**: Text input to find members

## Requirements

### Requirement 1: Member Search

**User Story:** As a member, I want to search for other members by name, so that I can find them quickly.

#### Acceptance Criteria

1. WHEN a member enters a search query with at least 1 character, THE System SHALL return all members whose firstname or lastname contains the query text (case-insensitive)
2. WHEN a member submits an empty search query, THE System SHALL return an empty result set
3. WHEN displaying search results, THE System SHALL show each member's firstname, lastname, and email
4. WHEN a search query matches multiple members, THE System SHALL order results alphabetically by lastname then firstname
```

### Design (20 minutes)

```markdown
# Design Document

## Overview

Implement a simple search API endpoint that queries the member table using SQL LIKE with case-insensitive matching.

## Architecture

```
Browser → GET /api/members/search?q=query → Flask Route → MemberService → Database
```

## System Invariants

1. **Search is read-only**: Search never modifies data

## Components and Interfaces

### Routes

**GET /api/members/search**
- Query param: `q` (required, min 1 char)
- Response: `[{id, firstname, lastname, email}]`
- Errors: 400 if query missing

### Services

```python
class MemberService:
    def search_members(query: str) -> List[Member]:
        # Query where firstname LIKE %query% OR lastname LIKE %query%
        # Order by lastname, firstname
```

## Correctness Properties

### Prework

1.1 Search returns matching members
Thoughts: This is a universal rule - for any query, all results should match. Testable as property.
Testable: yes - property

1.2 Empty query returns empty results
Thoughts: This is a specific edge case.
Testable: yes - edge case

1.3 Results include required fields
Thoughts: For any result, it should have firstname, lastname, email. Property.
Testable: yes - property

1.4 Results are ordered
Thoughts: For any multi-result query, results should be sorted. Property.
Testable: yes - property

### Properties

Property 1: Search returns matching members
*For any* search query and member database, all returned results should have either firstname or lastname containing the query text (case-insensitive)
**Validates: Requirements 1.1**

Property 2: Search results include required fields
*For any* search result, it should contain firstname, lastname, and email
**Validates: Requirements 1.3**

Property 3: Search results are ordered
*For any* search query returning multiple results, results should be ordered by lastname then firstname
**Validates: Requirements 1.4**

## Testing Strategy

- **Unit Tests**: Test search_members() with various queries
- **Property Tests**: Use Hypothesis to generate random queries and member data
- **Integration Tests**: Test full API endpoint
```

### Tasks (15 minutes)

```markdown
# Implementation Plan

- [ ] 1. Implement search API
  - [ ] 1.1 Add GET /api/members/search route
    - Validate query parameter
    - Call MemberService.search_members()
    - Return JSON response
    - _Requirements: 1.1, 1.2_
  
  - [ ] 1.2 Implement MemberService.search_members()
    - Query with LIKE on firstname and lastname
    - Case-insensitive matching
    - Order by lastname, firstname
    - _Requirements: 1.1, 1.4_
  
  - [ ]* 1.3 Write property test for matching
    - **Property 1: Search returns matching members**
    - **Validates: Requirements 1.1**
  
  - [ ]* 1.4 Write property test for fields
    - **Property 2: Search results include required fields**
    - **Validates: Requirements 1.3**
  
  - [ ]* 1.5 Write property test for ordering
    - **Property 3: Search results are ordered**
    - **Validates: Requirements 1.4**

- [ ] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
```

---

## Time Estimates

| Phase | Simple Feature | Medium Feature | Complex Feature |
|-------|---------------|----------------|-----------------|
| Requirements | 15-30 min | 30-60 min | 1-2 hours |
| Design | 30-45 min | 60-90 min | 2-4 hours |
| Tasks | 15-30 min | 30-45 min | 1-2 hours |
| **Total** | **1-2 hours** | **2-3 hours** | **4-8 hours** |

**Note**: This is spec creation time, not implementation time!

---

## Common Questions

### Q: Do I need to write specs for every feature?

**A**: For complex features with business logic, yes. For simple UI tweaks, probably not.

### Q: Can I skip the prework analysis?

**A**: No! Prework helps you think through testability and catch issues early.

### Q: Should all property tests be required?

**A**: For MVP, mark them optional (`*`). For production, make them required.

### Q: What if requirements change during implementation?

**A**: Update the spec! Keep requirements, design, and tasks in sync.

### Q: How detailed should tasks be?

**A**: Detailed enough that someone else could implement them. Include specific methods, fields, and requirements references.

---

## Next Steps

1. **Read**: [SPEC_BEST_PRACTICES.md](./SPEC_BEST_PRACTICES.md) for detailed guidance
2. **Reference**: [SPEC_TEMPLATE.md](./SPEC_TEMPLATE.md) when creating new specs
3. **Practice**: Try creating a spec for a small feature
4. **Iterate**: Specs improve with practice!

---

## Getting Help

If you're stuck:

1. **Requirements unclear?** → Add more acceptance criteria, define more terms
2. **Can't write properties?** → Review prework, look for property patterns
3. **Tasks too vague?** → Break down further, add more details
4. **Tests failing?** → Check if requirements match implementation

Remember: Good specs lead to correct code. Take time to get them right!
