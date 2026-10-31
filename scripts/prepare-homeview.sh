#!/bin/zsh
# Create the HomeView VM and stage its firmware (no root, no boot).
# Needs vphone-cli/ built with patches/vphone-cli-homeview.patch applied.
set -euo pipefail
cli=${0:A:h:h}/vphone-cli/.build/XcodeBundle/Build/Products/Debug/VPhone.bundle/Contents/MacOS/vphone-cli
name=${1:-homeview}
hd_ipsw=https://updates.cdn-apple.com/2026SummerFCS/fullrestores/140-67287/F525C1FF-B49B-40AB-A5F4-A6F4A4847407/AppleTV5,3_26.6_23L773_Restore.ipsw
cloud_ipsw=https://updates.cdn-apple.com/private-cloud-compute/c0ecdb4b310cf5239ab2b248dd3098eec297dc5aa3bbe6ada27273262b0b8b64  # cloudOS 26.4 beta (23E5207q)
ota=~/.vphone/ipsws/ota/HomeAccessory17,1_27.2_24V514_OTA.aea  # catalog file name; the catalog supplies the key

[[ -d ~/.vphone/machines/$name ]] || "$cli" vm new "$name" --cpu 4 --memory 4096 --disk-size 48
"$cli" fw set-patches "$name" --preset tvos-4k
"$cli" fw prepare "$name" --device HomeAccessory17,1 \
  --iphone-source "$hd_ipsw" --cloudos-source "$cloud_ipsw" \
  --ota-source "$ota"
"$cli" fw patch "$name"
