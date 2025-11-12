# PyPI Publishing Guide

How to publish Fidelity Portfolio Tracker to the Python Package Index (PyPI).

## Prerequisites

- PyPI account (register at https://pypi.org/)
- TestPyPI account for testing (https://test.pypi.org/)
- API tokens for both PyPI and TestPyPI

## Setup

### 1. Install Build Tools

```bash
pip install --upgrade pip
pip install build twine
```

### 2. Configure PyPI Credentials

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

Set secure permissions:

```bash
chmod 600 ~/.pypirc
```

## Building the Package

### 1. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info/
```

### 2. Update Version

Edit version in multiple files:
- `pyproject.toml` - `version = "2.0.1"`
- `setup.py` - `version='2.0.1'`
- `fidelity_tracker/__init__.py` - `__version__ = '2.0.1'`

### 3. Build Distribution

```bash
python -m build
```

This creates:
- `dist/fidelity_portfolio_tracker-2.0.1.tar.gz` (source distribution)
- `dist/fidelity_portfolio_tracker-2.0.1-py3-none-any.whl` (wheel)

### 4. Verify Build

```bash
# Check package
twine check dist/*

# List contents
tar -tzf dist/fidelity_portfolio_tracker-2.0.1.tar.gz | head -20

# Test installation locally
pip install dist/fidelity_portfolio_tracker-2.0.1-py3-none-any.whl
portfolio-tracker --version
pip uninstall fidelity-portfolio-tracker
```

## Publishing

### Test on TestPyPI First

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    fidelity-portfolio-tracker

# Verify it works
portfolio-tracker --version
portfolio-tracker --help

# Uninstall
pip uninstall fidelity-portfolio-tracker
```

### Publish to PyPI

```bash
# Upload to PyPI (production)
twine upload dist/*

# Verify on PyPI
open https://pypi.org/project/fidelity-portfolio-tracker/

# Test installation
pip install fidelity-portfolio-tracker
```

## Post-Publishing

### 1. Create Git Tag

```bash
git tag -a v2.0.1 -m "Release version 2.0.1"
git push origin v2.0.1
```

### 2. Create GitHub Release

1. Go to https://github.com/rlust/Fid-Import/releases
2. Click "Create a new release"
3. Select tag `v2.0.1`
4. Add release notes
5. Attach distribution files from `dist/`

### 3. Update Documentation

- Update README.md with new version
- Update CHANGELOG.md with release notes
- Update version badges

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Publish to Test PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
        run: |
          twine upload --repository testpypi dist/*

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          twine upload dist/*
```

Add secrets to GitHub repository:
- `PYPI_API_TOKEN` - Your PyPI API token
- `TEST_PYPI_API_TOKEN` - Your TestPyPI API token

## Version Management

### Semantic Versioning

Follow https://semver.org/:

- **MAJOR** (2.x.x) - Incompatible API changes
- **MINOR** (x.1.x) - New features, backwards compatible
- **PATCH** (x.x.1) - Bug fixes, backwards compatible

### Version Bumping Script

Create `scripts/bump_version.sh`:

```bash
#!/bin/bash

# Usage: ./scripts/bump_version.sh 2.0.1

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new_version>"
    exit 1
fi

# Update version in files
sed -i.bak "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i.bak "s/version='.*'/version='$NEW_VERSION'/" setup.py
sed -i.bak "s/__version__ = '.*'/__version__ = '$NEW_VERSION'/" fidelity_tracker/__init__.py

# Remove backup files
rm -f pyproject.toml.bak setup.py.bak fidelity_tracker/__init__.py.bak

echo "Updated version to $NEW_VERSION"
echo "Remember to:"
echo "  1. Update CHANGELOG.md"
echo "  2. Commit changes"
echo "  3. Create git tag: git tag -a v$NEW_VERSION -m 'Release $NEW_VERSION'"
echo "  4. Push tag: git push origin v$NEW_VERSION"
```

Make it executable:

```bash
chmod +x scripts/bump_version.sh
./scripts/bump_version.sh 2.0.1
```

## Troubleshooting

### Upload Fails with "File already exists"

PyPI doesn't allow re-uploading the same version. Solutions:

1. Bump version number
2. Delete from PyPI (if possible)
3. Use a post-release version: `2.0.1.post1`

### Missing Dependencies

Ensure all dependencies are in `install_requires` in setup.py and `dependencies` in pyproject.toml.

### Import Errors After Install

Check:
- Package structure is correct
- `__init__.py` files exist
- MANIFEST.in includes necessary files

### Wheel Build Fails

```bash
# Install wheel package
pip install wheel

# Build wheel explicitly
python setup.py bdist_wheel
```

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning**
3. **Keep a detailed CHANGELOG.md**
4. **Tag releases in git**
5. **Create GitHub releases**
6. **Test installation in clean environment**:
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install fidelity-portfolio-tracker
   portfolio-tracker --version
   deactivate
   rm -rf test_env
   ```

7. **Verify on multiple Python versions**:
   ```bash
   for version in 3.8 3.9 3.10 3.11 3.12; do
       python$version -m pip install fidelity-portfolio-tracker
       python$version -m portfolio_tracker --version
   done
   ```

## Yanking a Release

If you need to remove a broken release:

```bash
# Yank the release (users can still install if pinned)
twine yank fidelity-portfolio-tracker==2.0.1 \
    -r pypi \
    -m "Broken release, use 2.0.2 instead"
```

## Package Statistics

View download statistics:
- https://pypistats.org/packages/fidelity-portfolio-tracker
- https://pepy.tech/project/fidelity-portfolio-tracker

## Support

If you encounter issues:

1. Check the [PyPI help](https://pypi.org/help/)
2. Review [Python Packaging User Guide](https://packaging.python.org/)
3. Ask on [Python Packaging Discourse](https://discuss.python.org/c/packaging/14)

## Checklist

Before each release:

- [ ] All tests pass (`pytest`)
- [ ] Code quality checks pass (`black`, `flake8`, `mypy`)
- [ ] Version bumped in all files
- [ ] CHANGELOG.md updated
- [ ] README.md reviewed
- [ ] Build succeeds (`python -m build`)
- [ ] Package check passes (`twine check dist/*`)
- [ ] Tested on TestPyPI
- [ ] Git tag created
- [ ] GitHub release created
- [ ] Documentation updated
