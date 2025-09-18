"""
Unit tests for the Hebrew Audio Siddur rule engine.
Tests HebrewCalendar and TefillaRuleEngine functionality with boundary conditions and edge cases.
"""

import unittest
from datetime import date, datetime, timedelta
import sys; sys.path.append("../src"); from tefilla_rules import HebrewCalendar, TefillaRuleEngine, DateConditions, ChunkAnnotation


class TestHebrewCalendar(unittest.TestCase):
    """Test Hebrew calendar date condition calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calendar = HebrewCalendar()
    
    def assert_day_of_week(self, test_date, tefilla_type, expected_day):
        """Helper method to test day_of_week for a specific date and tefilla type."""
        conditions = self.calendar.get_date_conditions(test_date, tefilla_type)
        self.assertEqual(conditions.day_of_week, expected_day)
    
    def assert_condition(self, condition_checker, start_date, end_date, end_date_false_tefillos=None):
        """
        Test a condition across a range of dates with all tefilla types using a boolean function.
        
        Args:
            condition_checker: Function that takes (conditions) and returns boolean
            start_date: First date in the range (inclusive)
            end_date: Last date in the range (inclusive)
            end_date_false_tefillos: List of tefilla types that should be False on end_date (default: ['maariv'])
        """
        # Generate all dates in the range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Test from 1 day before start_date to 1 day after end_date
        all_dates = [start_date - timedelta(days=1)] + date_range + [end_date + timedelta(days=1)]
        tefilla_types = ['shacharis', 'mincha', 'maariv']
        
        # Default to maariv being False on end_date
        if end_date_false_tefillos is None:
            end_date_false_tefillos = ['maariv']
        
        for test_date in all_dates:
            for tefilla_type in tefilla_types:
                conditions = self.calendar.get_date_conditions(test_date, tefilla_type)
                expected_result = condition_checker(conditions)
                
                # Determine if this should be True or False based on date and tefilla_type
                should_be_true = test_date in date_range
                
                # Exception: Last date + specified tefillos should be False
                if tefilla_type in end_date_false_tefillos and test_date == end_date:
                    should_be_true = False
                
                # Exception: Date before range + maariv should be True (maariv uses next Hebrew date)
                if tefilla_type == 'maariv' and test_date == start_date - timedelta(days=1):
                    should_be_true = True
                
                # Skip validation for maariv on end_date + 1
                if tefilla_type == 'maariv' and test_date == end_date + timedelta(days=1):
                    continue
                
                self.assertEqual(expected_result, should_be_true, 
                               f"Failed for {test_date} {tefilla_type}: expected {should_be_true}, got {expected_result}")
    
    def assert_chol_hamoed(self, start_date, end_date):
        """
        Test chol_hamoed condition across a date range.
        Args:
            start_date: First date of chol hamoed (inclusive)
            end_date: Last date of chol hamoed (inclusive)
        """
        self.assert_condition(lambda conditions: conditions.chol_hamoed, start_date, end_date)
        self.assert_condition(lambda conditions: not conditions.yom_tov, start_date, end_date)

    def assert_rosh_chodesh(self, start_date, end_date):
        """
        Test rosh_chodesh condition across a date range.
        Args:
            start_date: First date of rosh chodesh (inclusive)
            end_date: Last date of rosh chodesh (inclusive)
        """
        self.assert_condition(lambda conditions: conditions.rosh_chodesh, 
                             start_date, end_date)
        
        # Test hallel_type is "partial" for Rosh Chodesh dates, except Teves (full Hallel)
        from pyluach import dates
        hebrew_date = dates.HebrewDate.from_pydate(end_date)
        if hebrew_date.month_name() != 'Teves':
            self.assert_condition(lambda conditions: conditions.hallel_type == "partial", 
                                 start_date, end_date)
    
    def assert_short_shmoneh_esreh(self, start_date, end_date):
        """
        Test that full_shmoneh_esreh is False across a date range.
        Automatically includes Shabbat dates that are adjacent to the range.
        Args:
            start_date: First date to test (inclusive)
            end_date: Last date to test (inclusive)
        """
        from datetime import timedelta
        
        # Check if dates before/after the range are Shabbat and include them
        extended_start = start_date
        extended_end = end_date
        
        # Check date before start_date
        date_before = start_date - timedelta(days=1)
        conditions_before = self.calendar.get_date_conditions(date_before, 'shacharis')
        if conditions_before.day_of_week == 'shabbat':
            extended_start = date_before
        
        # Check date after end_date
        date_after = end_date + timedelta(days=1)
        conditions_after = self.calendar.get_date_conditions(date_after, 'shacharis')
        if conditions_after.day_of_week == 'shabbat':
            extended_end = date_after
        
        # Test the extended range
        self.assert_condition(lambda conditions: not conditions.full_shmoneh_esreh, 
                             extended_start, extended_end)
    
    def assert_holiday(self, holiday_name, start_date, end_date):
        """
        Test holiday condition across a date range.
        Args:
            holiday_name: Name of the holiday (e.g., 'rosh_hashana', 'pesach')
            start_date: First date of holiday (inclusive)
            end_date: Last date of holiday (inclusive)
        """
        self.assert_condition(lambda conditions: conditions.holiday == holiday_name, 
                             start_date, end_date)
        
        # Test full_shmoneh_esreh is False for proper holidays
        if holiday_name in ['rosh_hashana', 'yom_kippur', 'shavuot', 'shmini_atzeret']:
            # Full Shmone Esre is False for entire holiday period
            self.assert_short_shmoneh_esreh(start_date, end_date)
        
        elif holiday_name == 'sukkot':
            # Full Shmone Esre is False for first two days of Sukkot only
            from datetime import timedelta
            first_two_end = start_date + timedelta(days=1)
            self.assert_short_shmoneh_esreh(start_date, first_two_end)
        
        elif holiday_name == 'pesach':
            # Full Shmone Esre is False for first two days and last two days of Pesach
            from datetime import timedelta
            first_two_end = start_date + timedelta(days=1)
            last_two_start = end_date - timedelta(days=1)
            
            # First two days
            self.assert_short_shmoneh_esreh(start_date, first_two_end)
            
            # Last two days
            self.assert_short_shmoneh_esreh(last_two_start, end_date)
        
        # Test hallel_type based on holiday rules
        if holiday_name in ['shavuot', 'chanukkah']:
            # Full Hallel for entire holiday period
            self.assert_condition(lambda conditions: conditions.hallel_type == "full", 
                                 start_date, end_date)
        
        elif holiday_name == 'sukkot':
            # Full Hallel for Sukkot + 2 additional days for Shmini Atzeret
            from datetime import timedelta
            extended_end = end_date + timedelta(days=2)
            self.assert_condition(lambda conditions: conditions.hallel_type == "full", 
                                 start_date, extended_end)
        
        elif holiday_name == 'pesach':
            # First 2 days: Full Hallel
            from datetime import timedelta
            first_two_end = start_date + timedelta(days=1)
            self.assert_condition(lambda conditions: conditions.hallel_type == "full", 
                                 start_date, first_two_end)
            
            # Remaining days: Partial Hallel
            if end_date > first_two_end:
                remaining_start = first_two_end + timedelta(days=1)
                self.assert_condition(lambda conditions: conditions.hallel_type == "partial", 
                                     remaining_start, end_date)
    
    def test_weekday_vs_shabbat(self):
        """Test weekday vs Shabbat detection across Friday-Sunday with all tefilla types."""
        # Test weekday condition: Jan 14-19, 2024 (Monday to Friday)
        self.assert_condition(lambda conditions: conditions.day_of_week == 'weekday', 
                                     date(2024, 1, 14), date(2024, 1, 19))
        
        # Test shabbat condition: Jan 20, 2024 (Saturday)
        self.assert_condition(lambda conditions: conditions.day_of_week == 'shabbat', 
                                     date(2024, 1, 20), date(2024, 1, 20))
        self.assert_condition(lambda conditions: not conditions.full_shmoneh_esreh, 
                                     date(2024, 1, 20), date(2024, 1, 20))
    
    def test_major_holidays_2025(self):
        """Test major holiday detection for 2025 (regular year)."""
        self.assert_holiday('rosh_hashana', date(2025, 9, 23), date(2025, 9, 24))  # Rosh Hashana 2025: Sep 23-24, 2025 (Tishrei 1-2) - Two days
        self.assert_holiday('yom_kippur', date(2025, 10, 2), date(2025, 10, 2))  # Yom Kippur 2025: Oct 2, 2025 (Tishrei 9) - Single day
        self.assert_condition(lambda conditions: conditions.aseret_yemei_teshuvah, date(2025, 9, 23), date(2025, 10, 2))  # Aseret Yemei Teshuvah 2025: Sep 23-Oct 2, 2025 (Rosh Hashana to Yom Kippur)
        self.assert_holiday('sukkot', date(2025, 10, 7), date(2025, 10, 13))  # Sukkot 2025: Oct 7-13, 2025 (Tishrei 15-21) - Multiple days
        self.assert_chol_hamoed(date(2025, 10, 9), date(2025, 10, 13))  # Chol Hamoed Sukkot 2025: Oct 9-13, 2025 (Tishrei 17-21) - Middle days
        self.assert_holiday('shmini_atzeret', date(2025, 10, 14), date(2025, 10, 15))  # Shmini Atzeret 2025: Oct 14-15, 2025 (Tishrei 22-23) - Multiple days
        self.assert_holiday('chanukkah', date(2025, 12, 15), date(2025, 12, 22))  # Chanukkah 2025: Dec 15-22, 2025 (Kislev 25 - Teves 2) - Multiple days
        self.assert_holiday('purim', date(2026, 3, 3), date(2026, 3, 3))  # Purim 2026: Mar 3, 2026 (Adar 14) - One day
        self.assert_holiday('pesach', date(2026, 4, 2), date(2026, 4, 9))  # Pesach 2026: Apr 2-9, 2026 (Nissan 15-22) - Multiple days
        self.assert_chol_hamoed(date(2026, 4, 4), date(2026, 4, 7))  # Chol Hamoed Pesach 2026: Apr 4-7, 2026 (Nissan 17-20) - Middle days
        self.assert_holiday('shavuot', date(2026, 5, 22), date(2026, 5, 23))  # Shavuot 2026: May 22-23, 2026 (Sivan 6-7) - Two days
    
    def test_major_holidays_2026(self):
        """Test major holiday detection for 2026 (regular year)."""
        self.assert_holiday('rosh_hashana', date(2026, 9, 12), date(2026, 9, 13))  # Rosh Hashana 2026: Sep 12-13, 2026 (Tishrei 1-2) - Two days
        self.assert_holiday('yom_kippur', date(2026, 9, 21), date(2026, 9, 21))  # Yom Kippur 2026: Sep 21, 2026 (Tishrei 10) - One day
        self.assert_condition(lambda conditions: conditions.aseret_yemei_teshuvah, date(2026, 9, 12), date(2026, 9, 21))  # Aseret Yemei Teshuvah 2026: Sep 12-21, 2026 (Rosh Hashana to Yom Kippur)
        self.assert_holiday('sukkot', date(2026, 9, 26), date(2026, 10, 2))  # Sukkot 2026: Sep 26-Oct 2, 2026 (Tishrei 15-21) - Multiple days
        self.assert_chol_hamoed(date(2026, 9, 28), date(2026, 10, 2))  # Chol Hamoed Sukkot 2026: Sep 28-Oct 2, 2026 - Middle days
        self.assert_holiday('shmini_atzeret', date(2026, 10, 3), date(2026, 10, 4))  # Shmini Atzeret 2026: Oct 3-4, 2026 (Tishrei 22-23) - Two days
        self.assert_holiday('chanukkah', date(2026, 12, 5), date(2026, 12, 12))  # Chanukkah 2026: Dec 5-12, 2026 (Kislev 25 - Teves 2) - Multiple days
        self.assert_holiday('purim', date(2027, 3, 23), date(2027, 3, 23))  # Purim 2027: Mar 23, 2027 (Adar 14) - One day
        self.assert_holiday('pesach', date(2027, 4, 22), date(2027, 4, 29))  # Pesach 2027: Apr 22-29, 2027 (Nissan 15-22) - Multiple days
        self.assert_chol_hamoed(date(2027, 4, 24), date(2027, 4, 27))  # Chol Hamoed Pesach 2027: Apr 24-27, 2027 - Middle days
        self.assert_holiday('shavuot', date(2027, 6, 11), date(2027, 6, 12))  # Shavuot 2027: June 11-12, 2026 (Sivan 6-7) - Two days
    
    def test_major_holidays_2027(self):
        """Test major holiday detection for 2027 - Leap Year."""
        self.assert_holiday('rosh_hashana', date(2027, 10, 2), date(2027, 10, 3))  # Rosh Hashana 2027: Oct 2-3, 2027 (Tishrei 1-2) - Two days
        self.assert_holiday('yom_kippur', date(2027, 10, 11), date(2027, 10, 11))  # Yom Kippur 2027: Oct 11, 2027 (Tishrei 10) - One days
        self.assert_condition(lambda conditions: conditions.aseret_yemei_teshuvah, date(2027, 10, 2), date(2027, 10, 11))  # Aseret Yemei Teshuvah 2027: Oct 2-11, 2027 (Rosh Hashana to Yom Kippur)
        self.assert_holiday('sukkot', date(2027, 10, 16), date(2027, 10, 22))  # Sukkot 2027: Oct 16-22, 2027 (Tishrei 15-21) - Multiple days
        self.assert_chol_hamoed(date(2027, 10, 18), date(2027, 10, 22))  # Chol Hamoed Sukkot 2027: Oct 18-22, 2027 - Middle days
        self.assert_holiday('shmini_atzeret', date(2027, 10, 23), date(2027, 10, 24))  # Shmini Atzeret 2027: Oct 23-24, 2027 (Tishrei 22-23) - Two days
        self.assert_holiday('chanukkah', date(2027, 12, 25), date(2028, 1, 1))  # Chanukkah 2027: Dec 25-Jan 1, 2027 (Kislev 25 - Teves 2) - Multiple days
        self.assert_holiday('purim', date(2028, 3, 12), date(2028, 3, 12))  # Purim 2028: Mar 12, 2028 (Adar 14) - One day
        self.assert_holiday('pesach', date(2028, 4, 11), date(2028, 4, 18))  # Pesach 2028: Apr 11-18, 2028 (Nissan 15-22) - Multiple days
        self.assert_chol_hamoed(date(2028, 4, 13), date(2028, 4, 16))  # Chol Hamoed Pesach 2028: Apr 13-16, 2028 - Middle days
        self.assert_holiday('shavuot', date(2028, 5, 31), date(2028, 6, 1))  # Shavuot 2028: May 31 - Jun 1, 2028 (Sivan 6-7) - Two days
    
    def test_rosh_chodesh_detection(self):
        """Test Rosh Chodesh detection using actual dates from Jewish years 5786-5788."""
        
        # Rosh Chodesh periods for Jewish Year 5786 (2025-2026)
        self.assert_rosh_chodesh(date(2025, 10, 22), date(2025, 10, 23))  # Cheshvan: Oct 22-23, 2025 (2 days)
        self.assert_rosh_chodesh(date(2025, 11, 21), date(2025, 11, 21))  # Kislev: Nov 21, 2025 (1 day)
        self.assert_rosh_chodesh(date(2025, 12, 20), date(2025, 12, 21))  # Teves: Dec 20-21, 2025 (2 days)
        self.assert_rosh_chodesh(date(2026, 1, 19), date(2026, 1, 19))    # Sh'vat: Jan 19, 2026 (1 day)
        self.assert_rosh_chodesh(date(2026, 2, 17), date(2026, 2, 18))    # Adar: Feb 17-18, 2026 (2 days)
        self.assert_rosh_chodesh(date(2026, 3, 19), date(2026, 3, 19))    # Nissan: Mar 19, 2026 (1 day)
        self.assert_rosh_chodesh(date(2026, 4, 17), date(2026, 4, 18))    # Iyyar: Apr 17-18, 2026 (2 days)
        self.assert_rosh_chodesh(date(2026, 5, 17), date(2026, 5, 17))    # Sivan: May 17, 2026 (1 day)
        self.assert_rosh_chodesh(date(2026, 6, 15), date(2026, 6, 16))    # Tamuz: Jun 15-16, 2026 (2 days)
        self.assert_rosh_chodesh(date(2026, 7, 15), date(2026, 7, 15))    # Av: Jul 15, 2026 (1 day)
        self.assert_rosh_chodesh(date(2026, 8, 13), date(2026, 8, 14))    # Elul: Aug 13-14, 2026 (2 days)
        
        # Rosh Chodesh periods for Jewish Year 5787 (2026-2027) - Leap Year
        self.assert_rosh_chodesh(date(2026, 10, 11), date(2026, 10, 12))  # Cheshvan: Oct 11-12, 2026 (2 days)
        self.assert_rosh_chodesh(date(2026, 11, 10), date(2026, 11, 11))  # Kislev: Nov 10-11, 2026 (2 days)
        self.assert_rosh_chodesh(date(2026, 12, 10), date(2026, 12, 11))  # Teves: Dec 10-11, 2026 (2 days)
        self.assert_rosh_chodesh(date(2027, 1, 9), date(2027, 1, 9))      # Sh'vat: Jan 9, 2027 (1 day)
        self.assert_rosh_chodesh(date(2027, 2, 7), date(2027, 2, 8))      # Adar I: Feb 7-8, 2027 (2 days)
        self.assert_rosh_chodesh(date(2027, 3, 9), date(2027, 3, 10))     # Adar II: Mar 9-10, 2027 (2 days)
        self.assert_rosh_chodesh(date(2027, 4, 8), date(2027, 4, 8))      # Nissan: Apr 8, 2027 (1 day)
        self.assert_rosh_chodesh(date(2027, 5, 7), date(2027, 5, 8))      # Iyyar: May 7-8, 2027 (2 days)
        self.assert_rosh_chodesh(date(2027, 6, 6), date(2027, 6, 6))      # Sivan: Jun 6, 2027 (1 day)
        self.assert_rosh_chodesh(date(2027, 7, 5), date(2027, 7, 6))      # Tamuz: Jul 5-6, 2027 (2 days)
        self.assert_rosh_chodesh(date(2027, 8, 4), date(2027, 8, 4))      # Av: Aug 4, 2027 (1 day)
        self.assert_rosh_chodesh(date(2027, 9, 2), date(2027, 9, 3))      # Elul: Sep 2-3, 2027 (2 days)
        
        # Rosh Chodesh periods for Jewish Year 5788 (2027-2028)
        self.assert_rosh_chodesh(date(2027, 10, 31), date(2027, 11, 1))   # Cheshvan: Oct 31-Nov 1, 2027 (2 days)
        self.assert_rosh_chodesh(date(2027, 11, 30), date(2027, 12, 1))   # Kislev: Nov 30-Dec 1, 2027 (2 days)
        self.assert_rosh_chodesh(date(2027, 12, 30), date(2027, 12, 31))  # Teves: Dec 30-31, 2027 (2 days)
        self.assert_rosh_chodesh(date(2028, 1, 29), date(2028, 1, 29))    # Sh'vat: Jan 29, 2028 (1 day)
        self.assert_rosh_chodesh(date(2028, 2, 27), date(2028, 2, 28))    # Adar: Feb 27-28, 2028 (2 days)
        self.assert_rosh_chodesh(date(2028, 3, 28), date(2028, 3, 28))    # Nissan: Mar 28, 2028 (1 day)
        self.assert_rosh_chodesh(date(2028, 4, 26), date(2028, 4, 27))    # Iyyar: Apr 26-27, 2028 (2 days)
        self.assert_rosh_chodesh(date(2028, 5, 26), date(2028, 5, 26))    # Sivan: May 26, 2028 (1 day)
        self.assert_rosh_chodesh(date(2028, 6, 24), date(2028, 6, 25))    # Tamuz: Jun 24-25, 2028 (2 days)
        self.assert_rosh_chodesh(date(2028, 7, 24), date(2028, 7, 24))    # Av: Jul 24, 2028 (1 day)
        self.assert_rosh_chodesh(date(2028, 8, 22), date(2028, 8, 23))    # Elul: Aug 22-23, 2028 (2 days)
    
    
    def test_mashiv_haruach(self):
        """Test Mashiv HaRuach period detection for years 2025-2028."""
        
        # Mashiv HaRuach 2025-2026: Oct 15, 2025 (Simchat Torah) to Apr 2, 2026 (Pesach)
        # Mashiv HaRuach stops at Shacharit of Pesach, so mincha and maariv should be False on end date
        self.assert_condition(lambda conditions: conditions.mashiv_haruach, 
                                     date(2025, 10, 15), date(2026, 4, 2), 
                                     end_date_false_tefillos=['mincha', 'maariv'])
        
        # Mashiv HaRuach 2026-2027: Oct 4, 2026 (Simchat Torah) to Apr 22, 2027 (Pesach)
        self.assert_condition(lambda conditions: conditions.mashiv_haruach, 
                                     date(2026, 10, 4), date(2027, 4, 22), 
                                     end_date_false_tefillos=['mincha', 'maariv'])
        
        # Mashiv HaRuach 2027-2028: Oct 24, 2027 (Simchat Torah) to Apr 11, 2028 (Pesach)
        self.assert_condition(lambda conditions: conditions.mashiv_haruach, 
                                     date(2027, 10, 24), date(2028, 4, 11), 
                                     end_date_false_tefillos=['mincha', 'maariv'])
    
    
    def test_veten_tal_umattar_period(self):
        """Test VeTen Tal UMattar period detection for years 2025-2028."""
        
        # VeTen Tal UMattar 2025-2026: Dec 4 Maariv, 2025 to Apr 2, 2026 (Pesach)
        self.assert_condition(lambda conditions: conditions.veten_tal_umattar, 
                                    date(2025, 12, 5), date(2026, 4, 2), 
                                    end_date_false_tefillos=['shacharit'])
        
        # VeTen Tal UMattar 2026-2027: Dec 4 Maariv, 2026 to Apr 22, 2027 (Pesach)
        self.assert_condition(lambda conditions: conditions.veten_tal_umattar, 
                                    date(2026, 12, 5), date(2027, 4, 22), 
                                    end_date_false_tefillos=['shacharit'])
        
        # VeTen Tal UMattar 2027-2028: Dec 5 Maariv, 2027 to Apr 11, 2028 (Pesach)
        # Note: Dec 5 because 2028 is a leap year
        self.assert_condition(lambda conditions: conditions.veten_tal_umattar, 
                                    date(2027, 12, 6), date(2028, 4, 11), 
                                    end_date_false_tefillos=['shacharit'])    
    
    def test_veten_tal_umattar_2026_comprehensive(self):
        """Comprehensive test for veten_tal_umattar logic for entire year 2026."""
        # 2026: Pesach is April 2, 2026
        # Expected: True from Dec 5, 2025 to April 2, 2026 (shacharis only on April 2)
        # Expected: False from April 3, 2026 to Dec 4, 2026
        # Expected: True from Dec 5, 2026 onwards
        
        pesach_2026 = date(2026, 4, 2)
        start = date(2026, 12, 4)
        
        # Single loop through all dates in 2026
        current_date = date(2026, 1, 1)
        while current_date <= date(2026, 12, 31):
            for tefilla_type in ['shacharis', 'mincha', 'maariv']:
                conditions = self.calendar.get_date_conditions(current_date, tefilla_type)
                
                # Calculate expected result based on ranges
                if current_date == start:
                    expected = (tefilla_type =='maariv')
                elif pesach_2026 < current_date < start:
                    expected = False
                else:
                    expected = True
                
                self.assertEqual(conditions.veten_tal_umattar, expected,
                               f"Failed for {current_date} {tefilla_type}: expected {expected}, got {conditions.veten_tal_umattar}")
            current_date += timedelta(days=1)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
