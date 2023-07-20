import json
from pathlib import Path
from tempfile import TemporaryDirectory
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

        with TemporaryDirectory() as output:
            process_keywords(sources, output)
            outfile = Path(output) / "safeguarding_words.json"
            with open(outfile, "r") as fp_actual:
                with open(resource_path("safeguarding_words.json"), "r") as fp_expected:
                    self.assertDictEqual(
                        json.load(fp_actual),
                        json.load(fp_expected),
                    )


def resource_path(name):
    return Path(__file__).parent / "resources" / name
