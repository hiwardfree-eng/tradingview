"""Build modified TradingView IPA from NOVA TECH APP base."""
import os, shutil, zipfile, plistlib

BASE = os.path.dirname(os.path.abspath(__file__))
SOURCE_IPA = "C:/Users/Chichi/Downloads/NOVA TECH APP_1.0.1_1775132453.ipa"
OUTPUT_IPA = os.path.join(BASE, "IPA", "tradingview.ipa")
PAYLOAD_DIR = os.path.join(BASE, "IPA", "Payload")
APP_DIR = os.path.join(PAYLOAD_DIR, "NovaTech.app")
RENDER_URL = os.environ.get("TV_RENDER_URL", "https://tradingview-k7u2.onrender.com")

def build():
    # Clean
    if os.path.exists(PAYLOAD_DIR):
        shutil.rmtree(PAYLOAD_DIR)
    os.makedirs(APP_DIR, exist_ok=True)

    # Extract original IPA
    with zipfile.ZipFile(SOURCE_IPA, 'r') as z:
        z.extractall(os.path.join(BASE, "IPA"))

    # Copy our new main.html (overwrite the old one)
    src_html = os.path.join(BASE, "IPA", "main.html")
    dst_html = os.path.join(APP_DIR, "main.html")
    if os.path.exists(src_html):
        shutil.copy2(src_html, dst_html)
        print("main.html copied")

    # Inject Render URL
    with open(dst_html, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('"https://tradingview.onrender.com"', f'"{RENDER_URL}"')
    with open(dst_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"URL injected: {RENDER_URL}")

    # Update Info.plist — keep original bundle ID
    plist_path = os.path.join(APP_DIR, "Info.plist")
    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)

    plist['CFBundleDisplayName'] = 'TradingView'
    plist['CFBundleName'] = 'TradingView Terminal'
    plist['CFBundleShortVersionString'] = '1.0.0'
    plist['CFBundleVersion'] = '1'
    plist['CFBundleDevelopmentRegion'] = 'es'

    with open(plist_path, 'wb') as f:
        plistlib.dump(plist, f)
    print("Info.plist updated (bundle ID kept original)")

    # Build IPA
    os.makedirs(os.path.dirname(OUTPUT_IPA), exist_ok=True)
    if os.path.exists(OUTPUT_IPA):
        os.remove(OUTPUT_IPA)

    with zipfile.ZipFile(OUTPUT_IPA, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(PAYLOAD_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, os.path.dirname(PAYLOAD_DIR))
                z.write(filepath, arcname)

    shutil.rmtree(PAYLOAD_DIR)
    print(f"IPA built: {OUTPUT_IPA} ({os.path.getsize(OUTPUT_IPA)} bytes)")
    return True

if __name__ == "__main__":
    build()
