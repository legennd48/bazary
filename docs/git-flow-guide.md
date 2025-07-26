# 🌊 Git Flow Workflow Guide

This document outlines the Git Flow branching strategy for the Bazary project.

## 🌟 Branch Structure

### Main Branches

- **`main`** - Production-ready code. All releases are tagged here.
- **`develop`** - Integration branch for features. All feature development flows through here.

### Supporting Branches

- **`feature/*`** - New features (e.g., `feature/user-authentication`)
- **`release/*`** - Release preparation (e.g., `release/1.2.0`)
- **`hotfix/*`** - Critical production fixes (e.g., `hotfix/security-patch`)

## 🚀 Workflow Commands

### Starting a New Feature

```bash
# Switch to develop and pull latest changes
git checkout develop
git pull origin develop

# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Work on your feature...
git add .
git commit -m "feat: add new feature implementation"

# Push feature branch
git push -u origin feature/your-feature-name

# Create Pull Request from feature/your-feature-name → develop
```

### Finishing a Feature

```bash
# Ensure feature is up to date with develop
git checkout develop
git pull origin develop
git checkout feature/your-feature-name
git rebase develop

# Create Pull Request and merge through GitHub
# After merge, clean up local branch
git checkout develop
git pull origin develop
git branch -d feature/your-feature-name
```

### Creating a Release

```bash
# Start from develop
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/1.2.0

# Update version numbers, changelog, etc.
# Make final tweaks and bug fixes

# Commit release changes
git add .
git commit -m "chore: prepare release 1.2.0"

# Push release branch
git push -u origin release/1.2.0

# Create PR to main for release
# After merge to main, tag the release
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# Merge back to develop
git checkout develop
git merge main
git push origin develop

# Clean up release branch
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

### Emergency Hotfix

```bash
# Start from main
git checkout main
git pull origin main

# Create hotfix branch
git checkout -b hotfix/critical-security-fix

# Make the fix
git add .
git commit -m "fix: resolve critical security vulnerability"

# Push hotfix
git push -u origin hotfix/critical-security-fix

# Create PR to main
# After merge, tag the hotfix
git checkout main
git pull origin main
git tag -a v1.2.1 -m "Hotfix version 1.2.1"
git push origin v1.2.1

# Merge back to develop
git checkout develop
git merge main
git push origin develop

# Clean up hotfix branch
git branch -d hotfix/critical-security-fix
git push origin --delete hotfix/critical-security-fix
```

## 📝 Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples
```bash
feat(auth): add JWT token refresh functionality
fix(products): resolve category filtering bug
docs: update API documentation for v1.2
test(auth): add integration tests for login flow
chore: update dependencies to latest versions
```

## 🛡️ Branch Protection Rules

### Main Branch
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date
- Restrict pushes to admins only
- Require signed commits

### Develop Branch
- Require pull request reviews
- Require status checks to pass
- Allow force pushes for maintainers

## 🔄 Pull Request Process

1. **Create Feature Branch** from `develop`
2. **Implement Changes** with tests
3. **Run Local Checks**:
   ```bash
   # Code formatting
   black .
   isort .
   
   # Linting
   flake8 .
   
   # Tests
   pytest
   
   # Security checks
   bandit -r apps/
   ```
4. **Push and Create PR**
5. **Code Review** and feedback
6. **CI/CD Checks** must pass
7. **Merge** after approval

## 📊 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All features merged to develop
- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release notes
- [ ] Tag release
- [ ] Deploy to production

## 🚨 Emergency Procedures

### Critical Hotfix
1. Create hotfix branch from `main`
2. Implement minimal fix
3. Fast-track PR review
4. Deploy immediately after merge
5. Merge back to `develop`

### Rollback Process
1. Identify last known good commit
2. Create hotfix branch
3. Revert problematic changes
4. Follow emergency deployment process

## 🛠️ Useful Git Aliases

Add these to your `~/.gitconfig`:

```ini
[alias]
    # Git Flow shortcuts
    feature = "!f() { git checkout develop && git pull origin develop && git checkout -b feature/$1; }; f"
    release = "!f() { git checkout develop && git pull origin develop && git checkout -b release/$1; }; f"
    hotfix = "!f() { git checkout main && git pull origin main && git checkout -b hotfix/$1; }; f"
    
    # Useful shortcuts
    st = status
    co = checkout
    br = branch
    cm = commit
    pl = pull
    ps = push
    lg = log --oneline --decorate --graph --all
    
    # Clean up merged branches
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"
```

## 📱 IDE Integration

### VS Code Extensions
- GitLens
- Git Graph
- Git History
- Conventional Commits

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 🎯 Best Practices

1. **Keep branches focused** - One feature per branch
2. **Write descriptive commit messages**
3. **Rebase feature branches** before merging
4. **Delete merged branches** promptly
5. **Use draft PRs** for work in progress
6. **Review your own PR** before requesting reviews
7. **Keep PRs small** and focused
8. **Write tests** for new features
9. **Update documentation** as needed
10. **Follow the Boy Scout Rule** - leave code cleaner than you found it
