from unittest import TestCase

from parenttext_pipeline.steps import set_expiration


class TestUpdateExpirationTime(TestCase):

    def test_must_set_expiration_to_default(self):
        default = 1440
        flow = {
            "name": "flow_1",
            "expire_after_minutes": 0,
        }
        updated = set_expiration(flow, default)
        self.assertEqual(updated["expire_after_minutes"], 1440)
        self.assertFalse("metadata" in updated)

    def test_must_set_metadata_expires_if_exists(self):
        default = 360
        flow = {"name": "flow_1", "expire_after_minutes": 0, "metadata": {"expires": 0}}
        updated = set_expiration(flow, default)
        self.assertEqual(updated["metadata"]["expires"], 360)
        self.assertEqual(updated["expire_after_minutes"], 360)

    def test_must_not_create_metadata_expires(self):
        default = 480
        flow = {"name": "flow_1", "expire_after_minutes": 0, "metadata": {}}
        updated = set_expiration(flow, default)
        self.assertFalse("expires" in updated["metadata"])
        self.assertEqual(updated["expire_after_minutes"], 480)

    def test_must_allow_per_flow_expiration_times(self):
        default = 120
        specifics = {
            "flow_1": 240,
        }
        flow = {
            "name": "flow_1",
            "expire_after_minutes": 0,
            "metadata": {"expires": 0},
        }
        updated = set_expiration(flow, default, specifics)
        self.assertEqual(updated["expire_after_minutes"], 240)
        self.assertEqual(updated["metadata"]["expires"], 240)
