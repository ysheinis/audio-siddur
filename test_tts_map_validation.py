#!/usr/bin/env python3

import unittest
import json
from datetime import date
from tefilla_rules import HebrewCalendar, TefillaRuleEngine, ChunkAnnotation, DateConditions


class TestTtsMapValidation(unittest.TestCase):
    """Test that all conditions in tts_map.py can be processed by the rule engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calendar = HebrewCalendar()
        
        # Import tts_map module directly
        import tts_map
        self.text_map = tts_map.TEXT_MAP
        
        # Create rule engine with all chunks from tts_map
        chunk_annotations = self._create_chunk_annotations()
        self.rule_engine = TefillaRuleEngine(chunk_annotations)
    
    def _create_chunk_annotations(self):
        """Create ChunkAnnotation objects from tts_map data."""
        annotations = []
        
        for chunk_name, chunk_data in self.text_map.items():
            if isinstance(chunk_data, dict) and 'conditions' in chunk_data:
                conditions = chunk_data['conditions']
                tefilla_types = chunk_data.get('tefilla_types', ['shacharis', 'mincha', 'maariv'])
                
                # Ensure tefilla_types is a list
                if isinstance(tefilla_types, str):
                    tefilla_types = [tefilla_types]
                
                annotation = ChunkAnnotation(
                    name=chunk_name,
                    tefilla_types=tefilla_types,
                    conditions=conditions
                )
                annotations.append(annotation)
        
        return annotations
    
    def test_no_duplicate_chunk_names(self):
        """Test that there are no duplicate chunk names in tts_map."""
        chunk_names = list(self.text_map.keys())
        unique_chunk_names = set(chunk_names)
        
        # Check for duplicates
        if len(chunk_names) != len(unique_chunk_names):
            duplicates = []
            seen = set()
            for name in chunk_names:
                if name in seen:
                    duplicates.append(name)
                else:
                    seen.add(name)
            
            self.fail(f"Duplicate chunk names found: {duplicates}")
    
    def test_all_condition_keys_supported(self):
        """Test that all condition keys in tts_map are supported by DateConditions."""
        # Get all unique condition keys from tts_map
        all_condition_keys = set()
        for chunk_data in self.text_map.values():
            if isinstance(chunk_data, dict) and 'conditions' in chunk_data:
                all_condition_keys.update(chunk_data['conditions'].keys())
        
        # Get all supported keys from DateConditions
        date_conditions = DateConditions(day_of_week="weekday")
        supported_keys = set(date_conditions.__dict__.keys())
        
        # Add 'always' as a special case (it's handled by the rule engine, not DateConditions)
        supported_keys.add('always')
        
        # Check for unsupported keys
        unsupported_keys = all_condition_keys - supported_keys
        self.assertEqual(len(unsupported_keys), 0, 
                        f"Unsupported condition keys found: {unsupported_keys}")
    
    def test_all_condition_values_supported(self):
        """Test that all condition values in tts_map are valid."""
        # Test with a sample date to get actual DateConditions
        test_date = date(2024, 1, 15)  # Monday
        test_tefilla_type = "shacharis"
        
        # Get actual conditions for this date
        actual_conditions = self.calendar.get_date_conditions(test_date, test_tefilla_type)
        
        # Define valid values for each condition type
        valid_values = {
            'day_of_week': ['weekday', 'shabbat'],
            'holiday': [None, 'rosh_hashana', 'yom_kippur', 'sukkot', 'shmini_atzeret', 
                       'pesach', 'shavuot', 'chanukkah', 'purim'],
            'rosh_chodesh': [True, False],
            'chol_hamoed': [True, False],
            'fast_day': [True, False],
            'aseret_yemei_teshuvah': [True, False],
            'sefirat_haomer': list(range(50)),  # 0-49
            'mashiv_haruach': [True, False],
            'veten_tal_umattar': [True, False],
            'hallel_type': ['none', 'partial', 'full'],
            'full_shmoneh_esreh': [True, False],
            'always': [True, False]
        }
        
        # Test each chunk's conditions
        for chunk_name, chunk_data in self.text_map.items():
            if isinstance(chunk_data, dict) and 'conditions' in chunk_data:
                conditions = chunk_data['conditions']
                
                # Validate each condition value
                for condition_key, condition_value in conditions.items():
                    if condition_key in valid_values:
                        # Handle list values (like holiday lists)
                        if isinstance(condition_value, list):
                            for value in condition_value:
                                self.assertIn(value, valid_values[condition_key],
                                            f"Invalid value '{value}' for condition '{condition_key}' in chunk '{chunk_name}'. "
                                            f"Valid values: {valid_values[condition_key]}")
                        else:
                            self.assertIn(condition_value, valid_values[condition_key],
                                        f"Invalid value '{condition_value}' for condition '{condition_key}' in chunk '{chunk_name}'. "
                                        f"Valid values: {valid_values[condition_key]}")
                    else:
                        self.fail(f"Unknown condition key '{condition_key}' in chunk '{chunk_name}'")
                
                # Test that the rule engine can process these conditions
                try:
                    # Create a test annotation
                    test_annotation = ChunkAnnotation(
                        name=f"test_{chunk_name}",
                        tefilla_types=[test_tefilla_type],
                        conditions=conditions
                    )
                    
                    # Test condition matching
                    matches = self.rule_engine._chunk_matches_conditions(
                        test_annotation, test_tefilla_type, actual_conditions
                    )
                    
                    # The test should not raise an exception
                    self.assertIsInstance(matches, bool, 
                                        f"Condition matching failed for chunk '{chunk_name}'")
                    
                except Exception as e:
                    self.fail(f"Failed to process conditions for chunk '{chunk_name}': {e}")
    
    def test_specific_condition_values(self):
        """Test specific condition values that are used in tts_map."""
        # Test various date scenarios to ensure all condition values work
        test_scenarios = [
            # Regular weekday
            (date(2024, 1, 15), "shacharis", {
                "day_of_week": "weekday",
                "holiday": None,
                "rosh_chodesh": False,
                "chol_hamoed": False,
                "full_shmoneh_esreh": True,
                "hallel_type": "none"
            }),
            
            # Shabbat
            (date(2024, 1, 20), "shacharis", {
                "day_of_week": "shabbat",
                "holiday": None,
                "rosh_chodesh": False,
                "chol_hamoed": False,
                "full_shmoneh_esreh": False,
                "hallel_type": "none"
            }),
            
            # Rosh Hashana
            (date(2024, 10, 3), "shacharis", {
                "day_of_week": "weekday",
                "holiday": "rosh_hashana",
                "rosh_chodesh": True,  # Rosh Hashana is Tishrei 1, which is Rosh Chodesh
                "chol_hamoed": False,
                "aseret_yemei_teshuvah": True,
                "full_shmoneh_esreh": False,
                "hallel_type": "full"
            }),
            
            # Chol Hamoed Pesach
            (date(2024, 4, 25), "shacharis", {
                "day_of_week": "weekday",
                "holiday": "pesach",
                "rosh_chodesh": False,
                "chol_hamoed": True,
                "full_shmoneh_esreh": True,  # Chol Hamoed uses full Shmone Esre
                "hallel_type": "partial"  # Chol Hamoed has partial Hallel
            }),
            
            # Chanukkah
            (date(2024, 12, 26), "shacharis", {
                "day_of_week": "weekday",
                "holiday": "chanukkah",
                "rosh_chodesh": False,
                "chol_hamoed": False,
                "full_shmoneh_esreh": True,
                "hallel_type": "full"
            })
        ]
        
        for test_date, tefilla_type, expected_conditions in test_scenarios:
            with self.subTest(date=test_date, tefilla_type=tefilla_type):
                actual_conditions = self.calendar.get_date_conditions(test_date, tefilla_type)
                
                # Test each expected condition
                for key, expected_value in expected_conditions.items():
                    actual_value = getattr(actual_conditions, key)
                    self.assertEqual(actual_value, expected_value,
                                   f"Condition '{key}' mismatch for {test_date} {tefilla_type}: "
                                   f"expected {expected_value}, got {actual_value}")
    
    def test_condition_value_types(self):
        """Test that all condition values have the correct types."""
        test_date = date(2024, 1, 15)
        test_tefilla_type = "shacharis"
        conditions = self.calendar.get_date_conditions(test_date, test_tefilla_type)
        
        # Define expected types for each condition
        expected_types = {
            'day_of_week': str,
            'holiday': (str, type(None)),
            'rosh_chodesh': bool,
            'chol_hamoed': bool,
            'fast_day': bool,
            'aseret_yemei_teshuvah': bool,
            'sefirat_haomer': int,
            'mashiv_haruach': bool,
            'veten_tal_umattar': bool,
            'hallel_type': str,
            'full_shmoneh_esreh': bool
        }
        
        for key, expected_type in expected_types.items():
            actual_value = getattr(conditions, key)
            if isinstance(expected_type, tuple):
                # Handle union types (like str | None)
                self.assertTrue(any(isinstance(actual_value, t) for t in expected_type),
                              f"Condition '{key}' has wrong type: expected one of {expected_type}, got {type(actual_value)}")
            else:
                self.assertIsInstance(actual_value, expected_type,
                                    f"Condition '{key}' has wrong type: expected {expected_type}, got {type(actual_value)}")
    
    def test_rule_engine_can_process_all_chunks(self):
        """Test that the rule engine can process all chunks without errors."""
        test_date = date(2024, 1, 15)  # Monday
        test_tefilla_type = "shacharis"
        
        # Get conditions for this date
        conditions = self.calendar.get_date_conditions(test_date, test_tefilla_type)
        
        # Test that rule engine can process all chunks
        try:
            # Test each chunk individually to ensure no errors
            for chunk_name, chunk in self.rule_engine.chunk_annotations.items():
                if test_tefilla_type in chunk.tefilla_types:
                    matches = self.rule_engine._chunk_matches_conditions(chunk, test_tefilla_type, conditions)
                    self.assertIsInstance(matches, bool)
                
        except Exception as e:
            self.fail(f"Rule engine failed to process chunks: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
