# Known Issues and Limitations

This document tracks known issues, limitations, and planned improvements for GitSimulator.

## 🔴 Critical Issues (Fixed in v1.0.12)

### ✅ Empty Repository Crash
- **Status:** FIXED
- **Issue:** Commands crashed when run in repositories with no commits
- **Fix:** Added proper error handling in `Repository.head_sha` property
- **Version:** Fixed in 1.0.12

### ✅ TUI Detached Commit Detection  
- **Status:** FIXED
- **Issue:** HEAD commit incorrectly shown as "detached" in TUI
- **Fix:** Added check to exclude HEAD from detached commit marking
- **Version:** Fixed in 1.0.12

## 🟡 Known Limitations

### Large Repository Performance
- **Impact:** Commands may be slow on repositories with 10,000+ commits
- **Workaround:** Use `--max-count` flag to limit commit traversal
- **Example:** `gitsim log --max-count 50`
- **Planned Fix:** Optimize topological sort with early termination (v1.1.0)

### Binary File Conflict Detection
- **Impact:** Binary file conflicts may not be detected accurately
- **Current Behavior:** Assumes conflict when hunks are empty
- **Planned Fix:** Improve binary file handling (v1.1.0)

### Merge Commit Cherry-Pick
- **Impact:** Cherry-picking merge commits shows warning but proceeds
- **Current Behavior:** Diffs against first parent only
- **Git Behavior:** Requires `-m` flag to specify parent
- **Planned Fix:** Add parent selection support (v1.1.0)

### Status Command Naming
- **Impact:** `gitsim status` doesn't show working directory changes like `git status`
- **Current Behavior:** Shows repository info and recent commits
- **Workaround:** Use `git status` for working directory changes
- **Consideration:** May rename to `gitsim info` in future version

## 🔵 Edge Cases

### Detached HEAD in Merge Operations
- **Behavior:** When HEAD is detached, visualizations show "HEAD" as a branch name
- **Impact:** Slightly misleading but functional
- **Priority:** Low

### Fast-Forward Merge Visualization
- **Behavior:** Before/after graphs look identical for fast-forward merges
- **Workaround:** Check the "Operation" type in output
- **Planned Improvement:** Add special visualization for fast-forward (v1.1.0)

### Zero Commits to Rebase
- **Behavior:** When source and onto are the same, before/after graphs are identical
- **Current:** Shows warning in validation
- **Planned Improvement:** Add clearer messaging (v1.1.0)

## 📋 Usage Recommendations

### For Large Repositories
```bash
# Always use --max-count for large repos
gitsim log --max-count 50

# For simulations, limit scope
gitsim rebase main  # Only shows relevant commits
```

### For Complex Merges
```bash
# Check for conflicts first
gitsim merge feature-branch

# Review conflict predictions before actual merge
# Use git merge after reviewing simulation
```

### For Safe Reset Operations
```bash
# Create snapshot before reset
gitsim snapshot create "before-reset"

# Simulate reset
gitsim reset --hard HEAD~5

# Only proceed if comfortable with result
```

## 🛠️ Workarounds

### Empty Repository Initialization
If you're testing in a new repository:
```bash
# Create initial commit first
echo "# Project" > README.md
git add README.md
git commit -m "Initial commit"

# Now GitSimulator commands will work
gitsim status
```

### TUI in Empty Repository
The TUI requires at least one commit. Create an initial commit first:
```bash
git init
git commit --allow-empty -m "Initial commit"
gitsim tui
```

## 🔄 Reporting Issues

Found a new issue? Please report it:
1. Check this document first
2. Open an issue at: https://github.com/egekaya1/GitSimulator/issues
3. Include:
   - GitSimulator version (`gitsim --version`)
   - Command that failed
   - Error message
   - Repository state (empty, large, etc.)

## 📅 Roadmap

### v1.1.0 (Planned)
- [ ] Performance improvements for large repositories
- [ ] Better binary file conflict detection
- [ ] Merge commit parent selection for cherry-pick
- [ ] Improved fast-forward merge visualization
- [ ] Better error messages with suggestions

### v1.2.0 (Planned)
- [ ] Interactive conflict resolution preview
- [ ] Plugin API improvements
- [ ] Advanced graph visualization options
- [ ] Stash simulation support

### v2.0.0 (Future)
- [ ] Remote operations simulation (push, pull, fetch)
- [ ] Submodule support
- [ ] Performance optimization for enterprise repos
- [ ] Web-based TUI option
