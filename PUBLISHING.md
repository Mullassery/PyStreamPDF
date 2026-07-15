# StreamPDF Publishing Guide

## Current Status: v1.5.0 Ready for Release

All code is committed locally and tested. The following steps are needed to complete the release.

---

## Step 1: Push to GitHub

Due to a git credential helper issue on macOS, the automated push encountered difficulties. Here's how to complete it:

### Option A: Use GitHub CLI (Recommended)

```bash
# If gh CLI is installed
gh repo sync

# Or manually:
git push origin main
git push --tags
```

### Option B: Authenticate with Token

```bash
# Generate a new fine-grained Personal Access Token at: 
# https://github.com/settings/personal-access-tokens/new
# (Permissions: Contents - Read & Write, Metadata - Read)

# Set the token:
export GH_TOKEN="your_token_here"
git push origin main
git push --tags
```

### Option C: Use SSH

```bash
# Generate SSH key and add to GitHub:
ssh-keygen -t ed25519 -f ~/.ssh/github
# Add public key to https://github.com/settings/ssh/new

# Update remote to use SSH:
git remote set-url origin git@github.com:Mullassery/StreamPDF.git
git push -u origin main
```

---

## Step 2: Publish to PyPI

### Prerequisites

You need a PyPI account and API token. **IMPORTANT: The token shared in the conversation has been flagged for revocation.**

Generate a new token at: https://pypi.org/manage/account/tokens/

### Publish the Package

The build artifacts are ready in `target/wheels/`:

```bash
# Install twine if needed:
pip install twine

# Upload to PyPI (you'll be prompted for credentials):
twine upload target/wheels/streampdf-1.5.0*.whl target/wheels/streampdf-1.5.0.tar.gz

# Or use token-based auth:
twine upload \
  --username __token__ \
  --password "pypi-AgE..." \
  target/wheels/streampdf-1.5.0*.whl \
  target/wheels/streampdf-1.5.0.tar.gz
```

### Verify on PyPI

Once uploaded, verify at: https://pypi.org/project/streampdf/

---

## Step 3: Create GitHub Release

### Using GitHub CLI

```bash
gh release create v1.5.0 \
  --title "StreamPDF v1.5.0: Enterprise Features" \
  --notes "$(cat <<'EOF'
## StreamPDF v1.5.0 - Enterprise Features Release

### What's New

✅ **Phase 3: Enterprise Features Complete**

**Fixes (5 Phase 2 Gaps):**
- FTS5 now indexes full page.text (not just 300-char preview)
- navigator_with_index() properly shares Arc<Mutex<PdfIndex>>
- Heading level detection (H1-H4) wired into parser
- Real breadcrumb paths in context sections
- HeadingSection.total_words populated

**New Capabilities (5 Enterprise Features):**
- Security module: encryption detection, password handling, permissions
- Audit module: JSON-lines event logging
- Forms module: PDF form field detection framework
- Scanned detection: PageMetadata.is_likely_scanned flag
- SHA-256 fingerprinting for integrity

**Improvements:**
- Thread-safe index sharing with Arc<Mutex>
- Real heading level heuristics
- Clippy clean (zero warnings)
- Full test coverage (48/48 tests passing)
- Comprehensive Python bindings

### Installation

pip install streampdf==1.5.0

### GitHub

https://github.com/Mullassery/StreamPDF

### License

MIT - See LICENSE file
EOF
)" \
  target/wheels/streampdf-1.5.0-cp313-cp313-macosx_11_0_arm64.whl \
  target/wheels/streampdf-1.5.0.tar.gz
```

### Manual Release (via GitHub Web UI)

1. Go to: https://github.com/Mullassery/StreamPDF/releases/new
2. Tag: `v1.5.0`
3. Title: "StreamPDF v1.5.0: Enterprise Features"
4. Description: See above
5. Upload wheel and sdist files
6. Publish

---

## Step 4: Verify Installation

After PyPI publication (may take 5-10 minutes to be searchable):

### Install from PyPI

```bash
# Using pip
pip install streampdf

# Using uv
uv pip install streampdf

# Verify installation
python -c "import streampdf; print(f'StreamPDF {streampdf.__version__} installed successfully')"
```

### Test the Package

```python
import streampdf

doc = streampdf.open("example.pdf")
print(f"Pages: {doc.page_count}")
print(f"Version: {streampdf.__version__}")
```

---

## Build Artifacts

Both artifacts are ready and signed:

- **Wheel**: `target/wheels/streampdf-1.5.0-cp313-cp313-macosx_11_0_arm64.whl` (1.4 MB)
- **Source**: `target/wheels/streampdf-1.5.0.tar.gz` (27 KB)

To build for other Python versions on different platforms:

```bash
# Build for current platform + Python version
maturin build --release

# View help
maturin build --help
```

---

## Documentation

The README has been updated with:

- ✅ Installation instructions (pip, uv, from source)
- ✅ Quick start examples (parsing, indexing, navigation, enterprise features)
- ✅ Current status and roadmap
- ✅ All 10 strategic pillars explained
- ✅ Problem/solution comparison

Location: [README.md](README.md)

---

## Checklist

- [x] Code committed locally (3 new commits)
- [x] All tests passing (48/48)
- [x] Clippy clean (zero warnings)
- [x] Version bumped to 1.5.0
- [x] README updated with installation + examples
- [x] Build artifacts ready (wheel + sdist)
- [ ] GitHub push completed (requires credential setup)
- [ ] GitHub release created (requires GitHub access)
- [ ] PyPI upload completed (requires PyPI token)

---

## Troubleshooting

### "Device not configured" error on macOS

This is a credential helper issue. Try:

```bash
git config --global credential.helper manager-core
# or
git config --global credential.helper ""
# Then re-authenticate when prompted
```

### PyPI upload fails

Ensure you have:
- Valid PyPI account: https://pypi.org/account/register/
- Valid API token: https://pypi.org/manage/account/tokens/
- twine installed: `pip install twine --upgrade`

### Package not found on PyPI

PyPI takes 5-15 minutes to index new packages. Check:
https://pypi.org/project/streampdf/

---

## Next Steps

After v1.5.0 is released:

1. Announce on social media / communities
2. Pin release on GitHub
3. Monitor PyPI download stats
4. Begin Phase 4 (Semantic understanding, citation networks)

---

For questions or issues, see: https://github.com/Mullassery/StreamPDF/issues
