"""Build modified TradingView IPA from NOVA TECH APP base."""
import os, shutil, zipfile, plistlib, tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_IPA = "C:/Users/Chichi/Downloads/NOVA TECH APP_1.0.1_1775132453.ipa"
OUTPUT_IPA = os.path.join(BASE_DIR, "IPA", "tradingview.ipa")
PAYLOAD_DIR = os.path.join(BASE_DIR, "IPA", "Payload")
APP_DIR = os.path.join(PAYLOAD_DIR, "NovaTech.app")

def build():
    # Clean
    if os.path.exists(PAYLOAD_DIR):
        shutil.rmtree(PAYLOAD_DIR)
    os.makedirs(APP_DIR, exist_ok=True)

    # Extract original IPA (zip has Payload/ prefix)
    with zipfile.ZipFile(SOURCE_IPA, 'r') as z:
        z.extractall(os.path.join(BASE_DIR, "IPA"))

    # Verify PRO binary exists
    pro_path = os.path.join(APP_DIR, "PRO")
    if not os.path.exists(pro_path):
        print("ERROR: PRO binary not found in IPA")
        return False

    # Copy new main.html
    src_html = os.path.join(BASE_DIR, "IPA", "main.html")
    if os.path.exists(src_html):
        shutil.copy2(src_html, os.path.join(APP_DIR, "main.html"))
        print("main.html copied")

    # Modify Info.plist
    plist_path = os.path.join(APP_DIR, "Info.plist")
    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)

    # Customize app metadata
    plist['CFBundleDisplayName'] = 'TradingView'
    plist['CFBundleName'] = 'TradingView Terminal'
    plist['CFBundleIdentifier'] = 'com.tradingview.terminal'
    plist['CFBundleShortVersionString'] = '1.0.0'
    plist['CFBundleVersion'] = '1'
    plist['CFBundleDevelopmentRegion'] = 'es'
    plist['LSRequiresIPhoneOS'] = True
    plist['UIApplicationSupportsMultipleScenes'] = False
    plist['MinimumOSVersion'] = '12.0'

    # Remove signature files (must be re-signed by user)
    sig_dir = os.path.join(APP_DIR, "_CodeSignature")
    if os.path.exists(sig_dir):
        shutil.rmtree(sig_dir)
        print("_CodeSignature removed (app needs re-signing)")

    esign_file = os.path.join(APP_DIR, "SignedByEsign")
    if os.path.exists(esign_file):
        os.remove(esign_file)
        print("SignedByEsign removed")

    with open(plist_path, 'wb') as f:
        plistlib.dump(plist, f)
    print("Info.plist updated")

    # Create output IPA dir
    os.makedirs(os.path.dirname(OUTPUT_IPA), exist_ok=True)

    # Build IPA (zip)
    if os.path.exists(OUTPUT_IPA):
        os.remove(OUTPUT_IPA)

    with zipfile.ZipFile(OUTPUT_IPA, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(PAYLOAD_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, PAYLOAD_DIR)
                z.write(filepath, arcname)

    # Clean up
    shutil.rmtree(PAYLOAD_DIR)
    print(f"IPA built: {OUTPUT_IPA} ({os.path.getsize(OUTPUT_IPA)} bytes)")
    return True

if __name__ == "__main__":
    build()
