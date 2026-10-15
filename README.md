# Slipgate Android 0.2.0 — experimental

**The v0.1.0 APK was not verified to bypass DPI and failed a real user's test. Do not treat a successful build or a Connected status as evidence that DPI bypass works.**

This project has now switched to the maintained [ByeByeDPI 1.8.2](https://github.com/romanvht/ByeByeDPI/releases/tag/v.1.8.2) codebase (October 2, 2026; pinned commit 96a3c1ff555043d915af814aa4f0e9a572c89aba). This provides a real strategy scanner, diagnostics, app filtering, DNS settings, a modern native ByeDPI engine and local Android VPN service. It is not a byte-for-byte port of the Windows Zapret/winws engine.

Slipgate-specific content: the original icon and bundled Slipgate 1.8.0 domain list, exposed as an extra option under Domain lists in the strategy tester. The list must be enabled there if you wish to test these domains. No one bypass strategy is claimed to work on all networks.

## First Android test

1. Uninstall the earlier Slipgate Android 0.1.0 debug APK before installing this new build; fresh GitHub Actions runs do not share a stable debug signing key.
2. Download the universal debug APK from the successful Build Android APK GitHub Actions run.
3. Permit local VPN creation (no external VPN server). Disable any other active Android VPN.
4. Open the strategy test (Подбор стратегий); select which domain lists to test, including Slipgate if desired. Run it and choose a strategy that actually succeeds for your current network.
5. Start the local VPN and check specific previously blocked resources, including video playback, not just site homepages.
6. If it fails, collect the built-in diagnostic report. Connected only means the VPN service is active.

## Build

The GitHub workflow clones the exact ByeByeDPI 1.8.2 source revision with native submodules, applies scripts/apply_port_v2.py and compiles the universal debug APK using the Android SDK/NDK on GitHub Actions.

This GPL-3.0 project contains derivative work and original site lists from Slipgate 1.8.0. All upstream component copyrights belong to their respective authors. No guarantee of circumvention, privacy, or Android compatibility is made.

Roadmap: device network tests, accurate Slipgate-equivalent strategies where available, a Slipgate-specific UI, and separate Telegram proxy integration.
