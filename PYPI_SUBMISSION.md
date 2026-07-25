# PyPI Submission Guide for PyStreamPDF v2.1.0

This document provides step-by-step instructions to publish PyStreamPDF v2.1.0 to PyPI.

---

## Prerequisites

### 1. Python Tools
```bash
# Ensure you have the build tools
pip install twine build

# Or with uv
uv pip install twine build
```

### 2. PyPI Account
- Create account at https://pypi.org/account/register/
- Set up 2FA (recommended)
- Store credentials in `~/.pypirc` (see template below)

### 3. PyPI API Token
- Go to https://pypi.org/manage/account/token/
- Create a new API token with **scope: Entire account**
- Save the token (it's only shown once)

### 4. Setup ~/.pypirc
Create `~/.pypirc` with your token:

```ini
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5...  # Your full token from step 3
```

**Security Note**: Make sure permissions are restricted:
```bash
chmod 600 ~/.pypirc
```

---

## Submission Steps

### Step 1: Verify Package is Built

```bash
cd /Users/georgimullassery/PyStreamPDF

# Check that dist/ has both wheel and sdist
ls -lh dist/

# Expected output:
# pystreampdf-2.1.0-cp313-cp313-macosx_11_0_arm64.whl  (~5MB)
# pystreampdf-2.1.0.tar.gz  (~200KB)
```

### Step 2: Verify Package Metadata

```bash
# Check that README renders correctly
python -m twine check dist/*

# Expected output:
# Checking dist/pystreampdf-2.1.0.tar.gz: PASSED
# Checking dist/pystreampdf-2.1.0-cp313-cp313-macosx_11_0_arm64.whl: PASSED
```

### Step 3: Test Upload (OPTIONAL but RECOMMENDED)

Before submitting to PyPI, test on TestPyPI first:

```bash
# Create TestPyPI token at https://test.pypi.org/manage/account/token/
# Then configure ~/.pypirc with both indices:

# ~/.pypirc:
# [distutils]
# index-servers =
#     pypi
#     testpypi
#
# [testpypi]
# repository = https://test.pypi.org/legacy/
# username = __token__
# password = pypi-AgEIcHlwaS5...  # Test token

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Then test install from TestPyPI
pip install --index-url https://test.pypi.org/simple pystreampdf==2.1.0

# Verify it works
python -c "import pystreampdf; print(pystreampdf.__version__)"
```

### Step 4: Submit to PyPI

```bash
# Upload to official PyPI
python -m twine upload dist/*

# You'll be prompted for credentials (or uses ~/.pypirc)
# Expected output:
# Uploading pystreampdf-2.1.0.tar.gz
# Uploading pystreampdf-2.1.0-cp313-cp313-macosx_11_0_arm64.whl
# View at: https://pypi.org/project/pystreampdf/2.1.0/
```

### Step 5: Verify on PyPI

Go to https://pypi.org/project/pystreampdf/2.1.0/ and verify:
- ✅ Version 2.1.0 is listed
- ✅ Description and README render correctly
- ✅ Installation instructions work
- ✅ Links to repository, issues, docs are correct

### Step 6: Test Installation from PyPI

```bash
# In a fresh virtualenv or environment
pip install pystreampdf

# Verify version
python -c "import pystreampdf; print(pystreampdf.__version__)"
# Expected: 2.1.0

# Verify modules are available
python -c "from pystreampdf.optimization import ChunkingEngine; print('✅ All modules imported')"
```

---

## Troubleshooting

### Issue: "twine not found"
```bash
pip install --upgrade twine build
```

### Issue: "Invalid or missing credentials"
```bash
# Check ~/.pypirc permissions
ls -l ~/.pypirc  # Should be 600

# Test credentials
python -m twine check dist/*  # This should work without auth

# If twine auth fails, re-create ~/.pypirc with your token
```

### Issue: "Package already exists"
PyPI doesn't allow re-uploading the same version. Options:
1. **Increment version** (e.g., 2.1.1) and rebuild
2. **Delete on PyPI** (via website, then re-upload) - this has a 30-minute grace period

### Issue: "wheel requires Rust compilation"
This is expected for mixed Python/Rust packages. Ensure:
- maturin is installed: `pip install maturin`
- Rust toolchain is available: `rustc --version`
- PyO3 bindings are configured: check `python/Cargo.toml`

### Issue: "README doesn't render"
```bash
# Check README for issues
python -m readme_renderer README.md

# Common issues:
# - Invalid RST syntax
# - Missing image files
# - Broken links

# Verify README.md is referenced in pyproject.toml
cat pyproject.toml | grep readme
```

---

## Post-Submission Steps

### 1. Create GitHub Release

```bash
cd /Users/georgimullassery/PyStreamPDF

# Tag the release
git tag -a v2.1.0 -m "Release v2.1.0: Complete intelligent document pipeline"

# Push tag to GitHub
git push origin v2.1.0

# Create release on GitHub (using gh CLI)
gh release create v2.1.0 \
  --title "PyStreamPDF v2.1.0: Complete Pipeline" \
  --notes-file RELEASE_2_1_0.md \
  dist/*
```

### 2. Announce Release

- Post on relevant channels (Twitter, LinkedIn, Reddit r/Python, etc.)
- Update documentation sites
- Notify users via email/newsletter

### 3. Monitor for Issues

```bash
# Watch PyPI page for questions
# https://pypi.org/project/pystreampdf/

# Monitor GitHub issues
gh issue list

# Check package stats
# https://pepy.tech/project/pystreampdf
```

---

## Quick Checklist

Before final submission, verify:

- [ ] Version bumped to 2.1.0 in `Cargo.toml`
- [ ] Version bumped to 2.1.0 in `python/pystreampdf/__init__.py`
- [ ] README.md updated with v2.1.0 content
- [ ] RELEASE_2_1_0.md created with release notes
- [ ] Package builds without errors: `python -m build`
- [ ] Metadata valid: `python -m twine check dist/*`
- [ ] PyPI credentials configured in `~/.pypirc`
- [ ] Test upload to TestPyPI works (optional but recommended)
- [ ] 523 tests passing: `pytest tests/`

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 2.1.0 | 2026-07-25 | Ready for PyPI |
| 2.0.0 | 2026-07-20 | Published |
| 1.5.0 | 2026-07-15 | Published |

---

## References

- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)

---

## Support

If you encounter issues during submission:
1. Check PyPI status: https://status.pypi.org/
2. Review Twine logs: `twine upload --verbose dist/*`
3. Open issue: https://github.com/pypa/twine/issues

---

**Ready to publish PyStreamPDF v2.1.0 to PyPI!**
