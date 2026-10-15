# Slipgate Android 0.3.1 — experimental (Telegram / TikTok / TCP+UDP)

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

## v0.3 additions (experimental)
- **Integrated Telegram MTProto WebSocket proxy:** MIT-licensed Kotlin implementation from crim50n/tg-ws-proxy-android at pinned commit 41f4d4ff9a5f14c5ffbc5b9a4662099cd11c7738. Open via main screen menu **Telegram MTProto / WS**, start its local listener, then tap **Open in Telegram** to configure proxy; not the same service as ByeDPI. The proxy is bound to localhost by default and does not claim proven Telegram connectivity yet.
- **TikTok domains** available in the built-in strategy tester as `TikTok`; video and upload may need different TCP/UDP strategies.
- **Apps**: Main screen menu **DPI: приложения и TCP/UDP**, then **App filter / Выбор приложений** (existing ByeByeDPI VPN app list). Choose a whitelist to apply DPI only to selected apps or disable filter for all. This affects the VPN mode, not Proxy mode.
- **TCP/UDP modes** in Settings: Automatic (keep tested strategy), TCP only (disable UDP transport; may break video/calls), TCP + UDP (add an experimental UDP-desync stage). The last mode is not guaranteed and is not a kernel-packet Zapret-equivalent. Restart service after changing.
- Android 8+ is now required by integrated Telegram module (formerly Android 5+ for standalone ByeByeDPI). GPL-3.0 for Slipgate/ByeByeDPI; Telegram module is MIT (copyright crim50n), see upstream LICENSE.
\n## v0.3.1 quick tile fix\n- The app's single Quick Settings tile now has the Slipgate app icon and always toggles **ByeDPI VPN mode** (not local SOCKS proxy mode), regardless of the selected main-screen connection mode.\n- The second Telegram quick tile is removed to avoid two tiles for separate services; Telegram MTProto/WS proxy stays available from the menu.\n- If VPN permission is missing, the tile opens the main activity for approval instead of silently doing nothing.\n- Background tile state sync is requested when the VPN status changes. On some Android launchers you may need to remove the old cached tiles and add the new Slipgate tile again.\n- This release does **not yet** implement SpeedFix/Xray or a hybrid tunnel. Do not assume importing the subscription into V2RayTun makes ByeDPI handle TikTok or ChatGPT.\n