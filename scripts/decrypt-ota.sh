#!/bin/zsh
# Decrypt an Apple OTA .aea with its published extraction key.
# usage: decrypt-ota.sh <in.aea> <base64-key> <out.zip>
set -euo pipefail
aea decrypt -i "$1" -o "$3" -key-value "base64:$2"
echo "decrypted -> $3"; ls -l "$3"
