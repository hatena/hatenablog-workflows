#!/usr/bin/env bash

set -euo pipefail

repository_root=$(git rev-parse --show-toplevel)
resolver="$repository_root/.github/actions/resolve-working-directory/resolve.bash"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

new_repository() {
  local name=$1
  local path="$tmp/$name"

  mkdir -p "$path"
  git -C "$path" init -q
  echo "$path"
}

assert_resolves_to() {
  local repository=$1
  local expected=$2
  local output="$repository/output"

  (
    cd "$repository"
    GITHUB_OUTPUT="$output" bash "$resolver"
  )

  grep -Fxq "working_directory=$expected" "$output"
}

assert_rejected_with() {
  local repository=$1
  local expected=$2
  local output="$repository/output"
  local log="$repository/log"

  if (
    cd "$repository"
    GITHUB_OUTPUT="$output" bash "$resolver"
  ) >"$log" 2>&1; then
    echo "expected resolver to reject $repository" >&2
    exit 1
  fi

  grep -Fq "$expected" "$log"
}

root_repository=$(new_repository root)
touch "$root_repository/blogsync.yaml"
git -C "$root_repository" add blogsync.yaml
assert_resolves_to "$root_repository" .

subdirectory_repository=$(new_repository subdirectory)
mkdir "$subdirectory_repository/blog"
touch "$subdirectory_repository/blog/blogsync.yaml"
git -C "$subdirectory_repository" add blog/blogsync.yaml
assert_resolves_to "$subdirectory_repository" blog

space_repository=$(new_repository space)
mkdir "$space_repository/blog content"
touch "$space_repository/blog content/blogsync.yaml"
git -C "$space_repository" add "blog content/blogsync.yaml"
assert_resolves_to "$space_repository" "blog content"

missing_repository=$(new_repository missing)
touch "$missing_repository/README.md"
git -C "$missing_repository" add README.md
assert_rejected_with "$missing_repository" "blogsync.yaml was not found"

untracked_repository=$(new_repository untracked)
touch "$untracked_repository/blogsync.yaml"
assert_rejected_with "$untracked_repository" "blogsync.yaml was not found"

multiple_repository=$(new_repository multiple)
mkdir "$multiple_repository/blog"
touch "$multiple_repository/blogsync.yaml" "$multiple_repository/blog/blogsync.yaml"
git -C "$multiple_repository" add blogsync.yaml blog/blogsync.yaml
assert_rejected_with "$multiple_repository" "Multiple blogsync.yaml files found"

echo "resolve-working-directory tests passed"
