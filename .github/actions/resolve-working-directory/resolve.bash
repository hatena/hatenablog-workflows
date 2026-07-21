#!/usr/bin/env bash

set -euo pipefail

config_files=()
while IFS= read -r -d '' config_file; do
  config_files+=("$config_file")
done < <(git ls-files -z -- 'blogsync.yaml' '**/blogsync.yaml')

if [[ ${#config_files[@]} -eq 0 ]]; then
  echo "::error title=blogsync.yaml was not found::Add exactly one tracked blogsync.yaml file to the repository."
  exit 1
fi

if [[ ${#config_files[@]} -gt 1 ]]; then
  printf -v matches ' %q' "${config_files[@]}"
  echo "::error title=Multiple blogsync.yaml files found::Expected exactly one tracked blogsync.yaml file, but found:${matches}"
  exit 1
fi

working_directory=$(dirname "${config_files[0]}")
echo "working_directory=$working_directory" >> "$GITHUB_OUTPUT"
