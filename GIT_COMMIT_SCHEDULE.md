# Git Commit Schedule & Best Practices

## 📅 Recommended Commit Schedule

### **Development Phase (Current)**
- **Frequency**: After completing each feature/phase
- **Timing**: Daily or every 2-3 days
- **Trigger**: When a significant feature is complete and tested

### **Specific Schedule for SEO AI Checker Phases**

| Phase | Feature | Recommended Commit Timing |
|-------|---------|--------------------------|
| Phase 3 | Keyword Research Module | Within 2-3 days of completion |
| Phase 4 | Competitor Analysis | Within 2-3 days of completion |
| Phase 5 | Backlink Analysis | Within 2-3 days of completion |
| Phase 6 | Content Marketing Module | Within 2-3 days of completion |
| Phase 7 | Dashboard UI Redesign | Within 1-2 days (split into 2-3 commits) |

---

## 🎯 Commit Guidelines

### **Commit Message Format** (Semantic Commit)
```
<type>(<scope>): <subject>

<body>

<footer>
```

### **Types**
- `feat`: A new feature
- `fix`: A bug fix
- `refactor`: Code refactoring without feature changes
- `style`: Code style changes (formatting, missing semicolons)
- `test`: Adding or updating tests
- `docs`: Documentation changes
- `perf`: Performance improvements
- `ci`: CI/CD configuration changes

### **Examples**

**Good Commits:**
```bash
# Feature commit
git commit -m "feat(keyword-research): add SerpAPI integration for search volume and difficulty"

# Bug fix
git commit -m "fix(audit): resolve issue categorization logic for critical issues"

# Database migration
git commit -m "feat(models): add Keyword and KeywordRanking models for rank tracking"

# Frontend update
git commit -m "feat(dashboard): create Semrush-like audit report UI with issue categorization"
```

---

## 📋 Pre-Commit Checklist

Before every commit, verify:

- [ ] All new code is tested locally
- [ ] No `.env` file is committed (should be in `.gitignore`)
- [ ] No `node_modules` or `env/` directory is committed
- [ ] Database migrations are included for model changes
- [ ] API endpoints return correct response format
- [ ] Frontend updates match backend API response
- [ ] No debug print statements left in code
- [ ] Comments are clear and helpful

### **Files to NEVER commit:**
```
.env                    # API keys
.env.local             # Local config
db.sqlite3             # Database (can be recreated)
env/                   # Virtual environment
node_modules/          # NPM packages
__pycache__/           # Python cache (update .gitignore)
*.pyc                  # Compiled Python (update .gitignore)
.next/                 # Next.js build cache
```

---

## 🔄 Commit Frequency Strategy

### **Recommended Pattern**
```
Day 1:  Start Phase 3 → Commit at end of day (even if incomplete)
Day 2:  Continue Phase 3 → Bug fixes → Final commit when done
Day 3:  Start Phase 4 → Commit daily
...
```

### **Daily/2-3 Day Development**
```bash
# At end of day (save progress)
git add -A
git commit -m "wip(phase-3): keyword research - 60% complete"

# Next day when complete
git add -A
git commit -m "feat(keyword-research): complete SerpAPI integration with caching"
```

---

## 📤 When to Push to GitHub

### **Push Immediately When:**
- ✅ Feature is complete and tested
- ✅ Bug fix is verified
- ✅ All tests pass
- ✅ No `.env` or sensitive data

### **Push at Scheduled Times:**
- **After each completed phase** (every 2-3 days)
- **Daily at end of work day** (if working on multi-day features)
- **Before major milestones** (feature complete, deployment ready)

### **Push Command**
```bash
# Push to main branch
git push origin main

# Or push to feature branch (if using branches)
git push origin feature/phase-3-keyword-research
```

---

## 🌳 Optional: Feature Branches (Advanced)

For larger phases, consider using feature branches:

```bash
# Create feature branch
git checkout -b feature/phase-3-keyword-research

# Work on the feature
git add -A
git commit -m "feat: keyword research implementation"

# When complete, merge back to main
git checkout main
git merge feature/phase-3-keyword-research
git push origin main

# Delete branch
git branch -d feature/phase-3-keyword-research
```

---

## 🚨 Important Notes

### **What NOT to Commit**
- Passwords, API keys (use `.env` instead)
- Database file (`db.sqlite3`)
- Virtual environment (`env/` folder)
- Node modules (`node_modules/`)
- IDE settings (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)

### **Update .gitignore if needed:**
```bash
# View current .gitignore
cat .gitignore

# Add entries if missing
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "db.sqlite3" >> .gitignore
```

---

## 📊 Commit Log Format for This Project

Each phase will be tracked as:

```
Phase 1-2: Enhanced SEO Audit & Database Models ✅
Phase 3:   Keyword Research Module
Phase 4:   Competitor Analysis Module
Phase 5:   Backlink Analysis Module
Phase 6:   Content Marketing Module
Phase 7:   Dashboard UI Redesign
```

View all commits:
```bash
git log --oneline
```

---

## 🎯 Summary Schedule for Your Project

| Timeline | Action |
|----------|--------|
| **Today (Complete)** | ✅ Phase 1-2 committed and pushed |
| **Next 2-3 days** | Start Phase 3 (Keyword Research) → Commit when done |
| **Following 2-3 days** | Start Phase 4 (Competitor Analysis) → Commit |
| **Every 2-3 days** | Continue pattern for Phases 5, 6, 7 |
| **Total Timeline** | 2-3 weeks for complete Semrush-like platform |

---

## Commands Quick Reference

```bash
# Check status
git status

# Stage all changes
git add -A

# Commit with message
git commit -m "feat: description here"

# Push to GitHub
git push origin main

# View commit history
git log --oneline

# View specific commit details
git show <commit-hash>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

---

## Next Commit Plan

**Phase 3 (Keyword Research):**
```bash
git commit -m "feat(keyword-research): implement SerpAPI integration
- Add Keyword model data persistence
- Create keyword research service with search volume, difficulty, intent analysis
- Build /api/keyword-research/ endpoint
- Add caching for API calls
- Support competitor keyword analysis"
```

**Phase 4 (Competitor Analysis):**
```bash
git commit -m "feat(competitor-analysis): implement competitor tracking
- Add Competitor model and tracking logic
- Analyze top keywords for competitors
- Estimate competitor traffic
- Build /api/competitors/ endpoint
- Add backlink profile comparison"
```

---

Good luck with Phase 3! 🚀
