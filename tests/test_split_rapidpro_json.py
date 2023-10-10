from unittest import TestCase

from parenttext_pipeline.steps import edit_campaign


class TestSplitRapidProJson(TestCase):
    def test_must_not_edit_campaign_with_no_events(self):
        flows = []
        campaign = {
            "events": [],
        }
        self.assertEqual(campaign, edit_campaign(campaign, flows))

    def test_must_remove_campaign_with_no_events_after_editing(self):
        flows = [
            {"name": "flow_a"},
        ]
        campaign = {
            "name": "campaign_a",
            "events": [
                {"event_type": "X", "flow": {"name": "flow_b"}},
            ],
        }
        self.assertIsNone(edit_campaign(campaign, flows))

    def test_must_remove_events_that_reference_missing_flows(self):
        flows = [
            {"name": "flow_a"},
        ]
        campaign = {
            "name": "campaign_a",
            "events": [
                {"event_type": "F", "flow": {"name": "flow_a"}},
                {"event_type": "F", "flow": {"name": "flow_b"}},
            ],
        }
        events = edit_campaign(campaign, flows)["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["flow"]["name"], "flow_a")

    def test_must_remove_events_where_type_does_not_match(self):
        flows = [
            {"name": "flow_a"},
            {"name": "flow_b"},
            {"name": "flow_c"},
        ]
        campaign = {
            "name": "campaign_a",
            "events": [
                {"event_type": "X", "flow": {"name": "flow_a"}},
                {"event_type": "F", "flow": {"name": "flow_b"}},
                {"event_type": "M", "flow": {"name": "flow_c"}},
            ],
        }
        events = edit_campaign(campaign, flows)["events"]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["flow"]["name"], "flow_b")
        self.assertEqual(events[1]["flow"]["name"], "flow_c")
