#!/bin/zsh
# Restore the staged HomeView VM: boot it in DFU, run the online restore,
# then shut it down. cfw install (root) comes after this.
set -uo pipefail
cli=${0:A:h:h}/vphone-cli/.build/XcodeBundle/Build/Products/Debug/VPhone.bundle/Contents/MacOS/vphone-cli
name=${1:-homeview}

"$cli" vm launch "$name" --dfu --headless &
dfu=$!
for i in {1..60}; do [[ -s ~/.vphone/machines/$name/udid-prediction.txt ]] && break; sleep 1; done
"$cli" restore "$name"
rc=$?
"$cli" vm stop "$name"
wait $dfu
exit $rc
