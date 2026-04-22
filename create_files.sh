#!/bin/bash
set -e

FILES_PER_DIR="${1:-5000}"

create_files() {
    local dir="$1"
    mkdir -p "$dir"
    echo "Creating $FILES_PER_DIR files in $dir..."
    (cd "$dir" && touch $(seq -f "file_%g.txt" 1 "$FILES_PER_DIR"))
}

TOP_LEVEL_DIRS=10
DEPTH=10
TOTAL_DIRS=$((TOP_LEVEL_DIRS * DEPTH))

for t in $(seq 1 $TOP_LEVEL_DIRS); do
    path="top_level_directory_with_a_very_long_name_for_testing_purposes_${t}"
    create_files "$path"

    for n in $(seq 2 $DEPTH); do
        path="$path/deeply_nested_subdirectory_with_a_very_long_name_for_testing_purposes_level_${n}"
        create_files "$path"
    done
done

echo "Done. Created $(($TOTAL_DIRS * FILES_PER_DIR)) empty files total."
