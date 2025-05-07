#!/bin/bash

set -eu

BRANCH_NAME=update-hatenablog-workflows-digest

git rev-parse --verify "$BRANCH_NAME" 2>/dev/null && git branch -d "$BRANCH_NAME"
git switch -c "$BRANCH_NAME"

current_reference=$(git grep -h -oP '(?<=hatena/hatenablog-workflows/.github/actions/setup@)([0-9a-f]+)' | head -1)
current_revision=$(git show --format='%H' --no-patch)
git grep --name-only "$current_reference"  | xargs -L 1 -I@  gsed -i @ -e "s/$current_reference/$current_revision/g"

git add .github
git commit -m "update hatenablog-workflows digest"
