#!/usr/bin/env python3

import unittest
from datetime import date
from tefilla_rules import HebrewCalendar, TefillaRuleEngine, ChunkAnnotation


class TestIntegration(unittest.TestCase):
    """Integration tests combining HebrewCalendar and TefillaRuleEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calendar = HebrewCalendar()
        # Create minimal test chunks for integration tests
        test_chunks = [
            ChunkAnnotation(
                name="test_chunk",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"day_of_week": "weekday"}
            )
        ]
        self.rule_engine = TefillaRuleEngine(test_chunks)
    
    def test_end_to_end_weekday(self):
        """Test end-to-end for a regular weekday."""
        test_date = date(2024, 1, 15)  # Monday
        tefilla_type = "shacharis"
        
        # Get date conditions
        conditions = self.calendar.get_date_conditions(test_date, tefilla_type)
        
        # Verify expected conditions
        self.assertEqual(conditions.day_of_week, "weekday")
        self.assertIsNone(conditions.holiday)
        self.assertFalse(conditions.rosh_chodesh)
        self.assertFalse(conditions.chol_hamoed)
        self.assertFalse(conditions.fast_day)
        self.assertFalse(conditions.aseret_yemei_teshuvah)
        self.assertEqual(conditions.sefirat_haomer, 0)
        self.assertTrue(conditions.full_shmoneh_esreh)
        self.assertEqual(conditions.hallel_type, "none")
    
    def test_end_to_end_pesach(self):
        """Test end-to-end for Pesach."""
        test_date = date(2024, 4, 24)  # Third day of Pesach (Nissan 16 - Chol Hamoed)
        tefilla_type = "shacharis"
        
        # Get date conditions
        conditions = self.calendar.get_date_conditions(test_date, tefilla_type)
        
        # Verify expected conditions
        self.assertEqual(conditions.holiday, "pesach")
        self.assertTrue(conditions.chol_hamoed)
        self.assertFalse(conditions.aseret_yemei_teshuvah)
        self.assertFalse(conditions.full_shmoneh_esreh)
        self.assertEqual(conditions.hallel_type, "full")
    
    def test_end_to_end_rosh_hashana(self):
        """Test end-to-end for Rosh Hashana."""
        test_date = date(2024, 10, 3)  # First day of Rosh Hashana (corrected date)
        tefilla_type = "shacharis"
        
        # Get date conditions
        conditions = self.calendar.get_date_conditions(test_date, tefilla_type)
        
        # Verify expected conditions
        self.assertEqual(conditions.holiday, "rosh_hashana")
        self.assertFalse(conditions.chol_hamoed)
        self.assertTrue(conditions.aseret_yemei_teshuvah)
        self.assertFalse(conditions.full_shmoneh_esreh)
        self.assertEqual(conditions.hallel_type, "full")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
