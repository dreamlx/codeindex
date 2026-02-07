# GitHub Issue Management - Quick Reference

**For**: codeindex project
**Strategy**: Lightweight, Future-Focused (方案B + 策略1)
**Last Updated**: 2026-02-07

---

## 🎯 Core Principles

1. **Only create issues for future work** (不追溯历史)
2. **ROADMAP.md is single source of truth** (已完成的工作看文档)
3. **Epic issues at design phase** (有planning doc后创建)
4. **Story issues only when needed** (复杂或需要讨论时)

---

## 📋 When to Create Issues

| Situation | Create Issue? | Type |
|-----------|--------------|------|
| New Epic starting | ✅ Yes | Epic |
| Complex Story (>3 days) | ✅ Yes | Feature/Story |
| Simple Story (<3 days) | ❌ No (just implement) | - |
| Bug discovered | ✅ Yes | Bug |
| Enhancement idea | ✅ Yes | Enhancement |
| Completed Epic | ❌ No (document in ROADMAP) | - |

---

## 🚀 Quick Commands

### Create Epic Issue

```bash
gh issue create \
  --title "Epic N: [Name]" \
  --label epic,priority:high \
  --milestone v0.X.0 \
  --body "See: docs/planning/epicN-name.md

## User Stories
- [ ] Story N.1: [description]
- [ ] Story N.2: [description]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2"
```

### Create Story Issue

```bash
gh issue create \
  --title "Story N.M: [Name]" \
  --label feature,story \
  --milestone v0.X.0 \
  --body "Part of: #N (Epic name)

## Acceptance Criteria
- [ ] AC1: [description]
- [ ] AC2: [description]

## Estimated Effort
[X days]"
```

### Close Old Issues

```bash
# Close single issue
gh issue close N --comment "✅ Completed in v0.X.0. See CHANGELOG.md"

# Close multiple issues
gh issue close 1 2 3 4 --comment "✅ Completed as part of Epic N."
```

### List Issues

```bash
# All open issues
gh issue list

# By milestone
gh issue list --milestone v0.12.0

# By label
gh issue list --label epic
gh issue list --label bug
```

---

## 🏷️ Labels Reference

### Type Labels
- `epic` - Major feature (2+ weeks)
- `feature` / `story` - User story
- `enhancement` - Improvement
- `bug` - Bug fix
- `documentation` - Docs only

### Priority Labels
- `priority:high` - Must have, blocking
- `priority:medium` - Should have
- `priority:low` - Nice to have

---

## 📝 Commit Message Format

```bash
# Reference issue (work in progress)
git commit -m "feat(module): add feature

Implements part of the feature.

Refs #N"

# Close issue (final commit or PR)
git commit -m "feat(module): complete feature

Implements all acceptance criteria.

Closes #N"
```

---

## 🔄 Workflow Example

### Starting a New Epic

```bash
# 1. Create planning document
vim docs/planning/epic8-typescript-support.md

# 2. Create Epic issue
gh issue create --title "Epic 8: TypeScript Support" \
  --label epic --milestone v0.13.0

# 3. Create Story issues (only complex ones)
gh issue create --title "Story 8.1: TypeScript Parser" \
  --label feature,story --milestone v0.13.0

# 4. Create feature branch
git checkout -b feature/typescript-parser

# 5. TDD development
# ... write tests, implement, commit ...

# 6. Create PR
gh pr create --title "feat: TypeScript parser support" \
  --body "Closes #N"
```

---

## ⚠️ Common Mistakes

### ❌ Don't Do This

1. **Creating issues for completed work**
   - Past work → Document in ROADMAP.md
   - Completed Epic → Write completion report

2. **Creating Story issues for trivial tasks**
   - <3 days → Just implement, commit with good message
   - Obvious changes → No need for issue

3. **Forgetting to link Epic**
   - Always add "Part of: #N" in Story issues
   - Always add "Closes #N" in PRs

4. **Not updating ROADMAP.md**
   - Mark stories as ✅ when done
   - Update version status

### ✅ Do This Instead

1. **Use ROADMAP.md as single source of truth**
2. **Create issues only for future work**
3. **Link everything: Planning Doc ↔ Issue ↔ Commit ↔ PR**
4. **Keep issues focused and actionable**

---

## 📚 Related Documents

- **Full Workflow**: `docs/development/requirements-workflow.md`
- **Issue Templates**: `.github/ISSUE_TEMPLATE/`
- **Strategic Roadmap**: `docs/planning/ROADMAP.md`
- **Developer Guide**: `CLAUDE.md`

---

## 🎓 Examples

### Good Issue Title ✅
- `Epic 8: TypeScript Language Support`
- `Story 8.1: TypeScript Parser Integration`
- `[Bug]: Parser fails on Java 21 sealed classes`
- `[Enhancement]: Add --watch mode for incremental indexing`

### Bad Issue Title ❌
- `TypeScript` (too vague)
- `Fix bug` (no context)
- `Epic 9 completed` (don't create issues for past work)
- `Update docs` (no specific scope)

---

**Last Updated**: 2026-02-07
**Strategy**: Lightweight, Future-Focused
**Status**: ✅ Active
