#!/bin/zsh
# Skip HomeView's setup in a running VM: write Setup Assistant's done keys
# (setup.skip's restart targets SpringBoard and fails, which is expected),
# mark the tvOS buddy finished, then restart BreadBoard so it reads them.
set -uo pipefail
h=${0:A:h}/hostctl.py
vm=${1:-homeview}
python3 -I $h '{"t":"rpc","method":"setup.skip","params":{"force":true}}' $vm 60 >/dev/null
python3 -I $h '{"t":"rpc","method":"settings.set","params":{"domain":"com.apple.purplebuddy","key":"TVBuddyCompletedSuccessfully","value":true}}' $vm 20
python3 -I $h '{"t":"rpc","method":"services.kickstart","params":{"label":"com.apple.BreadBoard","kill":true,"force":true}}' $vm 30
python3 -I $h '{"t":"rpc","method":"setup.status","params":{}}' $vm 20
