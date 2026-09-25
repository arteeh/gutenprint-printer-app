import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "audit", Path(__file__).resolve().parents[1] / "scripts/audit-oci-licenses.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LicenseAuditTests(unittest.TestCase):
    def setUp(self):
        self.sbom = {
            "spdxVersion": "SPDX-2.3",
            "packages": [{"name": "gutenprint", "SPDXID": "SPDXRef-gutenprint",
                          "licenseDeclared": "GPL-2.0-or-later"}],
            "hasExtractedLicensingInfos": [{"licenseId": "LicenseRef-custom",
                                           "extractedText": "Keep this notice"}],
            "externalDocumentRefs": [{"externalDocumentId": "DocumentRef-runtime"}],
        }
        self.index = {"annotations": {audit.LICENSE_KEY: "Apache-2.0"}}
        self.config = {"config": {"Labels": {audit.LICENSE_KEY: "Apache-2.0"}}}

    def report(self, configs=None):
        return audit.audit(self.sbom, self.index,
                           configs or {"amd64": self.config, "arm64": self.config},
                           "Apache-2.0")

    def test_inventory_preserves_unknowns_notices_and_input(self):
        before = copy.deepcopy(self.sbom)
        report = self.report()
        self.assertEqual(report["errors"], [])
        self.assertTrue(report["packages"][0]["reviewRequired"])
        self.assertEqual(report["packages"][0]["licenseConcluded"], "NOASSERTION")
        self.assertEqual(report["hasExtractedLicensingInfos"],
                         self.sbom["hasExtractedLicensingInfos"])
        self.assertEqual(report["externalDocumentRefs"], self.sbom["externalDocumentRefs"])
        self.assertEqual(self.sbom, before)

    def test_each_platform_must_agree(self):
        bad = {"config": {"Labels": {audit.LICENSE_KEY: "MIT"}}}
        report = self.report({"amd64": self.config, "arm64": bad})
        self.assertEqual(len(report["errors"]), 1)
        self.assertIn("arm64", report["errors"][0])

    def test_missing_index_label_fails(self):
        self.index = {}
        self.assertIn("index", self.report()["errors"][0])

    def test_missing_config_label_fails(self):
        self.assertEqual(len(self.report({"amd64": {}})["errors"]), 1)

    def test_differing_expressions_remain_visible(self):
        self.sbom["packages"][0]["licenseConcluded"] = "GPL-2.0-only"
        self.assertTrue(self.report()["packages"][0]["reviewRequired"])

    def test_empty_or_unsupported_sbom_rejected(self):
        for document in ({"spdxVersion": "SPDX-2.3", "packages": []},
                         {"spdxVersion": "SPDX-3.0", "packages": [{}]}):
            with self.assertRaises(ValueError):
                audit.audit(document, self.index, {}, "Apache-2.0")


if __name__ == "__main__":
    unittest.main()
