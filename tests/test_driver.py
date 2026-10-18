"""Offline behavioral regressions; never contact SCNet."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import hc
import scnet_lite as lite


class DriverTests(unittest.TestCase):
    def args(self, *extra):
        return hc.parser().parse_args(["crack", "--hashes", str(ROOT / "tests/data/hashes.txt"), "--dict", str(ROOT / "tests/data/dict.txt"), *extra])

    def test_dry_run_is_offline_and_read_only(self):
        with patch.object(lite.Client, "request", side_effect=AssertionError("network")), patch.object(lite.Client, "upload", side_effect=AssertionError("upload")), redirect_stdout(io.StringIO()):
            self.assertEqual(hc.crack(lite.Client(), self.args("--dry-run")), 0)

    def test_invalid_attack_and_resources_before_network(self):
        for options in (("--attack", "1"), ("--dcus-per-node", "5"), ("--mask", "?d"), ("--name", "../old"), ("--walltime", "00:99:00")):
            with self.subTest(options=options), redirect_stdout(io.StringIO()), self.assertRaises(lite.ClientError):
                hc.make_plan(self.args(*options))

    def test_command_preserves_arguments_without_evaluation(self):
        plan = {"attack": "0", "mode": 0, "nodes": 1, "dcus_per_node": 1, "module": 'hc/$(touch injected)', "modulefiles": "/a b/'x", "extra_args": ["-w", "1"]}
        argv = shlex.split(hc.remote_command(plan, "/run with spaces", {"hashes": "/a b/$(bad)", "dict": "/a b/d"}))
        self.assertIn(plan["module"], argv)
        self.assertIn("/a b/$(bad)", argv)
        self.assertIn(plan["modulefiles"], argv)

    def test_extras_cannot_override_owned_outputs(self):
        for extra in ("--potfile-disable", "--outfile /tmp/other", "--restore", "-a 3", "--runtime x"):
            with self.assertRaises(lite.ClientError):
                hc.extra_arguments(extra)
        self.assertEqual(hc.extra_arguments("-w 1 -O --runtime 30"), ["-w", "1", "-O", "--runtime", "30"])

    def test_report_detects_missing_failed_aborted_and_negative_ranks(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "hashes.txt").write_bytes(b"h1\nh1\nh2\n")
            (out / "pot.0").write_bytes(b"h1:secret\n")
            (out / "pot.merged").write_bytes(b"stale:secret\n")
            (out / "cracked.0").write_bytes(b"h1\n")
            job = {"state": "COMPLETED"}
            manifest = {"nodes": 2, "region_id": "other"}
            for codes in ((0,), (0, 2), (0, -1), (0, 3)):
                summary = {"ranks": [{"rank": i, "hashcat_rc": rc} for i, rc in enumerate(codes)]}
                self.assertFalse(hc.result_report("real-id", job, manifest, summary, out)["ok"])
            summary = {"ranks": [{"rank": i, "hashcat_rc": rc} for i, rc in enumerate((0, 1))]}
            report = hc.result_report("real-id", job, manifest, summary, out)
            self.assertTrue(report["ok"])
            self.assertEqual((report["job_id"], report["cracked"], report["total_hashes"], report["remaining"]), ("real-id", 1, 2, 1))
            self.assertNotIn(b"stale", (out / "pot.merged").read_bytes())
            job["state"] = "FINALIZING"
            self.assertFalse(hc.result_report("real-id", job, manifest, summary, out)["ok"])

    def test_saved_region_and_complete_credential_resolution(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp}, clear=True):
            path = Path(tmp) / "scnet-hpc/config.json"
            path.parent.mkdir()
            path.write_text('{"openapi":{"default_region_id":"custom"}}')
            self.assertEqual(lite.default_region(), "custom")
            os.environ["SCNET_OPENAPI_REGION_ID"] = "explicit"
            self.assertEqual(lite.default_region(), "explicit")
            os.environ["SCNET_OPENAPI_USER"] = "partial"
            with self.assertRaises(lite.ClientError):
                lite.Client()._credentials()

    def test_live_completed_requires_history(self):
        client = lite.Client()
        ctx = {"hpc_url": "https://example.invalid", "token": "test", "scheduler_id": "1"}
        live = {"jobId": "j", "jobStatus": "statC"}
        with patch.object(client, "hpc_context", return_value=ctx), patch.object(client, "request", side_effect=[live, {"items": []}]):
            self.assertEqual(client.job("j", "r")["state"], "FINALIZING")
        history = {"jobId": "j", "jobStatus": "statD", "jobExitStatus": "10005"}
        with patch.object(client, "hpc_context", return_value=ctx), patch.object(client, "request", side_effect=[live, {"items": [history]}]):
            self.assertEqual(client.job("j", "r")["state"], "FAILED")

    def test_file_listing_fetches_every_page(self):
        client = lite.Client()
        with patch.object(client, "efile_context", return_value=("https://example.invalid", "test")), patch.object(client, "request", side_effect=[{"fileList": [{"name": "a"}, {"name": "b"}], "total": 3}, {"fileList": [{"name": "c"}], "total": 3}]):
            self.assertEqual(len(client.ls("/results", "r", limit=2)["files"]), 3)

    def test_no_secret_config_fallback(self):
        with patch("scnet_lite.load_openapi_credentials", return_value=(None, None)):
            with self.assertRaisesRegex(lite.ClientError, "Never put secrets"):
                lite.Client()._credentials()

    def test_adapter_wait_returns_failure_for_failed_terminal_jobs(self):
        with redirect_stdout(io.StringIO()):
            for state, expected in (("FAILED", 1), ("CANCELLED", 1), ("COMPLETED", 0)):
                with patch.object(lite.Client, "wait", return_value={"state": state}):
                    self.assertEqual(lite.main(["--region", "r", "wait", "j"]), expected)

    def test_collection_keeps_region_and_discards_stale_rank_evidence(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            out = Path(tmp)
            (out / "summary.json").write_text('{"ranks":[{"rank":0,"hashcat_rc":0}]}')
            (out / "pot.99").write_text("old:plaintext\n")
            manifest = {"nodes": 1, "region_id": "selected", "run_dir": "/run", "remote_inputs": {"hashes": "/run/inputs/hashes/data.txt"}}
            class FakeClient:
                def __init__(self):
                    self.regions = []
                def job(self, job_id, region):
                    self.regions.append(region)
                    return {"state": "COMPLETED", "work_dir": "/run"}
                def ls(self, path, region):
                    self.regions.append(region)
                    return {"files": [{"name": "pot.0"}, {"name": "cracked.0"}]}
                def download(self, remote, local, region, cover=False):
                    self.regions.append(region)
                    content = {"/run/run.json": json.dumps(manifest), "/run/results/pot.0": "hash:plain\n", "/run/results/cracked.0": "hash\n", "/run/inputs/hashes/data.txt": "hash\n"}[remote]
                    Path(local).write_text(content)
            client = FakeClient()
            self.assertEqual(hc.collect(client, "actual-id", "selected", out, cover=True), 1)
            self.assertEqual(set(client.regions), {"selected"})
            self.assertEqual(json.loads((out / "report.json").read_text())["reported_ranks"], 0)
            self.assertNotIn(b"old", (out / "pot.merged").read_bytes())

    def test_wait_timeout_never_becomes_successful_collection(self):
        client = lite.Client()
        with patch.object(hc, "live_preflight", return_value="/home"), patch.object(client, "mkdir"), patch.object(client, "upload"), patch.object(client, "submit", return_value={"job_id": "j"}), patch.object(client, "wait", side_effect=lite.ClientError("still running")), patch.object(hc, "collect") as collector, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(lite.ClientError, "still running"):
                hc.crack(client, self.args("--wait"))
            collector.assert_not_called()

    def test_empty_control_and_pkzip_inputs_rejected(self):
        spec = importlib.util.spec_from_file_location("precheck", ROOT / "scripts/remote/hc-precheck.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            path = Path(tmp) / "input.txt"
            for content in (b"", b"hash\x0bother\n", b"hash\x1cother\n", b"$pkzip2$1*2*hex\n"):
                path.write_bytes(content)
                self.assertEqual(module.main([str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
