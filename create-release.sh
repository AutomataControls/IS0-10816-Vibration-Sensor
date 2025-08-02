#!/bin/bash
# Create GitHub release

VERSION="v3.0.0-alpha.1"
TITLE="v3.0.0-alpha.1 - Database & UI Update"

echo "Creating GitHub Release: $VERSION"
echo "=================================="
echo

# Create git tag
echo "Creating tag..."
git tag -a "$VERSION" -m "$TITLE"

# Push tag to GitHub
echo "Pushing tag to GitHub..."
git push origin "$VERSION"

echo
echo "Tag created and pushed!"
echo
echo "Now go to GitHub to create the release:"
echo "1. Visit: https://github.com/AutomataControls/IS0-10816-Vibration-Sensor/releases/new"
echo "2. Select tag: $VERSION"
echo "3. Title: $TITLE"
echo "4. Mark as 'Pre-release' (alpha)"
echo "5. Copy release notes from RELEASE_NOTES.md"
echo
echo "Or use GitHub CLI:"
echo "gh release create $VERSION --title \"$TITLE\" --notes-file RELEASE_NOTES.md --prerelease"