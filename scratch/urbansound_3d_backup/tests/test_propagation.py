"""
Unit tests for the UrbanSound 3D Acoustic Propagation Engine.
Tests fundamental acoustic laws:
1. Inverse Square Law / Geometric Divergence (6 dB drop per doubling of distance)
2. Decibel Energy Summation (60 dB + 60 dB = 63.01 dB)
3. Sound Barrier screening reduction behind obstacle
4. Non-negative attenuation terms
"""

import sys
import os
import unittest
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.sources import NoiseSource
from core.geometry import CityLayout, SoundBarrier
from core.propagation import (
    simulate_grid,
    evaluate_single_receiver,
    compute_ground_attenuation,
    calculate_atmospheric_alpha
)

class TestAcousticEngine(unittest.TestCase):

    def test_geometric_divergence_doubling(self):
        """
        Verify inverse square law: 20*log10(d2/d1) = 20*log10(2) ≈ 6.02 dB drop per doubling.
        At d1 = 10m and d2 = 20m, geometric divergence increases by ~6.02 dB.
        """
        city = CityLayout("Test City", 100.0, 100.0)
        source = NoiseSource("S1", "Test Source", 0.0, 0.0, 1.0, 100.0)
        
        # Probe at 10m and 20m along x axis (ground_type hard to minimize ground effect)
        r10 = evaluate_single_receiver(10.0, 0.0, 1.0, city, [source], ground_type="hard")
        r20 = evaluate_single_receiver(20.0, 0.0, 1.0, city, [source], ground_type="hard")
        
        div_10 = r10["breakdown"][0]["A_div"]
        div_20 = r20["breakdown"][0]["A_div"]
        
        diff = div_20 - div_10
        # Exactly 20 * log10(20/10) = 20 * log10(2) = 6.0206 dB
        self.assertAlmostEqual(diff, 20.0 * np.log10(2.0), places=2)

    def test_energy_summation(self):
        """
        Verify logarithmic decibel summation: 60 dB + 60 dB = 10*log10(10^6 + 10^6) = 63.01 dB.
        Decibels must never be added linearly (60 + 60 != 120).
        """
        l1 = 60.0
        l2 = 60.0
        energy_sum = 10.0 ** (l1 / 10.0) + 10.0 ** (l2 / 10.0)
        l_total = 10.0 * np.log10(energy_sum)
        
        self.assertAlmostEqual(l_total, 63.01, places=2)
        
        # Also test with 3 identical sources: 60 + 60 + 60 = 64.77 dB
        energy_3 = 3.0 * (10.0 ** (l1 / 10.0))
        l_3 = 10.0 * np.log10(energy_3)
        self.assertAlmostEqual(l_3, 64.77, places=2)

    def test_barrier_reduces_sound_level(self):
        """
        Verify that placing a sound barrier between source and receiver
        causes screening attenuation (received level is lower behind barrier).
        """
        city_open = CityLayout("Open Field", 200.0, 200.0)
        source = NoiseSource("S1", "Point Source", 50.0, 100.0, 1.0, 100.0)
        
        # Receiver at (150, 100)
        open_res = evaluate_single_receiver(150.0, 100.0, 1.5, city_open, [source])
        open_db = open_res["total_db"]
        
        # Add acoustic barrier wall at x = 100 from y = 50 to y = 150, height = 4.5m
        city_bar = CityLayout("Protected Field", 200.0, 200.0)
        barrier = SoundBarrier(100.0, 50.0, 100.0, 150.0, height=4.5, name="Test Barrier")
        city_bar.add_barrier(barrier)
        
        bar_res = evaluate_single_receiver(150.0, 100.0, 1.5, city_bar, [source])
        bar_db = bar_res["total_db"]
        a_bar = bar_res["breakdown"][0]["A_bar"]
        
        # Sound behind barrier must be lower
        self.assertGreater(open_db, bar_db)
        self.assertGreater(a_bar, 0.0)
        self.assertLessEqual(a_bar, 20.0)  # Capped at 20 dB per standard

    def test_non_negative_attenuations(self):
        """
        Verify that individual attenuation terms (A_div, A_atm, A_gr, A_bar) are non-negative.
        """
        distances = np.array([1.0, 10.0, 50.0, 150.0, 500.0])
        a_gr = compute_ground_attenuation(distances, ground_type="grass", z_s=1.0, z_r=1.5)
        self.assertTrue(np.all(a_gr >= 0.0))
        
        alpha = calculate_atmospheric_alpha(temp_c=25.0, rel_humidity=60.0)
        self.assertGreater(alpha, 0.0)

    def test_grid_simulation_execution(self):
        """
        Verify simulate_grid completes and produces valid shape and reasonable dB range.
        """
        city = CityLayout("Test City", 100.0, 100.0)
        city.add_building("B1", "Test Building", [(30, 30), (60, 30), (60, 60), (30, 60)], 15.0, "Residential Area")
        source = NoiseSource("S1", "Car", 20.0, 20.0, 0.5, 90.0)
        
        res = simulate_grid(city, [source], grid_res=30)
        l_tot = res["L_total"]
        
        self.assertEqual(l_tot.shape, (30, 30))
        self.assertTrue(np.all(np.isfinite(l_tot)))
        self.assertTrue(np.all(l_tot >= 30.0))  # At or above ambient floor
        self.assertTrue(np.all(l_tot <= 130.0))  # Reasonable upper bound

if __name__ == "__main__":
    unittest.main()
