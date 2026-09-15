"""Patch only the editable ChatGPT copy. --check verifies; --rollback restores."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import struct

TARGET = Path(r"D:\Documents\ChatGPT-Acrylic\app\resources\app.asar")
BACKUP = TARGET.with_name("app.asar.before-acrylic.bak")
SOURCE_SHA256 = "2bd5b96a48232f3ccf3df6be50965920699ea3a1b4512dcdd770e209fd1f009e"
CSS_ONLY_SHA256 = "2563c33ff3ecadb56d44caf21d5e2b66efc79f8f76ce7482ecc420c25abb3f65"
ASSET = "webview/assets/app-initial-a09fe9cd72bc.css"
MAIN = ".vite/build/main-D8abTQQE.js"


def patched_archive(original, css):
    if hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unknown original build; inspect the new release before patching")
    _, header_size, _, json_size = struct.unpack("<4I", original[:16])
    header = json.loads(original[16:16 + json_size])
    payload = original[8 + header_size:]
    original_payload = payload
    changed = []
    for asset in (ASSET, MAIN):
        entry = header
        for part in asset.split("/"):
            entry = entry["files"][part]
        changed.append((entry, copy.deepcopy(entry)))
        start = int(entry["offset"])
        content = payload[start:start + entry["size"]]
        if asset == ASSET:
            content += b"\n" + css
        else:
            needle = b"backgroundColor:D9,backgroundMaterial:`mica`"
            assert content.count(needle) == 1, "Unexpected native backdrop selector"
            content = content.replace(needle, b"backgroundColor:D9,backgroundMaterial:`acrylic`")
        assert entry["integrity"]["algorithm"] == "SHA256"
        block_size = entry["integrity"]["blockSize"]
        assert block_size > 0
        entry.update(offset=str(len(payload)), size=len(content))
        entry["integrity"]["hash"] = hashlib.sha256(content).hexdigest()
        entry["integrity"]["blocks"] = [hashlib.sha256(content[i:i + block_size]).hexdigest()
                                          for i in range(0, len(content), block_size)]
        payload += content
    encoded = json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    padded = encoded + b"\0" * (-len(encoded) % 4)
    packed_header = struct.pack("<II", 4 + len(padded), len(encoded)) + padded
    # ponytail: retain replaced assets' old bytes; relocation avoids shifting other files.
    result = struct.pack("<II", 4, len(packed_header)) + packed_header + payload
    new_header_size = struct.unpack("<I", result[4:8])[0]
    assert result[8 + new_header_size:8 + new_header_size + len(original_payload)] == original_payload
    for entry, before in changed:
        entry.clear()
        entry.update(before)
    assert header == json.loads(original[16:16 + json_size]), "Unrelated archive metadata changed"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    assert TARGET.resolve() == TARGET, "Refusing a redirected target"
    current = TARGET.read_bytes()
    original = BACKUP.read_bytes() if BACKUP.exists() else current
    css = Path(__file__).with_suffix(".css").read_bytes()
    patched = patched_archive(original, css)
    assert current in (original, patched) or hashlib.sha256(current).hexdigest() == CSS_ONLY_SHA256, \
        "Unexpected local edits; refusing to overwrite"
    if args.check:
        assert current == patched, "Acrylic CSS/native material patch is not installed"
        print("PASS: patched archive matches; every original payload byte and unrelated entry is preserved")
        return
    desired = original if args.rollback else patched
    if current == desired:
        print("Already in the requested state; no changes")
        return
    if not BACKUP.exists():
        with BACKUP.open("xb") as stream:
            stream.write(original)
    temporary = TARGET.with_name("app.asar.acrylic-tmp")
    with temporary.open("xb") as stream:
        stream.write(desired)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, TARGET)
    assert TARGET.read_bytes() == desired
    print("Restored original bundle" if args.rollback else "Applied Acrylic CSS and native material selection to the editable copy")


if __name__ == "__main__":
    main()
