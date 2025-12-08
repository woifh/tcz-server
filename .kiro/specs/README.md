# Feature Specifications

This directory contains feature specifications for the Tennis Club Reservation System, along with templates and best practices for creating new specs.

## Directory Structure

```
.kiro/specs/
├── README.md                      # This file
├── QUICK_START_GUIDE.md          # Step-by-step guide for creating specs
├── SPEC_TEMPLATE.md              # Template for new feature specs
├── SPEC_BEST_PRACTICES.md        # Detailed best practices and patterns
├── tennis-club-reservation/      # Main application spec
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
└── member-search/                # Member search feature spec
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

## What is Spec-Driven Development?

Spec-driven development is a methodology for building software by:

1. **Requirements**: Defining what the system should do using EARS (Easy Approach to Requirements Syntax)
2. **Design**: Specifying how it will work with architecture and correctness properties
3. **Tasks**: Creating an implementation plan with property-based tests

This approach ensures:
- ✅ Clear requirements that everyone understands
- ✅ Testable correctness properties
- ✅ Comprehensive test coverage
- ✅ Traceability from requirements to code
- ✅ Fewer bugs and rework

## Quick Start

**New to specs?** Start here:

1. Read [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md) (15 minutes)
2. Review an existing spec: [member-search/](./member-search/)
3. Use [SPEC_TEMPLATE.md](./SPEC_TEMPLATE.md) to create your first spec

**Creating a new spec?**

```bash
# 1. Create directory
mkdir -p .kiro/specs/{feature-name}

# 2. Copy template
cp .kiro/specs/SPEC_TEMPLATE.md .kiro/specs/{feature-name}/requirements.md

# 3. Follow the workflow in QUICK_START_GUIDE.md
```

## Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md) | Step-by-step walkthrough | Creating your first spec |
| [SPEC_TEMPLATE.md](./SPEC_TEMPLATE.md) | Copy-paste template | Starting a new spec |
| [SPEC_BEST_PRACTICES.md](./SPEC_BEST_PRACTICES.md) | Detailed guidance | Deep dive into patterns |

## Existing Specs

### Tennis Club Reservation System

**Status**: ✅ Complete and implemented

The main application spec covering:
- Member management
- Court reservations
- Admin functions
- Email notifications
- German localization

**Files**:
- [requirements.md](./tennis-club-reservation/requirements.md) - 17 requirements with 80+ acceptance criteria
- [design.md](./tennis-club-reservation/design.md) - Architecture with 39 correctness properties
- [tasks.md](./tennis-club-reservation/tasks.md) - 29 implementation tasks

**Key Features**:
- Property-based testing with Hypothesis
- EARS-compliant requirements
- Comprehensive error handling
- Timezone handling (UTC storage, Europe/Berlin display)
- Email failure resilience

### Member Search

**Status**: ✅ Complete and implemented

Search functionality for finding members to add to favourites.

**Files**:
- [requirements.md](./member-search/requirements.md) - 6 requirements
- [design.md](./member-search/design.md) - 14 correctness properties
- [tasks.md](./member-search/tasks.md) - 11 implementation tasks

**Key Features**:
- Real-time search with debouncing
- Case-insensitive matching on firstname, lastname, email
- Alphabetical ordering
- Excludes self and existing favourites

## Spec Workflow

### Phase 1: Requirements (30-60 min)

1. Write introduction and glossary
2. Create user stories
3. Write acceptance criteria using EARS patterns
4. Review with stakeholders

**Output**: `requirements.md`

### Phase 2: Design (60-90 min)

1. Create architecture diagram
2. Define system invariants
3. Document models, services, routes
4. Analyze testability (prework)
5. Write correctness properties
6. Define testing strategy

**Output**: `design.md`

### Phase 3: Tasks (30-45 min)

1. Break design into implementation tasks
2. Order tasks to validate core functionality early
3. Add property tests after each implementation
4. Add checkpoints

**Output**: `tasks.md`

### Phase 4: Implementation

Execute tasks from `tasks.md`:
1. Implement functionality
2. Write property-based tests
3. Run tests
4. Iterate until all tests pass

## Key Concepts

### EARS Patterns

Every acceptance criterion follows one of these patterns:

- **Ubiquitous**: `THE System SHALL [response]`
- **Event-driven**: `WHEN [trigger], THE System SHALL [response]`
- **State-driven**: `WHILE [condition], THE System SHALL [response]`
- **Unwanted event**: `IF [condition], THEN THE System SHALL [response]`
- **Optional feature**: `WHERE [option], THE System SHALL [response]`

### Correctness Properties

Universal statements about system behavior:

```
Property: [Name]
*For any* [input space], [expected behavior]
**Validates: Requirements X.Y**
```

Properties are tested using property-based testing (Hypothesis for Python).

### Property-Based Testing

Instead of testing specific examples:
```python
def test_sort():
    assert sort([3, 1, 2]) == [1, 2, 3]  # One example
```

Test universal properties:
```python
@given(st.lists(st.integers()))
def test_sort_preserves_length(lst):
    assert len(sort(lst)) == len(lst)  # All lists
```

## Best Practices

### Requirements

✅ **DO:**
- Define all terms in glossary
- Use EARS patterns consistently
- Specify error behavior explicitly
- Include edge cases
- Think about concurrency

❌ **DON'T:**
- Mix requirements and design
- Use vague terms
- Forget error handling
- Assume implicit behavior

### Design

✅ **DO:**
- Start with invariants
- Define state machines
- Analyze testability (prework)
- Look for redundant properties
- Document compensation logic

❌ **DON'T:**
- Skip prework analysis
- Write untestable properties
- Forget timezone handling
- Ignore concurrency

### Tasks

✅ **DO:**
- Order to validate core functionality early
- Place property tests after implementation
- Add checkpoints after milestones
- Reference specific requirements

❌ **DON'T:**
- Include non-coding tasks
- Create orphaned code
- Skip property tests
- Forget to wire components together

## Examples

### Good Requirement

```markdown
WHEN a member with fewer than 2 active reservations selects an available court and time slot during operating hours, THE System SHALL create a reservation linking the court, date, time, booked_for member, and booked_by member
```

### Good Property

```markdown
Property 1: Reservation creation stores all required fields
*For any* valid court (1-6), date (future), time (06:00-21:00 on hour boundary), booked_for member, and booked_by member, creating a reservation should result in a database record containing all five fields with correct values and status='active'
**Validates: Requirements 1.1, 1.2**
```

### Good Task

```markdown
- [ ] 1.1 Create ReservationService class
  - Implement create_reservation() with validation
  - Add transaction management for atomicity
  - Convert times from Europe/Berlin to UTC before storing
  - _Requirements: 1.1, 1.2, 17.1, 17.3_

- [ ]* 1.2 Write property test for reservation field storage
  - **Property 1: Reservation creation stores all required fields**
  - **Validates: Requirements 1.1, 1.2**
```

## Property Patterns

Common patterns for correctness properties:

| Pattern | Example |
|---------|---------|
| **Round Trip** | `parse(print(ast)) == ast` |
| **Invariant** | `len(sort(list)) == len(list)` |
| **Idempotence** | `filter(filter(list)) == filter(list)` |
| **Metamorphic** | `len(filter(list)) <= len(list)` |
| **Model-Based** | `quicksort(list) == bubblesort(list)` |
| **Error Condition** | `validate(invalid_time) == False` |

## Testing Strategy

### Unit Tests

Test specific examples and edge cases:
- Valid inputs produce expected outputs
- Invalid inputs are rejected
- Edge cases (empty, boundary values)

### Property-Based Tests

Test universal properties across many inputs:
- Generate random valid inputs
- Verify property holds for all inputs
- Minimum 100 iterations per property

### Integration Tests

Test complete workflows end-to-end:
- Happy path scenarios
- Error scenarios
- Multi-step workflows

## Tools and Libraries

- **Requirements**: EARS patterns, INCOSE quality rules
- **Property Testing**: Hypothesis (Python), QuickCheck (Haskell), fast-check (JavaScript)
- **Testing**: pytest, unittest
- **Documentation**: Markdown, Mermaid diagrams

## Lessons Learned

From reviewing and improving existing specs:

1. **Start with invariants** - They become your most important tests
2. **Define state machines** - Catches invalid transitions early
3. **Analyze testability** - Prework prevents untestable requirements
4. **Look for redundancies** - Property reflection eliminates duplicate tests
5. **Specify error behavior** - Don't just say "reject", say how and why
6. **Handle edge cases** - Empty inputs, boundaries, concurrency
7. **Document compensation** - What happens when operations partially fail
8. **Consider timezone** - Always specify storage and display timezones
9. **Group properties** - By category, not just numbered 1-N
10. **Place tests early** - After implementation, not at the end

## Contributing

When adding new specs:

1. Follow the template structure
2. Use EARS patterns for requirements
3. Complete prework analysis
4. Write testable properties
5. Reference specific requirements in tasks
6. Add property tests as optional (`*`)

## Resources

- [EARS Syntax Guide](https://alistairmavin.com/ears/)
- [INCOSE Requirements Quality](https://www.incose.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing](https://fsharpforfunandprofit.com/posts/property-based-testing/)

## Questions?

- **Stuck on requirements?** → See [SPEC_BEST_PRACTICES.md](./SPEC_BEST_PRACTICES.md) "Requirements Writing"
- **Can't write properties?** → See [SPEC_BEST_PRACTICES.md](./SPEC_BEST_PRACTICES.md) "Property-Based Testing"
- **Tasks too vague?** → See [SPEC_TEMPLATE.md](./SPEC_TEMPLATE.md) "tasks.md Template"
- **Need examples?** → Review [member-search/](./member-search/) or [tennis-club-reservation/](./tennis-club-reservation/)

## Version History

- **v2.0** (2025-12-08): Comprehensive improvements
  - Added timezone handling requirements
  - Added email failure resilience
  - Split toast notification properties
  - Added favourites edge cases
  - Created template and best practices docs
  
- **v1.0** (2025-12-01): Initial specs
  - Tennis club reservation system
  - Member search feature

---

**Remember**: Good specs lead to correct code. Take time to get them right!
