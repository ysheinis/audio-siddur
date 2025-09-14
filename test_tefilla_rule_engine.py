"""
Unit tests for TefillaRuleEngine chunk selection logic.

Tests the rule engine's ability to match prayer chunks to date conditions.
"""

import unittest
from datetime import date, timedelta

from tefilla_rules import HebrewCalendar, TefillaRuleEngine, DateConditions, ChunkAnnotation


class TestTefillaRuleEngine(unittest.TestCase):
    """Test TefillaRuleEngine chunk selection logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test chunk annotations for the rule engine
        test_chunks = [
            ChunkAnnotation(
                name="test_weekday",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"day_of_week": "weekday"}
            ),
            ChunkAnnotation(
                name="test_shabbat",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"day_of_week": "shabbat"}
            )
        ]
        self.rule_engine = TefillaRuleEngine(test_chunks)
        
        # Create test chunk annotations
        self.test_chunks = [
            ChunkAnnotation(
                name="test_weekday",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"day_of_week": "weekday"}
            ),
            ChunkAnnotation(
                name="test_shabbat",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"day_of_week": "shabbat"}
            ),
            ChunkAnnotation(
                name="test_holiday",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"holiday": "pesach"}
            ),
            ChunkAnnotation(
                name="test_rosh_chodesh",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"rosh_chodesh": True}
            ),
            ChunkAnnotation(
                name="test_mashiv_haruach",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"mashiv_haruach": True}
            ),
            ChunkAnnotation(
                name="test_full_hallel",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"hallel_type": "full"}
            ),
            ChunkAnnotation(
                name="test_full_shmoneh_esreh",
                tefilla_types=["shacharis", "mincha", "maariv"],
                conditions={"full_shmoneh_esreh": True}
            )
        ]
    
    def test_weekday_chunk_selection(self):
        """Test chunk selection for weekday."""
        # Create weekday conditions
        weekday_conditions = DateConditions(
            day_of_week="weekday",
            holiday=None,
            rosh_chodesh=False,
            chol_hamoed=False,
            fast_day=False,
            aseret_yemei_teshuvah=False,
            sefirat_haomer=0,
            mashiv_haruach=False,
            veten_tal_umattar=False,
            hallel_type="none",
            full_shmoneh_esreh=True
        )
        
        # Test chunk matching
        self.assertTrue(self.rule_engine._chunk_matches_conditions(
            self.test_chunks[0], "shacharis", weekday_conditions
        ))
        
        self.assertFalse(self.rule_engine._chunk_matches_conditions(
            self.test_chunks[1], "shacharis", weekday_conditions  # Shabbat chunk
        ))
    
    def test_holiday_chunk_selection(self):
        """Test chunk selection for holiday."""
        # Create Pesach conditions
        pesach_conditions = DateConditions(
            day_of_week="weekday",
            holiday="pesach",
            rosh_chodesh=False,
            chol_hamoed=False,
            fast_day=False,
            aseret_yemei_teshuvah=False,
            sefirat_haomer=1,
            mashiv_haruach=False,
            veten_tal_umattar=False,
            hallel_type="full",
            full_shmoneh_esreh=False
        )
        
        # Test chunk matching
        self.assertTrue(self.rule_engine._chunk_matches_conditions(
            self.test_chunks[2], "shacharis", pesach_conditions  # Holiday chunk
        ))
        
        # Weekday chunk should also match Pesach conditions since Pesach is a weekday
        # (The holiday chunk has more specific conditions, but weekday chunk is more general)
        self.assertTrue(self.rule_engine._chunk_matches_conditions(
            self.test_chunks[0], "shacharis", pesach_conditions  # Weekday chunk
        ))
    
    def test_condition_matching_with_lists(self):
        """Test condition matching with list values."""
        # Test holiday list matching
        holiday_conditions = DateConditions(
            day_of_week="weekday",
            holiday="pesach",
            rosh_chodesh=False,
            chol_hamoed=False,
            fast_day=False,
            aseret_yemei_teshuvah=False,
            sefirat_haomer=0,
            mashiv_haruach=False,
            veten_tal_umattar=False,
            hallel_type="full",
            full_shmoneh_esreh=False
        )
        
        # Create chunk with holiday list
        holiday_list_chunk = ChunkAnnotation(
            name="test_holiday_list",
            tefilla_types=["shacharis", "mincha", "maariv"],
            conditions={"holiday": ["pesach", "shavuot", "sukkot"]}
        )
        
        self.assertTrue(self.rule_engine._chunk_matches_conditions(
            holiday_list_chunk, "shacharis", holiday_conditions
        ))
        
        # Test hallel_type list matching
        hallel_conditions = DateConditions(
            day_of_week="weekday",
            holiday="pesach",
            rosh_chodesh=False,
            chol_hamoed=False,
            fast_day=False,
            aseret_yemei_teshuvah=False,
            sefirat_haomer=0,
            mashiv_haruach=False,
            veten_tal_umattar=False,
            hallel_type="full",
            full_shmoneh_esreh=False
        )
        
        # Create chunk with hallel_type list
        hallel_list_chunk = ChunkAnnotation(
            name="test_hallel_list",
            tefilla_types=["shacharis", "mincha", "maariv"],
            conditions={"hallel_type": ["full", "partial"]}
        )
        
        self.assertTrue(self.rule_engine._chunk_matches_conditions(
            hallel_list_chunk, "shacharis", hallel_conditions
        ))
    
    def test_tefilla_type_matching(self):
        """Test that chunks only match for their specified tefilla types."""
        # Create conditions
        conditions = DateConditions(
            day_of_week="weekday",
            holiday=None,
            rosh_chodesh=False,
            chol_hamoed=False,
            fast_day=False,
            aseret_yemei_teshuvah=False,
            sefirat_haomer=0,
            mashiv_haruach=False,
            veten_tal_umattar=False,
            hallel_type="none",
            full_shmoneh_esreh=True
        )
        
        # Create chunk that only applies to Mincha
        mincha_only_chunk = ChunkAnnotation(
            name="test_mincha_only",
            tefilla_types=["mincha"],
            conditions={"day_of_week": "weekday"}
        )
        
        # Should match for Mincha
        self.assertTrue(self.rule_engine._chunk_matches_conditions(
            mincha_only_chunk, "mincha", conditions
        ))
        
        # Should NOT match for Shacharis
        self.assertFalse(self.rule_engine._chunk_matches_conditions(
            mincha_only_chunk, "shacharis", conditions
        ))
        
        # Should NOT match for Maariv
        self.assertFalse(self.rule_engine._chunk_matches_conditions(
            mincha_only_chunk, "maariv", conditions
        ))


if __name__ == '__main__':
    unittest.main()
