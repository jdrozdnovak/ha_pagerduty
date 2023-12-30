#!/bin/sh

jq --version
curl --version

releases=$(curl -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases" | jq -r --arg BRANCH "$MERGED_BRANCH" '.[] | select(.target_commitish == $BRANCH) | "\(.id) \(.tag_name)"')

echo $releases

for release in $releases; do
    release_id=$(echo $release | cut -d ' ' -f1)
    tag_name=$(echo $release | cut -d ' ' -f2)

    curl -X DELETE -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases/$release_id"
    echo "Deleted Release $release_id"

    curl -X DELETE -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/${GITHUB_REPOSITORY}/git/refs/tags/$tag_name"
    echo "Deleted Tag $tag_name"
done