import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

_original_cwd = os.getcwd()
with tempfile.TemporaryDirectory() as _import_dir:
    os.chdir(_import_dir)
    try:
        from remote_stream import (
            SpiderCamRemoteThread,
            get_remote_config,
        )
        import reconstruction_3d
        from spiderweb import (
            EvidenceManifest,
            ForensicAuditLog,
            summarize_integrity_results,
        )
    finally:
        os.chdir(_original_cwd)
        sys.modules.pop("spiderweb", None)


class EvidenceManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.evidence = self.root / "sample.bin"
        self.evidence.write_bytes(b"synthetic test evidence")
        self.manifest = EvidenceManifest("TEST-CASE", "TEST-OPERATOR")
        self.manifest.manifest_path = self.root / "manifest.json"

    def test_hash_matches_sha256_digest(self):
        expected = hashlib.sha256(self.evidence.read_bytes()).hexdigest()
        self.assertEqual(self.manifest.hash_file(self.evidence), expected)

    def test_hash_failure_raises_instead_of_returning_digest_like_value(self):
        with self.assertRaises(OSError):
            self.manifest.hash_file(self.root / "missing.bin")

    def test_verifies_unchanged_file(self):
        self.manifest.register(self.evidence)
        self.assertEqual(
            self.manifest.verify_all(),
            [("sample.bin", "VERIFIED")],
        )

    def test_saved_manifest_loads_and_verifies(self):
        self.manifest.register(self.evidence)
        loaded = EvidenceManifest("TEST-CASE", "TEST-OPERATOR")
        loaded.manifest_path = self.manifest.manifest_path
        loaded._load_existing()
        self.assertIsNone(loaded.manifest_error)
        self.assertEqual(loaded.verify_all(), [("sample.bin", "VERIFIED")])

    def test_reports_modified_and_missing_files_distinctly(self):
        self.manifest.register(self.evidence)
        missing = self.root / "missing.bin"
        self.manifest.entries.append({
            "filename": missing.name,
            "filepath": str(missing),
            "sha256": "0" * 64,
        })
        self.evidence.write_bytes(b"modified synthetic data")
        self.assertEqual(
            self.manifest.verify_all(),
            [("sample.bin", "MODIFIED"), ("missing.bin", "MISSING")],
        )

    def test_reports_unreadable_file(self):
        self.manifest.register(self.evidence)
        with mock.patch.object(self.manifest, "hash_file", side_effect=PermissionError):
            self.assertEqual(
                self.manifest.verify_all(),
                [("sample.bin", "UNREADABLE")],
            )

    def test_invalid_manifest_is_not_verified_or_overwritten(self):
        self.manifest.manifest_path.write_text("{invalid", encoding="utf-8")
        self.manifest._load_existing()
        self.assertEqual(
            self.manifest.verify_all(),
            [("manifest.json", "INVALID_MANIFEST")],
        )
        with self.assertRaises(ValueError):
            self.manifest.register(self.evidence)
        self.assertEqual(
            self.manifest.manifest_path.read_text(encoding="utf-8"),
            "{invalid",
        )

    def test_manifest_with_invalid_hash_entry_is_rejected(self):
        self.manifest.manifest_path.write_text(
            json.dumps({
                "entries": [{
                    "filename": "sample.bin",
                    "filepath": str(self.evidence),
                    "sha256": "ERROR",
                }]
            }),
            encoding="utf-8",
        )
        self.manifest._load_existing()
        self.assertEqual(
            self.manifest.verify_all(),
            [("manifest.json", "INVALID_MANIFEST")],
        )

    def test_audit_log_write_failure_raises(self):
        blocked_path = self.root / "not-a-file"
        blocked_path.mkdir()
        audit = ForensicAuditLog()
        audit.log_path = blocked_path
        with self.assertRaises(OSError):
            audit.log("TEST")

    def test_report_hash_status_is_not_verified_after_any_failed_check(self):
        self.assertIn(
            "NOT VERIFIED",
            summarize_integrity_results([]),
        )
        self.assertIn(
            "CHECK FAILED",
            summarize_integrity_results([("sample.bin", "UNREADABLE")]),
        )
        self.assertIn(
            "MATCH THE MANIFEST",
            summarize_integrity_results([("sample.bin", "VERIFIED")]),
        )


class ConfigurationTests(unittest.TestCase):
    def test_remote_configuration_requires_url_and_key(self):
        with self.assertRaisesRegex(RuntimeError, "SPIDERCAM_API_BASE_URL"):
            get_remote_config({})
        with self.assertRaisesRegex(RuntimeError, "SPIDERCAM_SHARED_KEY"):
            get_remote_config({"SPIDERCAM_API_BASE_URL": "https://service.invalid"})

    def test_remote_configuration_reads_environment_without_default_credentials(self):
        config = {
            "SPIDERCAM_API_BASE_URL": "https://service.invalid/",
            "SPIDERCAM_SHARED_KEY": "synthetic-test-key",
        }
        self.assertEqual(
            get_remote_config(config),
            ("https://service.invalid", "synthetic-test-key"),
        )

    def test_token_error_does_not_include_response_body(self):
        thread = SpiderCamRemoteThread("test-device", "test-room", "https://service.invalid")
        with (
            mock.patch.dict(os.environ, {"SPIDERCAM_SHARED_KEY": "synthetic-test-key"}),
            mock.patch("remote_stream.requests.post") as post,
        ):
            post.return_value.status_code = 401
            post.return_value.text = "synthetic-response-secret"
            with self.assertRaises(RuntimeError) as error:
                thread._fetch_token()
        self.assertNotIn("synthetic-response-secret", str(error.exception))

    def test_data_directory_can_be_configured_portably(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            configured = reconstruction_3d.get_data_dir(
                {"CRIMESCAN_DATA_DIR": temp_dir}
            )
            self.assertEqual(configured, Path(temp_dir).resolve())

    def test_colmap_executable_uses_configured_existing_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "colmap-test-executable"
            executable.write_text("", encoding="utf-8")
            resolved = reconstruction_3d.resolve_colmap_executable(
                {"COLMAP_EXECUTABLE": str(executable)}
            )
            self.assertEqual(resolved, str(executable.resolve()))

    def test_colmap_configuration_fails_clearly_for_missing_executable(self):
        with self.assertRaisesRegex(FileNotFoundError, "COLMAP_EXECUTABLE"):
            reconstruction_3d.resolve_colmap_executable(
                {"COLMAP_EXECUTABLE": str(Path(tempfile.gettempdir()) / "missing-colmap")},
                path_lookup=lambda _name: None,
            )


class ReconstructionLabelTests(unittest.TestCase):
    def test_demo_point_cloud_is_marked_synthetic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "viewer_data" / "pointcloud.json"
            reconstruction_3d._create_demo_pointcloud_json(output)
            data = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(data["synthetic"])
        self.assertEqual(data["reconstruction_status"], "SYNTHETIC_DEMONSTRATION")
        self.assertIn("SYNTHETIC", data["source"])

    def test_missing_open3d_output_creates_labeled_demo_not_success_shaped_cloud(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "viewer_data" / "pointcloud.json"
            logs = []
            with (
                mock.patch.object(reconstruction_3d, "o3d", None),
                mock.patch.object(reconstruction_3d, "RECON_DIR", root / "reconstruction_3d"),
                mock.patch.object(reconstruction_3d, "VIEWER_DATA_DIR", output.parent),
                mock.patch.object(reconstruction_3d, "POINTCLOUD_JSON", output),
            ):
                reconstruction_3d._set_reconstruction_status("RUNNING")
                reconstruction_3d.convert_ply_to_threejs(
                    root / "missing.ply",
                    log_fn=logs.append,
                )
                data = json.loads(output.read_text(encoding="utf-8"))
                status = reconstruction_3d.LAST_RECONSTRUCTION_STATUS.copy()
        self.assertTrue(data["synthetic"])
        self.assertTrue(status["synthetic"])
        self.assertEqual(status["status"], "SYNTHETIC_DEMONSTRATION")
        self.assertTrue(any("synthetic demonstration data" in line.lower() for line in logs))

    def test_viewer_serves_configured_synthetic_data_and_visible_label(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            pointcloud = {
                "points": [[0, 0, 0]],
                "colors": [[0, 0.8, 1]],
                "synthetic": True,
                "source": "SYNTHETIC TEST DATA",
                "reconstruction_status": "SYNTHETIC_DEMONSTRATION",
            }
            (data_dir / "pointcloud.json").write_text(
                json.dumps(pointcloud),
                encoding="utf-8",
            )
            with mock.patch.object(reconstruction_3d, "VIEWER_DATA_DIR", data_dir):
                client = reconstruction_3d.flask_app.test_client()
                response = client.get("/pointcloud.json")
                viewer = client.get("/")
                try:
                    pointcloud_status = response.status_code
                    pointcloud_data = json.loads(response.get_data())
                    viewer_status = viewer.status_code
                    viewer_data = viewer.get_data()
                finally:
                    response.close()
                    viewer.close()
        self.assertEqual(pointcloud_status, 200)
        self.assertTrue(pointcloud_data["synthetic"])
        self.assertEqual(viewer_status, 200)
        self.assertIn(b"SYNTHETIC DEMONSTRATION DATA", viewer_data)

if __name__ == "__main__":
    unittest.main()
