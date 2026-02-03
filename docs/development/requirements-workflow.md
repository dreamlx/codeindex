# Requirements & Planning Workflow

**Document**: Requirements Management and Planning Process for codeindex
**Created**: 2026-02-03
**For**: Development team and contributors
**Version**: 1.0

---

## Overview

codeindex uses a **dual-track system** for requirements management and planning:

1. **Planning Documents** (`docs/planning/*.md`) - Long-term vision, detailed design, version control
2. **GitHub Issues** - Execution tracking, collaboration, task management

This approach combines the benefits of both:
- Planning docs provide comprehensive design and context (version controlled)
- GitHub Issues enable collaboration, tracking, and automation

---

## Planning Documents (Long-term Vision)

### Location

All planning documents are stored in `docs/planning/`:

```
docs/planning/
├── ROADMAP.md                    # Strategic roadmap (1-2 years)
├── epic7-java-support.md         # Epic: Detailed design
├── story-7.1-java-parser.md      # Story: Implementation plan (optional)
└── v0.6.0-execution-plan.md      # Version: Release plan (optional)
```

### When to Create Planning Documents

| Document Type | When to Create | Purpose |
|---------------|----------------|---------|
| **ROADMAP.md** | Quarterly planning | Strategic direction, priorities, version targets |
| **Epic Plan** | Before starting large feature (2+ weeks) | Detailed design, user stories, technical approach, success criteria |
| **Story Plan** | For complex stories requiring detailed design | Implementation approach, technical decisions, dependencies |
| **Version Plan** | Before release planning | Feature bundling, timeline, resource allocation |

### Document Templates

#### ROADMAP.md Structure

```markdown
# codeindex Strategic Roadmap

**Last Updated**: YYYY-MM-DD
**Current Version**: vX.Y.Z
**Vision**: [One-line vision statement]

## Current Status (vX.Y.Z)
- Completed features
- Active work
- Known issues

## Version Roadmap
### vX.Y.0 - [Theme] (Target: YYYY-MM-DD)
- Key features
- Success criteria
- Technical debt

## Language/Framework Priority
- Ranking with rationale

## Strategic Decisions
- Why X first?
- Alternatives considered

## Success Metrics
- Technical metrics
- Adoption metrics
```

#### Epic Plan Structure

```markdown
# Epic N: [Name]

**Created**: YYYY-MM-DD
**Target Version**: vX.Y.0
**Priority**: P0/P1/P2
**Status**: 📋 Planned / 🔄 In Progress / ✅ Complete

## Overview
[Brief description of the epic]

## User Stories
- Story N.1: [description]
- Story N.2: [description]
- Story N.3: [description]

## Technical Approach
### Architecture
[How will this be implemented?]

### Dependencies
[What must exist first?]

### Risks
[What could go wrong?]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Testing Strategy
- Unit tests: N tests
- Integration tests: N tests
- E2E tests: N scenarios

## Documentation Requirements
- User guide: [topics]
- Developer guide: [topics]
- API reference: [modules]

## Timeline
- Week 1-2: [stories]
- Week 3-4: [stories]
- Week 5-6: [polish + release]
```

---

## GitHub Issues (Execution & Collaboration)

### When to Create GitHub Issues

| Issue Type | When to Create | Labels |
|------------|----------------|--------|
| **Epic Issue** | For each Epic in planning docs | `epic`, `priority:high/medium/low` |
| **Story/Feature Issue** | For each user story or feature | `feature`, milestone |
| **Enhancement Issue** | Improvements to existing features | `enhancement` |
| **Bug Issue** | For each discovered bug | `bug`, `priority:high/medium/low` |
| **Task Issue** | Optional, for tasks needing discussion | `task` |

### Recommended Labels

**Type Labels**:
- `epic` - Major feature (Epic 7: Java Support)
- `feature` - User-facing feature or story
- `enhancement` - Improvement to existing feature
- `bug` - Bug fix
- `documentation` - Documentation only
- `task` - Development task

**Priority Labels**:
- `priority:high` - Must have, blocking
- `priority:medium` - Should have, important
- `priority:low` - Nice to have, enhancement

**Status Labels** (optional):
- `status:planning` - Design phase
- `status:in-progress` - Active development
- `status:blocked` - Waiting on dependencies

### Recommended Milestones

Create milestones for each version:
- `v0.6.0 - Java Support`
- `v0.7.0 - Multi-language Support`
- `v0.8.0 - Framework Intelligence`
- `v1.0.0 - Production Ready`

### Issue Linking

**In Planning Documents**:
```markdown
## Related Issues
- Epic Issue: #1
- Story Issues: #2, #3, #4
```

**In GitHub Issues**:
```markdown
## Epic
Part of: #1 (Epic 7: Java Support)

## Planning Document
See: `docs/planning/epic7-java-support.md`
```

**In Commits**:
```bash
git commit -m "feat(parser): add Java parser

Implements basic Java parsing with tree-sitter.

Refs #2"
```

**In Pull Requests**:
```markdown
Closes #2
Closes #3

Part of Epic #1
```

---

## Complete Workflow

### 1. Strategic Planning (Quarterly)

**Goal**: Set direction for next 2-3 versions

**Activities**:
```bash
# Review current status
- What's completed?
- What's in progress?
- User feedback?

# Update ROADMAP.md
vim docs/planning/ROADMAP.md

# Define priorities
- Which features for next version?
- Which epics are P0/P1/P2?
- Resource allocation?

# Communicate
- Share roadmap with team
- Get stakeholder feedback
```

**Output**: Updated `ROADMAP.md` with priorities

---

### 2. Epic Design (Before starting large feature)

**Goal**: Detailed design and breakdown of major feature

**Activities**:
```bash
# Create Epic plan
vim docs/planning/epic7-java-support.md

# Include:
# - User stories (what needs to be built)
# - Technical approach (how to build it)
# - Dependencies (what's needed first)
# - Success criteria (how to measure completion)
# - Timeline (rough estimate)

# Review and refine
- Technical feasibility?
- Resource requirements?
- Risks and mitigation?

# Create GitHub Issue
gh issue create \
  --title "Epic 7: Java Language Support" \
  --label epic,priority:high \
  --milestone v0.6.0 \
  --body "See: docs/planning/epic7-java-support.md

## User Stories
- [ ] Story 7.1: Java Parser
- [ ] Story 7.2: Spring Routes
- [ ] Story 7.3: Maven Detection

## Success Criteria
- [ ] Parse 95%+ valid Java code
- [ ] Extract Spring routes 100% accuracy
- [ ] Handle 100k+ LOC projects"
```

**Output**:
- Epic plan document (`epicN-name.md`)
- Epic GitHub Issue (linked to plan)

---

### 3. Story Breakdown (Sprint planning)

**Goal**: Break Epic into implementable stories

**Activities**:
```bash
# For each story in Epic:

# 1. Create GitHub Issue
gh issue create \
  --title "Story 7.1: Java Parser Integration" \
  --label feature \
  --milestone v0.6.0 \
  --body "Part of: #1 (Epic 7: Java Support)

## Description
Integrate tree-sitter-java parser to extract symbols from Java files.

## Acceptance Criteria
- [ ] Parse classes, interfaces, enums
- [ ] Extract methods with signatures
- [ ] Handle Java 8-21 syntax
- [ ] 90%+ test coverage

## Technical Notes
- Use tree-sitter-java 0.21+
- Extend Parser base class
- Add java.py module

## Estimated Effort
5 days"

# 2. Create detailed plan (if complex)
vim docs/planning/story-7.1-java-parser.md  # Optional

# 3. Link to Epic
# GitHub automatically links via "Part of: #1"
```

**Output**:
- Story GitHub Issues (one per story)
- Optional: Detailed story plans for complex stories
- All linked to Epic issue and milestone

---

### 4. Development (Daily)

**Goal**: Implement story following TDD

**Activities**:
```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/java-parser

# TDD Development
# 1. Red: Write failing tests
vim tests/test_java_parser.py
pytest tests/test_java_parser.py -v  # Expected: FAIL ❌

# 2. Green: Implement to pass tests
vim src/codeindex/java_parser.py
pytest tests/test_java_parser.py -v  # Expected: PASS ✅

# 3. Refactor: Optimize
ruff check src/
pytest  # All tests still pass

# Commit with issue reference
git add tests/test_java_parser.py src/codeindex/java_parser.py
git commit -m "feat(parser): add Java parser

Implements basic Java parsing with tree-sitter.
- Extract classes, interfaces, enums
- Parse method signatures
- Handle Java 8-21 syntax

Refs #2"

git push origin feature/java-parser

# Create Pull Request
gh pr create \
  --title "feat: Java parser support" \
  --body "Implements Story 7.1: Java Parser Integration

## Changes
- Add JavaParser class
- Integrate tree-sitter-java
- Extract symbols from Java files

## Testing
- 25 unit tests (95% coverage)
- Integration tests with sample Java projects

## Closes
Closes #2

Part of Epic #1"
```

**Output**:
- Feature branch with commits
- Pull Request (linked to issue)
- All tests passing

---

### 5. Completion (After PR merge)

**Goal**: Close issue, update documentation, track progress

**Activities**:
```bash
# PR merged → Issue auto-closes (via "Closes #2" in PR)

# Update ROADMAP.md status
vim docs/planning/ROADMAP.md
# Mark Story 7.1 as ✅ Complete

# Update CHANGELOG.md
vim CHANGELOG.md
# Add entry under [Unreleased] or [X.Y.0]

# Regenerate documentation
codeindex scan-all --fallback

# Commit documentation updates
git add ROADMAP.md CHANGELOG.md src/codeindex/README_AI.md
git commit -m "docs: update for Story 7.1 completion"

# Continue to next story
gh issue view 3  # Story 7.2
```

**Output**:
- Issue closed ✅
- ROADMAP.md updated
- CHANGELOG.md updated
- Documentation regenerated

---

## Best Practices

### Planning Documents

**✅ Do**:
- Version control all planning documents (track evolution)
- Include design decisions and rationale (why, not just what)
- Update status as work progresses (🔄 In Progress, ✅ Complete)
- Link to related GitHub Issues
- Keep plans up-to-date (reflect reality)

**❌ Don't**:
- Duplicate content between planning docs and issues
- Create plans without execution (planning for planning's sake)
- Let plans go stale (update or archive)
- Forget to reference plans in issues/PRs

### GitHub Issues

**✅ Do**:
- Use clear, actionable titles ("Add Java parser" not "Java stuff")
- Link to planning documents (provide context)
- Use issue templates for consistency
- Reference in commits/PRs ("Refs #N", "Closes #N")
- Close when done (via PR merge)
- Add acceptance criteria (what defines "done"?)

**❌ Don't**:
- Create issues for trivial tasks (just do them)
- Let issues go stale (close or update)
- Forget to link to Epic (loses context)
- Write novels in issue descriptions (link to planning doc instead)

### Workflow Integration

**✅ Do**:
- Create Epic issue BEFORE starting work (provides tracking)
- Break Epic into Story issues (manageable chunks)
- Use feature branches for each story
- Reference issues in every commit
- Use "Closes #N" in PRs (auto-close)
- Update ROADMAP.md regularly (source of truth)

**❌ Don't**:
- Start coding without planning (leads to rework)
- Skip TDD (write tests first!)
- Commit directly to develop/master (use feature branches)
- Forget to update CHANGELOG (users need to know what changed)

---

## Issue Templates

Create `.github/ISSUE_TEMPLATE/` directory with the following templates:

### epic.md

```markdown
---
name: Epic
about: Major feature requiring multiple stories (2+ weeks)
labels: epic
---

## Epic Overview

[Brief description of what this epic will deliver]

## User Stories

- [ ] Story 1: [description]
- [ ] Story 2: [description]
- [ ] Story 3: [description]

## Planning Document

See: `docs/planning/epicN-name.md`

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Target Version

vX.Y.0

## Dependencies

- Depends on: [other epics/features]
- Blocks: [future work]

## Estimated Timeline

[X weeks]
```

### feature.md

```markdown
---
name: Feature/Story
about: User-facing feature or story
labels: feature
---

## Description

[What does this feature do? What problem does it solve?]

## Epic

Part of: #N (Epic name)

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes

[Implementation approach, key decisions, dependencies]

## Testing Requirements

- Unit tests: [what to test]
- Integration tests: [scenarios]
- E2E tests: [user workflows]

## Estimated Effort

[X days]
```

### bug.md

```markdown
---
name: Bug Report
about: Report a bug or issue
labels: bug
---

## Description

[Clear description of the bug]

## Steps to Reproduce

1. [First step]
2. [Second step]
3. [See error]

## Expected Behavior

[What should happen]

## Actual Behavior

[What actually happens]

## Environment

- codeindex version: [e.g., v0.5.0]
- Python version: [e.g., 3.11]
- OS: [e.g., macOS 14.0]

## Additional Context

[Screenshots, logs, error messages]
```

### enhancement.md

```markdown
---
name: Enhancement
about: Improvement to existing feature
labels: enhancement
---

## Current Behavior

[How does the feature currently work?]

## Proposed Enhancement

[What improvement do you suggest?]

## Benefits

- [Benefit 1]
- [Benefit 2]

## Alternatives Considered

[Other approaches you've thought about]

## Additional Context

[Examples, use cases, references]
```

---

## Example: Java Support Workflow

This example demonstrates the complete workflow for Epic 7: Java Language Support.

### Phase 1: Strategic Planning

**Context**: After v0.5.0 release, team decides Java support is top priority

**Action**:
```bash
# Update ROADMAP.md
vim docs/planning/ROADMAP.md

# Added:
## v0.6.0 - Java Language Support (Target: 2026-03-15)
**Theme**: Enterprise Java ecosystem support
**Priority**: 🔥 P0

**Key Features**:
- Java parser (tree-sitter-java)
- Spring Framework route extraction
- Maven/Gradle project detection
```

**Decision**: Java support is v0.6.0 focus (6-week timeline)

---

### Phase 2: Epic Design

**Action**:
```bash
# Create detailed Epic plan
vim docs/planning/epic7-java-support.md

# Included:
# - 5 user stories (7.1 Parser, 7.2 Spring, 7.3 Maven, 7.4 Scoring, 7.5 JavaDoc)
# - Technical architecture (JavaParser class, SpringRouteExtractor plugin)
# - Testing strategy (100+ unit, 20 integration, 5 E2E)
# - 6-week implementation plan

# Create Epic issue
gh issue create \
  --title "Epic 7: Java Language Support" \
  --label epic,priority:high \
  --milestone v0.6.0 \
  --body "See: docs/planning/epic7-java-support.md

Enterprise Java projects need code indexing support.

## User Stories
- [ ] Story 7.1: Java Parser (tree-sitter-java)
- [ ] Story 7.2: Spring Routes (@RestController)
- [ ] Story 7.3: Maven/Gradle Detection
- [ ] Story 7.4: Java Symbol Scoring
- [ ] Story 7.5: JavaDoc Extraction

## Success Criteria
- [ ] Parse 95%+ valid Java code
- [ ] Extract Spring routes with 100% accuracy
- [ ] Handle large Java projects (>100k LOC)"
```

**Output**: Epic #1 created, linked to `epic7-java-support.md`

---

### Phase 3: Story Breakdown

**Action**:
```bash
# Story 7.1: Java Parser
gh issue create \
  --title "Story 7.1: Java Parser Integration" \
  --label feature \
  --milestone v0.6.0 \
  --body "Part of: #1 (Epic 7: Java Support)

Integrate tree-sitter-java parser.

## Acceptance Criteria
- [ ] Parse classes, interfaces, enums
- [ ] Extract methods with signatures
- [ ] Handle Java 8-21 syntax
- [ ] 90%+ test coverage"

# Story 7.2: Spring Routes
gh issue create \
  --title "Story 7.2: Spring Framework Route Extraction" \
  --label feature \
  --milestone v0.6.0 \
  --body "Part of: #1 (Epic 7: Java Support)

Extract REST API routes from Spring controllers.

## Acceptance Criteria
- [ ] Detect @RestController classes
- [ ] Parse @GetMapping, @PostMapping, etc.
- [ ] Generate route table in README_AI.md"

# ... (Stories 7.3, 7.4, 7.5)
```

**Output**: Issues #2, #3, #4, #5, #6 created, all linked to Epic #1

---

### Phase 4: Development (Story 7.1)

**Action**:
```bash
# Week 1-2: Story 7.1 (Java Parser)

# Create feature branch
git checkout -b feature/java-parser

# TDD: Write tests first
vim tests/test_java_parser.py
pytest tests/test_java_parser.py -v  # FAIL ❌

# Implement JavaParser
vim src/codeindex/java_parser.py
pytest tests/test_java_parser.py -v  # PASS ✅

# Refactor and polish
ruff check src/
pytest  # All tests pass

# Commit and push
git add .
git commit -m "feat(parser): add Java parser

Implements basic Java parsing with tree-sitter.

Refs #2"
git push origin feature/java-parser

# Create PR
gh pr create \
  --title "feat: Java parser support" \
  --body "Closes #2

Part of Epic #1"
```

**Output**: PR created, tests pass, ready for review

---

### Phase 5: Completion

**Action**:
```bash
# PR merged → Issue #2 auto-closes

# Update ROADMAP.md
vim docs/planning/ROADMAP.md
# Change: "- [ ] Story 7.1" → "- [x] Story 7.1 ✅"

# Update CHANGELOG.md
vim CHANGELOG.md
# Add: "- Java parser integration (Story 7.1)"

# Continue to Story 7.2
gh issue view 3  # Next story
```

**Output**: Story 7.1 complete, ready for Story 7.2

---

## Tips for Success

### For Planning Documents

1. **Start with Why**: Always explain rationale (why this feature? why this approach?)
2. **Include Alternatives**: Document what you considered and why you chose this path
3. **Keep It Updated**: Plans should reflect reality, not initial guesses
4. **Link Everything**: Cross-reference issues, PRs, commits

### For GitHub Issues

1. **Atomic Issues**: One issue = one deliverable (testable, mergeable)
2. **Clear Acceptance Criteria**: Define "done" upfront
3. **Estimate Effort**: Help with sprint planning (hours or days)
4. **Link to Epic**: Never lose context of why we're building this

### For Commits and PRs

1. **Reference Issues**: Use "Refs #N" or "Closes #N" in every commit
2. **Descriptive Messages**: Explain what and why, not just what
3. **Link to Epic**: In PR description, mention "Part of Epic #N"
4. **Keep PRs Small**: Easier to review, faster to merge

### For Documentation

1. **Update ROADMAP.md**: Single source of truth for progress
2. **Update CHANGELOG.md**: Every user-visible change
3. **Regenerate README_AI.md**: After code changes
4. **Write Release Notes**: For major versions

---

## Checklist: Did You Follow the Workflow?

**Before Starting Work**:
- [ ] ROADMAP.md defines priorities
- [ ] Epic plan exists (for large features)
- [ ] Epic issue created and linked
- [ ] Story issues created and linked to Epic
- [ ] Story has clear acceptance criteria

**During Development**:
- [ ] Feature branch created
- [ ] Tests written first (TDD)
- [ ] Implementation passes tests
- [ ] Code style checked (ruff)
- [ ] Commits reference issue ("Refs #N")
- [ ] PR links to issue ("Closes #N")

**After Completion**:
- [ ] PR merged
- [ ] Issue auto-closed
- [ ] ROADMAP.md updated
- [ ] CHANGELOG.md updated
- [ ] Documentation regenerated

---

## FAQ

**Q: When should I create an Epic vs just a Story issue?**
A: Epic = 2+ weeks of work with multiple stories. Story = 1-5 days of work, single deliverable.

**Q: Do I need a planning document for every story?**
A: No. Only for complex stories requiring design decisions. Most stories just need a GitHub issue.

**Q: Should I update planning docs or GitHub issues first?**
A: Planning docs = long-term design. GitHub issues = execution. Update docs first, then create issues.

**Q: What if priorities change mid-Epic?**
A: Update ROADMAP.md and Epic plan. Close or defer low-priority story issues. Communicate changes.

**Q: Can I work on multiple stories in parallel?**
A: Yes, but use separate feature branches. Don't let stories block each other.

**Q: How often should I update ROADMAP.md?**
A: After each story completion (mark ✅). Full review quarterly.

---

**Document Status**: ✅ Active
**Last Updated**: 2026-02-03
**Maintained By**: Development team
**Related Documents**:
- `CLAUDE.md` - Developer guide
- `docs/planning/ROADMAP.md` - Strategic roadmap
- `docs/planning/epic*.md` - Epic plans
