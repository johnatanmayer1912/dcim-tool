"""Two-sample counter math for live utilization."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.utilization_overlay.rates import (
    clamp_delta_seconds,
    compute_bps,
    compute_pct,
    delta_octets,
    pair_interface_samples,
    prefer_octets,
)


class TestRateMath(unittest.TestCase):
    def test_valid_two_sample_delta_bps(self):
        # 1_000_000 octets in 10s => 800_000 bps
        self.assertEqual(compute_bps(1_000_000, 10.0), 800_000.0)
        t0 = {'in_octets_64': 1000, 'out_octets_64': 500, 'if_speed_bps': 1_000_000_000}
        t1 = {'in_octets_64': 1_001_000, 'out_octets_64': 501_000, 'if_speed_bps': 1_000_000_000}
        paired = pair_interface_samples(t0, t1, 10.0)
        self.assertTrue(paired['ok'])
        self.assertEqual(paired['in_bps'], 800_000.0)
        self.assertAlmostEqual(paired['in_pct'], (800_000.0 / 1_000_000_000) * 100)

    def test_64bit_counter_path_preferred(self):
        sample = {'in_octets': 10, 'in_octets_64': 99}
        value, width = prefer_octets(sample, 'in')
        self.assertEqual(value, 99)
        self.assertEqual(width, '64')

    def test_negative_reset_is_invalid(self):
        # t1 << t0 and not a plausible 32/64 wrap at this magnitude
        delta, err = delta_octets(50, 10, '64')
        # 10 + 2**32 - 50 is a wrap; 64-bit width tries 2**32 first
        self.assertIsNotNone(delta)
        t0 = {'in_octets_64': 9_000_000_000, 'out_octets_64': 9_000_000_000, 'if_speed_bps': 1_000_000_000}
        t1 = {'in_octets_64': 1, 'out_octets_64': 1, 'if_speed_bps': 1_000_000_000}
        paired = pair_interface_samples(t0, t1, 10.0)
        # Wrap-corrected delta would imply implausible >2x ifSpeed → invalid
        self.assertFalse(paired['ok'])
        self.assertEqual(paired['reason'], 'counter_invalid')
        self.assertIsNone(paired['in_bps'])

    def test_zero_ifspeed_suppresses_percent(self):
        t0 = {'in_octets_64': 0, 'out_octets_64': 0, 'if_speed_bps': 0}
        t1 = {'in_octets_64': 1000, 'out_octets_64': 1000, 'if_speed_bps': 0}
        paired = pair_interface_samples(t0, t1, 10.0)
        self.assertTrue(paired['ok'])
        self.assertGreater(paired['in_bps'], 0)
        self.assertIsNone(paired['in_pct'])
        self.assertIsNone(paired['pct'])

    def test_missing_ifspeed_suppresses_percent(self):
        t0 = {'in_octets_64': 0, 'out_octets_64': 0}
        t1 = {'in_octets_64': 125000, 'out_octets_64': 0}
        paired = pair_interface_samples(t0, t1, 10.0)
        self.assertTrue(paired['ok'])
        self.assertEqual(paired['in_bps'], 100000.0)
        self.assertIsNone(paired['pct'])

    def test_clamp_delta_seconds(self):
        self.assertEqual(clamp_delta_seconds(1), 5.0)
        self.assertEqual(clamp_delta_seconds(10), 10.0)
        self.assertEqual(clamp_delta_seconds(99), 60.0)

    def test_missing_counters_invalid(self):
        paired = pair_interface_samples({}, {}, 10.0)
        self.assertFalse(paired['ok'])
        self.assertEqual(paired['reason'], 'counter_invalid')


if __name__ == '__main__':
    unittest.main()
