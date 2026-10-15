#!/usr/bin/env python3
"""Slipgate Android experimental 0.2 overlay for pinned ByeByeDPI 1.8.2. GPL-3.0."""
import argparse
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

def domains(file):
    out = set()
    for line in file.read_text(encoding="utf-8-sig").splitlines():
        h=line.split("#",1)[0].strip().lower()
        if re.fullmatch(r"(?:[a-z0-9_-]+\.)+[a-z0-9_-]+",h):
            out.add(h)
    return out

def targets(folder):
    out=(domains(folder/"list-general.txt")|domains(folder/"list-google.txt"))-domains(folder/"list-exclude.txt")
    if not {"youtube.com","discord.com"}.issubset(out):
        raise ValueError("Original Slipgate 1.8.0 site targets missing")
    return sorted(out)

def patch(file, before, after):
    s=file.read_text(encoding="utf-8")
    if s.count(before)!=1:
        raise ValueError("Upstream change detected: "+str(file)+": "+before)
    file.write_text(s.replace(before,after,1),encoding="utf-8")

def apply(repo,lists):
    gradle=repo/"app/build.gradle.kts"
    if not gradle.is_file():
        raise FileNotFoundError("Expected ByeByeDPI v.1.8.2 checkout")
    patch(gradle,'applicationId = "io.github.romanvht.byedpi"',
          'applicationId = "com.farliner.slipgate.android"')
    patch(gradle,'versionName = "1.8.2"',
          'versionName = "0.3.1-slipgate"')
    manifest=repo/"app/src/main/AndroidManifest.xml"
    m=manifest.read_text(encoding="utf-8")
    for original in ('@mipmap/ic_launcher_round','@mipmap/ic_launcher','@mipmap/ic_banner'):
        m=m.replace(original,'@drawable/slipgate_icon')
    manifest.write_text(m,encoding="utf-8")
    res=repo/"app/src/main/res"
    icons=res/"drawable-nodpi"
    icons.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(lists/"slipgate-icon.png",icons/"slipgate_icon.png")
    for lang in ("values","values-en"):
        file=res/lang/"strings.xml"
        patch(file,'<string name="app_name">ByeByeDPI</string>',
                   '<string name="app_name">Slipgate Android</string>')
    # ByeByeDPI automatically discovers proxytest_*.sites for the strategy scanner.
    # This target list is not a bypass strategy; the user can enable it for testing.
    assets=repo/"app/src/main/assets"
    assets.mkdir(parents=True,exist_ok=True)
    hosts=targets(lists)
    (assets/"proxytest_slipgate.sites").write_text("\n".join(hosts)+"\n",encoding="utf-8")
    ET.parse(manifest)
    print("Slipgate 0.2 patch applied. Original target domains:",len(hosts))

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--repo",type=Path,required=True)
    a.add_argument("--lists",type=Path,required=True)
    args=a.parse_args()
    apply(args.repo,args.lists)
