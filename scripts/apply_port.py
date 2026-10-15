#!/usr/bin/env python3
"""Android overlay for pinned ByeDPI Android v1.2.0, using Slipgate 1.8.0 domain lists. GPL-3.0."""
import argparse
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

def read_domains(file):
    found=set()
    for line in file.read_text(encoding="utf-8-sig").splitlines():
        host=line.split("#",1)[0].strip().lower()
        if re.fullmatch(r"(?:[a-z0-9_-]+\.)+[a-z0-9_-]+",host):
            found.add(host)
    return found

def load_profiles(folder):
    all_hosts=(read_domains(folder/"list-general.txt") |
               read_domains(folder/"list-google.txt")) - read_domains(folder/"list-exclude.txt")
    youtube={x for x in all_hosts if any(t in x for t in ("youtube","youtu.be","googlevideo","ytimg","ggpht","youtubei","googleusercontent"))}
    discord={x for x in all_hosts if "discord" in x or x=="dis.gd"}
    if not youtube or not discord: raise RuntimeError("Missing target domains")
    return [sorted(all_hosts),sorted(youtube),sorted(discord)]

def replace(file,original,replacement):
    s=file.read_text(encoding="utf-8")
    if s.count(original)!=1: raise RuntimeError("Missing unique patch anchor in "+str(file))
    file.write_text(s.replace(original,replacement,1),encoding="utf-8")

def apply(root,folder):
    src=root/"app/src/main"
    gradle=root/"app/build.gradle.kts"
    if not gradle.is_file(): raise FileNotFoundError("Expected ByeDPI Android source checkout")
    replace(gradle,'applicationId = "io.github.dovecoteescapee.byedpi"',
            'applicationId = "com.farliner.slipgate.android"')
    replace(gradle,'versionName = "1.2.0"','versionName = "0.1.0-slipgate"')
    replace(gradle,'    compileSdk = 34','    compileSdk = 34\n    ndkVersion = "26.3.11579264"')
    strings=src/"res/values/strings.xml"
    replace(strings,'<string name="app_name">ByeDPI</string>',
            '<string name="app_name">Slipgate Android</string>')
    replace(strings,'<string name="notification_title">ByeDPI</string>',
            '<string name="notification_title">Slipgate Android</string>')
    en=src/"res/values/slipgate_profiles.xml"
    en.write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
<string name="slipgate_profile">Slipgate profile</string>
<string-array name="slipgate_labels">
<item>General - Slipgate domains</item><item>YouTube (experimental UDP)</item>
<item>Discord</item><item>Manual ByeDPI settings</item>
</string-array>
<string-array name="slipgate_values">
<item>general</item><item>youtube</item><item>discord</item><item>manual</item>
</string-array>
</resources>""",encoding="utf-8")
    ru=src/"res/values-ru"
    ru.mkdir(exist_ok=True)
    (ru/"slipgate_profiles.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
<string name="slipgate_profile">Профиль Slipgate</string>
<string-array name="slipgate_labels">
<item>Общий - домены Slipgate</item><item>YouTube (экспериментальный UDP)</item>
<item>Discord</item><item>Ручные настройки ByeDPI</item>
</string-array>
</resources>""",encoding="utf-8")
    settings=src/"res/xml/main_settings.xml"
    replace(settings,'    <androidx.preference.PreferenceCategory\n        android:title="@string/about_category">',
    """    <androidx.preference.PreferenceCategory
        android:title="@string/slipgate_profile">
        <DropDownPreference
            android:key="slipgate_profile"
            android:title="@string/slipgate_profile"
            android:entries="@array/slipgate_labels"
            android:entryValues="@array/slipgate_values"
            android:defaultValue="general"
            app:useSimpleSummaryProvider="true" />
    </androidx.preference.PreferenceCategory>

    <androidx.preference.PreferenceCategory
        android:title="@string/about_category">""")
    # Vector launcher icon is self-contained (no external binary required).
    draw=src/"res/drawable"
    draw.mkdir(exist_ok=True)
    icon=draw/"slipgate_icon.xml"
    icon.write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
android:width="108dp" android:height="108dp"
android:viewportWidth="108" android:viewportHeight="108">
<path android:fillColor="#101828" android:pathData="M0,0 L108,0 L108,108 L0,108 Z"/>
<path android:fillColor="#35E1CE" android:pathData="M60,8 L27,57 L48,57 L39,100 L84,44 L59,44 Z"/>
</vector>""",encoding="utf-8")
    manifest=src/"AndroidManifest.xml"
    text=manifest.read_text(encoding="utf-8")
    for name in ("ic_launcher","ic_launcher_foreground","ic_launcher_round"):
        text=text.replace("@mipmap/"+name,"@drawable/slipgate_icon")
    manifest.write_text(text,encoding="utf-8")
    general,youtube,discord=load_profiles(folder)
    fmt=lambda hosts: json.dumps("\n".join(hosts))
    kotlin="""// Slipgate Android GPL-3.0: Android-compatible approximations of Windows profiles
package io.github.dovecoteescapee.byedpi.core
import android.content.SharedPreferences
object SlipgateProfiles {
  private val GENERAL = %s
  private val YOUTUBE = %s
  private val DISCORD = %s
  fun resolve(p: SharedPreferences): ByeDpiProxyPreferences {
    return when (p.getString("slipgate_profile","general")) {
      "general" -> ByeDpiProxyUIPreferences(
        hostsMode=ByeDpiProxyUIPreferences.HostsMode.Blacklist,
        hosts=GENERAL, desyncMethod=ByeDpiProxyUIPreferences.DesyncMethod.Disorder,
        splitPosition=1, splitAtHost=true, desyncHttp=true, desyncHttps=true, desyncUdp=false)
      "youtube" -> ByeDpiProxyUIPreferences(
        hostsMode=ByeDpiProxyUIPreferences.HostsMode.Blacklist,
        hosts=YOUTUBE, desyncMethod=ByeDpiProxyUIPreferences.DesyncMethod.Fake,
        fakeTtl=8, fakeSni="www.google.com", splitPosition=1,
        desyncHttp=true, desyncHttps=true, desyncUdp=true, udpFakeCount=3)
      "discord" -> ByeDpiProxyUIPreferences(
        hostsMode=ByeDpiProxyUIPreferences.HostsMode.Blacklist,
        hosts=DISCORD, desyncMethod=ByeDpiProxyUIPreferences.DesyncMethod.Disorder,
        splitPosition=1, splitAtHost=true, desyncHttp=true, desyncHttps=true, desyncUdp=false)
      else -> ByeDpiProxyPreferences.fromSharedPreferences(p)
    }
  }
}
""" % (fmt(general),fmt(youtube),fmt(discord))
    (src/"java/io/github/dovecoteescapee/byedpi/core/SlipgateProfiles.kt").write_text(kotlin,encoding="utf-8")
    for svc in ("ByeDpiVpnService.kt","ByeDpiProxyService.kt"):
        f=src/"java/io/github/dovecoteescapee/byedpi/services"/svc
        replace(f,"ByeDpiProxyPreferences.fromSharedPreferences(getPreferences())",
                "SlipgateProfiles.resolve(getPreferences())")
        replace(f,"import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyPreferences",
                "import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyPreferences\nimport io.github.dovecoteescapee.byedpi.core.SlipgateProfiles")
    for f in (en,ru/"slipgate_profiles.xml",settings,manifest,icon): ET.parse(f)
    print("Slipgate Android port applied",len(general),len(youtube),len(discord))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--lists",required=True,type=Path)
    a=p.parse_args()
    apply(a.repo,a.lists)
