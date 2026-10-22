"""Keep the embedded scnet-hpc adapter provenance verifiable."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "vendor-manifest.json"


class VendorManifestTests(unittest.TestCase):
    def test_manifest_records_upstream_and_checksums(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["repository"], "https://github.com/lql341/scnet-hpc")
        self.assertRegex(data["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(data["license"], "MIT")
        self.assertTrue(data["files"])
        self.assertTrue(data["derivatives"])

        for relative, meta in data["files"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertFalse(meta["modified"], relative)
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                meta["sha256"],
                relative,
            )

        for relative, meta in data["derivatives"].items():
            self.assertTrue((ROOT / relative).is_file(), relative)
            self.assertTrue(meta["modified"], relative)
            self.assertEqual(
                hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                meta["sha256"],
                relative,
            )

    def test_adapter_is_local_and_exposes_expected_surface(self):
        text = (ROOT / "scripts" / "scnet_lite.py").read_text(encoding="utf-8")
        self.assertNotIn("import scnet_hpc", text)
        self.assertIn("load_openapi_credentials", text)
        self.assertIn("scnet-hpc-openapi", (ROOT / "scripts" / "scnet_credentials.py").read_text(encoding="utf-8"))
        for method in ("regions", "mkdir", "upload", "submit", "wait", "job", "logs", "download"):
            self.assertIn("def " + method + "(", text)


if __name__ == "__main__":
    unittest.main()
