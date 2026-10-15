# Slipgate Android v0.1.0 (experimental)

An early Android port of Slipgate 1.8.0's DNS/domain targeting and DPI-desynchronization concept. **Not verified on real Android devices.** This is not an official Slipgate release.

## Mechanism

Android VpnService + local tun2socks + a native ByeDPI TCP/UDP DPI-desynchronization engine (not a remote VPN). The build fetches ByeDPI Android release v1.2.0 at commit 9d289f096ed8373dd3734ab9966312c4c9e8d0aa and applies the port overlay. Root privileges are not required.

## Getting an APK

Actions → **Build Android APK** → **Run workflow**. Successful workflow runs produce **SlipgateAndroid-debug-APK**, containing the debug-signed APK for installation. On your Android phone approve VPN permission, pick a profile in Settings, and turn the VPN mode on. Disconnect/reconnect the VPN after changing profiles.

Four profiles: General (Slipgate-derived host list), YouTube (experimental), Discord, Manual (native ByeDPI settings). The bypass results vary by ISP. Some original Windows strategies and the original Telegram WS proxy are *not yet ported*; hard IP blocks may still apply.

## Build locally

Requires Linux, JDK 17, Android SDK with NDK 26.3, Python, Git.

    bash scripts/prepare_upstream.sh
    cd upstream && bash ./gradlew :app:assembleDebug

## Attribution and license

This port is GPL-3.0. Lists adapted from the user's Slipgate 1.8.0 archive (original author: tenstepsbeforedecay). Upstream ByeDPI Android (dovecoteescapee), native ByeDPI (hufrea), and hev-socks5-tunnel (heiher) retain their respective license and attribution notices in the source downloaded for build. Please retain these on redistribution.
