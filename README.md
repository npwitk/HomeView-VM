# HomeView VM

Boot Apple's HomeView Software 27.2 (`HomeAccessory17,1`, board J490) in a
virtual machine on an Apple silicon Mac, using
[vphone-cli](https://github.com/Lakr233/vphone-cli) and Apple's Private Cloud
Compute research VM support in Virtualization.framework.

It is not a simulator: the VM runs HomeView's own tvOS-based userland from its
OTA, on top of the cloudOS 26.4 kernel that vphone-cli boots.

> **No Apple software is included in this repository.** You supply the
> HomeView OTA yourself; the scripts download Apple's public IPSWs from
> Apple's CDN. This project is not affiliated with or endorsed by Apple. It is
> for research and education.

## Status

Verified on one machine (Apple M4, macOS 27.2, Xcode 27.2):

- The VM restores, boots HomeView 27.2 (24V514) with no kernel panic, and
  shows HomeView's own "hello" setup screen.
- `scripts/skip-setup.sh` gets past setup to a full-screen HomeView screen.
  Whether that is the home screen has not been confirmed.
- The guest reaches the internet through NAT.

Not working or untested:

- Setup expects a nearby iPhone over Bluetooth; the VM has none, so setup is
  skipped rather than completed.
- Apple Account sign-in, iCloud, Home/HomeKit and other services that verify
  the device fail: the VM has no genuine hardware identity. **Do not sign in
  with your real Apple Account.**
- `HomeAccessory17,2` (J491) is not added.
- The 1088×1088 @2x, 220 ppi screen is inferred (boot artwork, device tree
  `dot-pitch`), not a published panel size.
- Apps, Siri, audio, video and long-term stability are untested.

## What the patch changes

`patches/vphone-cli-homeview.patch` applies to vphone-cli commit
[`39324ee`](https://github.com/Lakr233/vphone-cli/commit/39324ee7fcbb1d909bfa293f6188a8ef752ba734)
(2026-10-30):

- **Device.** Adds `HomeAccessory17,1` ("HomeView"), restored like the Apple TV
  4K: the Apple TV HD 26.6 IPSW as the restore base, cloudOS 26.4 beta
  (23E5207q) for the boot chain, and the device tree and userland from the
  HomeView OTA. It uses the `tvos-4k` preset and Apple TV setup handling.
- **Catalog.** Lists the 27.2 (24V514) OTA with its size and public AEA key,
  over the HD's 26.6 base. Only the asset's file name is known, not its CDN
  folder, so the catalog cannot download it; you place it in the cache.
- **Sandbox lookups** (`system-breadboard-exp-backboard_lookups`, on by
  default for this device). HomeView's `BreadBoard` (its shell) and
  `userprofilesd` declare the `temporary-sandbox` profile, whose cloudOS 26.4
  version denies lookups that 27.2's allows (error 159, "Sandbox
  restriction"). Without them `BKSDisplayServicesStart` traps, `userprofilesd`
  cannot create the guest persona through UserManager, and BreadBoard stops
  waiting for it, so the guest stays on the Apple logo. The patch adds the
  missing services to each binary's own mach-lookup exceptions and ad-hoc
  re-signs it, as vphone-cli already does for iOS 27's Campo.

## Requirements

- A physical Apple silicon Mac on **macOS 27** or later (HomeView 27's payload
  uses LZRAVEN compression, which only macOS 27 unpacks). It cannot run inside
  a VM.
- Xcode with the iOS and tvOS SDKs (tested with Xcode 27.2).
- Host security settings changed in macOS Recovery (below).
- Disk space: about 13 GB of firmware downloads (6.5 GB HomeView OTA, 5.3 GB
  Apple TV HD IPSW, 1.1 GB cloudOS), a 48 GB sparse VM disk, and **at least
  50 GiB free** when `cfw install` runs; it refuses to start with less.
- An internet connection: the restore fetches a signing ticket from Apple.

## Setup

### 1. Host security (macOS Recovery)

Shut down, hold the power button, choose Options, then Utilities › Terminal:

```sh
csrutil enable --without debug
csrutil allow-research-guests enable
```

SIP stays on with only its debugging restrictions relaxed. To undo it later,
run `csrutil allow-research-guests disable` and `csrutil enable` in Recovery.
See vphone-cli's
[Host Setup](https://github.com/Lakr233/vphone-cli/blob/main/Documents/Guides/host-setup.md).

### 2. vphone-cli with the patch

```sh
git clone <this repository> HomeView-VM
cd HomeView-VM
git clone https://github.com/Lakr233/vphone-cli.git
git -C vphone-cli checkout 39324ee7fcbb1d909bfa293f6188a8ef752ba734
git -C vphone-cli apply ../patches/vphone-cli-homeview.patch
(cd vphone-cli && xcodebuild -workspace VPhone.xcworkspace -scheme VPhone \
  -configuration Debug -destination 'platform=macOS,arch=arm64' \
  -derivedDataPath .build/XcodeBundle build)
```

Then allow the build's VM binary. AMFI's allowance is tied to this exact
signature, so **repeat this after every rebuild**:

```sh
B=vphone-cli/.build/XcodeBundle/Build/Products/Debug/VPhone.bundle/Contents/MacOS
sudo $B/vphone-escalator allow $B/vphone-vm
```

### 3. The HomeView OTA

Download the HomeView 27.2 (24V514) full OTA yourself. The Apple Wiki's
"OTA Updates/Apple HomeView/27.2" page lists it as
`91e6292d137569817d83050e9a21c6c93c25af6ab02fbaa7eeddb9ad5439b99a.aea`
(6,509,559,808 bytes). Put it in vphone-cli's cache under the name the
catalog expects; `cp -c` makes an APFS clone that takes no extra space:

```sh
mkdir -p ~/.vphone/ipsws/ota
cp -c /path/to/91e6292d…99a.aea ~/.vphone/ipsws/ota/HomeAccessory17,1_27.2_24V514_OTA.aea
```

### 4. Stage, restore, install, boot

```sh
scripts/prepare-homeview.sh      # creates VM "homeview", downloads the IPSWs, stages and patches firmware
scripts/restore-homeview.sh      # DFU boot and online restore
sudo vphone-cli/.build/XcodeBundle/Build/Products/Debug/VPhone.bundle/Contents/MacOS/vphone-cli \
  cfw install homeview --keep-artifacts
vphone-cli/.build/XcodeBundle/Build/Products/Debug/VPhone.bundle/Contents/MacOS/vphone-cli \
  vm launch homeview
```

`prepare-homeview.sh` starts a temporary cloudOS VM to extract the GPU
driver, so the Recovery change and the `vphone-escalator allow` step must be
done first. Each script takes an optional VM name (default `homeview`).

### 5. Skip setup

Once the "hello" screen appears, with the VM running:

```sh
scripts/skip-setup.sh
```

It writes Setup Assistant's completion keys, sets
`TVBuddyCompletedSuccessfully`, and restarts BreadBoard. vphoned's
`setup.skip` reports a failed SpringBoard restart along the way; HomeView has
no SpringBoard, so that is expected.

## Updating patches later

- `cfw install` deletes the prepared restore tree when it finishes unless you
  pass `--keep-artifacts`; without the tree, run `prepare-homeview.sh` again
  (the downloads are cached).
- After changing only guest-side patches, apply them to the stopped VM with
  `sudo … vphone-cli cfw update-environment homeview`, which needs 10 GiB free
  instead of 50.

## Scripts

| Script | Purpose |
| --- | --- |
| `prepare-homeview.sh` | Create the VM and stage/patch its firmware |
| `restore-homeview.sh` | Boot in DFU and restore |
| `skip-setup.sh` | Mark setup done and restart BreadBoard |
| `decrypt-ota.sh` | Decrypt an OTA `.aea` with its public key (`aea decrypt`) |
| `ota_peek.py` | List or extract files from a decrypted, segmented OTA archive without unpacking it |
| `dt_dump.py` | Print properties of a decompressed device tree |
| `dsc_extract.c` | Extract a dyld shared cache with Xcode's `dsc_extractor.bundle` (`clang -fblocks -o dsc_extract dsc_extract.c`) |
| `hostctl.py` | Send one request to a running VM's host control socket |
| `pull_dir.py` | Copy a folder out of the guest through vphoned |
| `watch_shell.py` | Wait until a guest launchd job stays up or exits |

### Debugging guest daemons

HomeView ships no `log` or `launchctl`. To see a daemon's `os_log` output,
copy its launchd plist with a new `Label`, a `StandardErrorPath` under
`/var/tmp`, and `EnvironmentVariables` `OS_ACTIVITY_DT_MODE=1`; push it with
`hostctl.py '{"t":"push",…}'`, `services.unload` the original (with
`"force":true`), then `services.load` the copy. A reboot restores the
original job. Crash reports are in `/var/mobile/Library/Logs/CrashReporter`.

## Credits

- [vphone-cli](https://github.com/Lakr233/vphone-cli) by Lakr233 and
  contributors (MIT). The patch is a modification of it, and its license
  notice applies to that code.
- The OTA file name and key come from The Apple Wiki.
