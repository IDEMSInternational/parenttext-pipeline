import json
from pathlib import Path
from unittest import TestCase

from parenttext_pipeline.extract_keywords import process_keywords


class TestProcessKeywords(TestCase):

    def test_everything(self):
        sources = [
            {
                "path": resource_path("zul_mod.xlsx"),
                "key": "zul",
            },
        ]

        content = process_keywords(sources)

        with open(resource_path("zul_mod_expected.json"), "r") as fp_expected:
            self.assertDictEqual(
                content,
                json.load(fp_expected),
            )


def resource_path(name):
    return Path(__file__).parent / "resources" / name
