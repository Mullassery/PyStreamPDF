# PyStreamPDF Commercial Transition - Quick Reference Card

**Print this. Post it on your team wall. Use it daily.**

---

## 30-Second Version

📦 **Before:** Open-source, MIT license, public source code  
📦 **After:** Proprietary, commercial license, private source code  
📦 **Distribution:** Same (PyPI wheels only)  
📦 **Quality:** Same (523 tests, production-ready)  
📦 **Installation:** Same (`pip install pystreampdf`)  

---

## The One Rule

**Public:** Documentation, examples, benchmarks, diagrams  
**Private:** Source code (.rs, .py implementation files)  
**Distribution:** Compiled wheels only (no source)  

---

## Week-by-Week Checklists

### Week 1: Remove MIT, Add Proprietary License
```bash
# Verify no MIT references remain
grep -r "MIT" . --exclude-dir=.git --exclude-dir=dist
# Should return 0 results or only in this guide

# Verify license in metadata
grep -n "license" Cargo.toml  # Should NOT show "MIT"
grep -n "license" python/pyproject.toml  # Should show "Proprietary"
```

### Week 2: Privatize Repo & Create Public Showcase
```bash
# Main repo is private
curl https://github.com/[user]/PyStreamPDF  # Should get 404

# Public repo exists with structure
ls pystreampdf-public/{docs,examples,benchmarks,architecture}
# All directories should exist with content
```

### Week 3: Harden PyPI & Document Everything
```bash
# Wheels contain no source
unzip -l dist/*.whl | grep -E "\.(rs|py|toml)$"
# Should return NO matches

# Documentation is complete
find docs/ -name "*.md" | wc -l  # Should be 10+
find examples/ -name "*.py" | wc -l  # Should be 5+
```

### Week 4: Security Audit & Launch
```bash
# No secrets in git history
git log --all -p | grep -E "password|api_key|secret" | wc -l
# Should return 0

# Legal sign-off obtained
[ -f LICENSE_COMMERCIAL.md ] && echo "✅ License ready"
```

---

## Critical Tasks (Do These First)

### Must Do
- [ ] Delete MIT LICENSE file
- [ ] Remove "MIT" from Cargo.toml and pyproject.toml
- [ ] Create LICENSE_COMMERCIAL.md
- [ ] Make GitHub repo private
- [ ] Create public showcase repo
- [ ] Verify wheel contents have no .py source
- [ ] Get legal sign-off

### Should Do
- [ ] Write API documentation
- [ ] Create 3-5 examples
- [ ] Publish benchmark results
- [ ] Create architecture diagrams
- [ ] Set up GitHub Actions for validation

### Nice to Have
- [ ] Create MkDocs documentation site
- [ ] Record demo video
- [ ] Create comparison table
- [ ] Set up landing page

---

## Common Mistakes (Don't Do These)

❌ **Leave MIT license in repo** → Delete it!  
❌ **Publish .py source in wheel** → Test: `unzip dist/*.whl`  
❌ **Keep repo public** → Make private immediately  
❌ **Skip legal review** → Get sign-off before launch  
❌ **Forget to update PyPI metadata** → Must set `license = Proprietary`  
❌ **Expose implementation in docs** → Only high-level architecture  
❌ **Leave secrets in git history** → Audit all commits  

---

## Files You Need to Create

| File | Purpose | Where |
|------|---------|-------|
| LICENSE_COMMERCIAL.md | Full license | Root directory |
| LICENSE.md | License summary | Public repo root |
| docs/getting-started.md | Installation guide | Public repo |
| docs/api-reference.md | API documentation | Public repo |
| docs/deployment.md | Deployment guide | Public repo |
| docs/architecture.md | System design | Public repo |
| examples/01-basic.py | Hello world | Public repo |
| examples/02-advanced.py | Real usage | Public repo |
| benchmarks/results.md | Performance | Public repo |
| benchmarks/methodology.md | How we test | Public repo |

---

## Verification Checklist

Run these before launch:

```bash
# 1. License check
grep -r "MIT" . --exclude-dir=.git | wc -l  # Should be 0-1

# 2. Repo check
curl -I https://github.com/[user]/PyStreamPDF 2>&1 | grep "404\|private"

# 3. Wheel check
unzip -l dist/*.whl | grep -E "\.rs$|\.py$" | grep -v "__pycache__"

# 4. Installation check
python -m venv test; source test/bin/activate
pip install dist/*.whl
python -c "import pystreampdf; print('✅ OK')"

# 5. Secret check
git log --all -p | grep -i "password\|secret\|api_key" | wc -l

# 6. Example check
cd examples/01-basic && python main.py  # Should work

# 7. Docs check
find docs -name "*.md" | wc -l  # Should be 10+
```

---

## Messaging Template

**For Users:**
```
PyStreamPDF is now proprietary, enabling faster innovation and better support.

✅ Installation unchanged: pip install pystreampdf
✅ Quality unchanged: Same reliable, tested product
✅ Features unchanged: All capabilities available
✅ Distribution unchanged: PyPI with wheels only
🆕 Support available: Commercial licensing options

Free evaluation: [30] days. Commercial licensing available.
Contact: licensing@company.com
```

**For Developers:**
```
PyStreamPDF's source is now proprietary, but...

✅ Public documentation is complete
✅ Public examples are working
✅ Public benchmarks are published
✅ Public architecture is documented

Extend with public APIs only. Support for questions via GitHub Discussions.
```

---

## Support Responses

**"Why did you make it proprietary?"**
→ Enables focused development, professional support, sustainable business

**"Can I see the source code?"**
→ No. You can see comprehensive documentation, examples, and benchmarks instead.

**"Does this break my existing usage?"**
→ No. Installation, features, and quality are unchanged. Only licensing model changes.

**"How much does it cost?"**
→ Free evaluation period. Commercial pricing available. Contact licensing@company.com

**"Can I modify it?"**
→ No modifications without commercial license agreement. Extend via public APIs.

---

## Email Template: Announcement

```
Subject: PyStreamPDF Going Proprietary - What You Need to Know

Hi [Community],

PyStreamPDF is now proprietary, enabling faster development and better support.

What Changes:
- Licensing model (MIT → Proprietary)
- Support availability (Community → Professional)

What Stays the Same:
- Installation: pip install pystreampdf ✅
- Quality: 523 tests, production-ready ✅
- Features: Complete and unchanged ✅
- Distribution: PyPI wheels only ✅

Free Trial: [30-day] evaluation period
Commercial: Contact licensing@company.com

Documentation: [public-repo-link]
Examples: [examples-directory-link]
Support: GitHub Discussions [link]

Thank you for your continued support!
```

---

## Git Commands Cheat Sheet

```bash
# Remove MIT license
git rm LICENSE
git commit -m "Remove MIT license (proprietary transition)"

# Remove MIT references
git grep -l "MIT"  # Find files with "MIT"
git add .
git commit -m "Remove MIT references from source"

# Make repo private
# GitHub Web UI → Settings → General → Change visibility

# Create public repo structure
mkdir -p pystreampdf-public/{docs,examples,benchmarks,architecture}
cd pystreampdf-public
git init
git add .
git commit -m "Initial public repository structure"
# Push to GitHub as public repository

# Validate wheel before upload
python -m twine check dist/*
unzip -l dist/pystreampdf-*.whl | head -30
```

---

## Timeline at a Glance

```
Week 1  │ ■■■■□ Licensing & License removal
Week 2  │ ■■■■□ Repository privatization & public repo creation
Week 3  │ ■■■■□ Documentation & benchmarks
Week 4  │ ■■■■□ Security audit & launch
        ├─────────────────────────────────────────
        → 28 days to commercial transition complete
```

---

## Red Flags (Stop and Ask for Help)

🚩 Source files (.rs, .py) in wheel distribution  
🚩 Secrets found in git history  
🚩 No sign-off from legal counsel  
🚩 Public repository contains implementation  
🚩 "MIT" still appears in Cargo.toml or pyproject.toml  
🚩 Main repository is still public  
🚩 PyPI metadata doesn't mention proprietary  
🚩 Examples don't work or have broken imports  

**If you see any of these → Stop and escalate**

---

## Success Looks Like This

✅ Private repo: inaccessible to public  
✅ Public repo: complete docs + examples + benchmarks  
✅ PyPI: wheels only, no source  
✅ Metadata: proprietary license listed  
✅ Examples: all run without modification  
✅ Docs: professional, comprehensive, no impl details  
✅ Legal: signed off  
✅ Users: installing normally, asking questions in GitHub  

---

## Questions?

- **How do I...?** → See COMMERCIAL_TRANSITION.md
- **When do I...?** → See TRANSITION_CHECKLIST.md
- **What's the license?** → See LICENSE_COMMERCIAL_TEMPLATE.md
- **Public repo structure?** → See PUBLIC_REPO_STRUCTURE.md

---

**Print. Post. Reference. Execute.**

*Keep this handy during the 4-week transition.*

