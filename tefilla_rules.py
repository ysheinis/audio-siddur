"""
Tefilla rule engine for Hebrew Audio Siddur.
Handles conditional logic for building prayer services based on Hebrew calendar dates.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, date
from pathlib import Path
import hashlib
import json

# Hebrew calendar integration - REQUIRED
try:
    from pyluach import dates, parshios
except ImportError:
    raise ImportError(
        "pyluach library is required for accurate Hebrew calendar support.\n"
        "Install with: pip install pyluach\n"
        "Without proper Hebrew calendar dates, tefillos cannot be generated correctly."
    )


@dataclass
class ChunkAnnotation:
    """Annotation for a prayer chunk with conditions for when it should be included."""
    name: str
    tefilla_types: List[str]  # ['shacharis', 'mincha', 'maariv']
    conditions: Dict[str, Any]  # {'season': 'summer', 'holiday': 'pesach', etc.}
    required: bool = True  # Whether this chunk is required or optional


@dataclass
class DateConditions:
    """Conditions applicable to a specific date."""
    day_of_week: str  # 'weekday', 'shabbat'
    holiday: Optional[str] = None  # 'pesach', 'shavuot', 'rosh_hashana', 'chanukkah', 'purim', etc.
    rosh_chodesh: bool = False
    chol_hamoed: bool = False
    fast_day: bool = False
    # Special periods
    aseret_yemei_teshuvah: bool = False  # Ten Days of Repentance (Rosh Hashana to Yom Kippur)
    sefirat_haomer: int = 0  # Days of Omer count (0-49, 0 means not in Omer period)
    # Halachic prayer variations (outside Israel)
    mashiv_haruach: bool = False  # "Who causes the wind to blow" - from Shemini Atzeret to Pesach
    veten_tal_umattar: bool = False  # "Give dew and rain" - from December 4/5 to Pesach
    # Derived conditions for complex logic
    hallel_type: str = "none"  # "none", "partial", "full"
    full_shmoneh_esreh: bool = False  # True for weekdays that need full Shmone Esre (excludes major holidays)


class HebrewCalendar:
    """Hebrew calendar integration using pyluach for accurate date conditions."""
    
    def __init__(self):
        pass  # pyluach is guaranteed to be available due to import check
    
    def get_date_conditions(self, target_date: date = None, tefilla_type: str = None) -> DateConditions:
        """Get conditions for a specific date using accurate Hebrew calendar.
        
        Args:
            target_date: Gregorian date
            tefilla_type: Type of tefilla ('maariv', 'shacharis', 'mincha')
                         For maariv, uses next Hebrew date since Hebrew day starts at nightfall
        """
        if target_date is None:
            target_date = date.today()
        
        # Convert Gregorian date to Hebrew date
        hebrew_date = dates.HebrewDate.from_pydate(target_date)
        
        # For Maariv, use the next Hebrew date since Hebrew day starts at nightfall
        if tefilla_type == 'maariv':
            hebrew_date = hebrew_date + 1
        
        
        # Check if it's Shabbat (Hebrew calendar weekday 7)
        day_of_week = 'shabbat' if hebrew_date.weekday() == 7 else 'weekday'
        
        # Check for holidays
        holiday = self._get_holiday_from_hebrew_date(hebrew_date)
        
        # Check for Rosh Chodesh
        rosh_chodesh = self._is_rosh_chodesh_hebrew(hebrew_date)
        
        # Check for Chol Hamoed
        chol_hamoed = self._is_chol_hamoed_hebrew(hebrew_date)
        
        # Check for fast days
        fast_day = self._is_fast_day_hebrew(hebrew_date)
        
        # Check for Aseret Yemei Teshuvah (Ten Days of Repentance)
        aseret_yemei_teshuvah = self._is_aseret_yemei_teshuvah(hebrew_date)
        
        # Calculate Sefirat HaOmer (count from Pesach to Shavuot)
        sefirat_haomer = self._calculate_sefirat_haomer(hebrew_date)
        
        # Calculate Halachic prayer variations (outside Israel)
        mashiv_haruach = self._is_mashiv_haruach_period(hebrew_date, tefilla_type)
        veten_tal_umattar = self._is_veten_tal_umattar_period(target_date)
        
        # Calculate Hallel type
        hallel_type = self._calculate_hallel_type(hebrew_date, holiday, rosh_chodesh, sefirat_haomer)
        
        # Calculate full Shmone Esre flag
        full_shmoneh_esreh = self._calculate_full_shmoneh_esreh(day_of_week, holiday)
        
        return DateConditions(
            day_of_week=day_of_week,
            holiday=holiday,
            rosh_chodesh=rosh_chodesh,
            chol_hamoed=chol_hamoed,
            fast_day=fast_day,
            aseret_yemei_teshuvah=aseret_yemei_teshuvah,
            sefirat_haomer=sefirat_haomer,
            mashiv_haruach=mashiv_haruach,
            veten_tal_umattar=veten_tal_umattar,
            hallel_type=hallel_type,
            full_shmoneh_esreh=full_shmoneh_esreh
        )
    
    
    def _get_holiday_from_hebrew_date(self, hebrew_date) -> Optional[str]:
        """Get holiday from Hebrew date using pyluach."""
        month_name = hebrew_date.month_name()
        day = hebrew_date.day
        
        # Major holidays
        if month_name == 'Tishrei':
            if day in [1, 2]:
                return 'rosh_hashana'
            elif day == 10:
                return 'yom_kippur'
            elif day in [15, 16, 17, 18, 19, 20, 21]:
                return 'sukkot'
            elif day in [22, 23]:
                return 'shmini_atzeret'
        # Pesach (15-21 Nisan) - month number varies by leap year
        elif month_name == 'Nisan' and day in [15, 16, 17, 18, 19, 20, 21]:
            return 'pesach'
        # Shavuot (6-7 Sivan) - month number varies by leap year  
        elif month_name == 'Sivan' and day in [6, 7]:
            return 'shavuot'
        elif month_name == 'Kislev':
            if day in [25, 26, 27, 28, 29, 30]:
                return 'chanukkah'
        elif month_name == 'Tevet':
            if day in [1, 2, 3]:
                return 'chanukkah'
        # Purim (14 Adar)
        # In regular years: Adar (month 6)
        # In leap years: Adar 2 (month 7), not Adar I (month 6)
        elif month_name in ['Adar', 'Adar 2'] and day == 14:
            return 'purim'
        
        return None
    
    def _is_rosh_chodesh_hebrew(self, hebrew_date) -> bool:
        """
        Check if Hebrew date is Rosh Chodesh.
        Rosh Chodesh occurs on:
        - 1st day of every month (always)
        - 30th day of months that have 30 days (also Rosh Chodesh for next month)
        """
        # Always Rosh Chodesh on the 1st of any month
        if hebrew_date.day == 1:
            return True
        
        # Check if this month has 30 days, and if so, the 30th is also Rosh Chodesh
        if hebrew_date.day == 30:
            # Get the number of days in this Hebrew month by trying to create day 30
            try:
                # Try to create day 30 of this month
                test_date = hebrew_date.replace(day=30)
                # If we can create it, this month has 30 days
                return True
            except ValueError:
                # If we can't create day 30, this month has 29 days
                return False
        
        return False
    
    def _is_chol_hamoed_hebrew(self, hebrew_date) -> bool:
        """Check if Hebrew date is Chol Hamoed."""
        month_name = hebrew_date.month_name()
        day = hebrew_date.day
        
        # Chol Hamoed Sukkot (Tishrei 16-20)
        if month_name == 'Tishrei' and 16 <= day <= 20:
            return True
        # Chol Hamoed Pesach (Nisan 16-20)
        elif month_name == 'Nisan' and 16 <= day <= 20:
            return True
        
        return False
    
    def _is_fast_day_hebrew(self, hebrew_date) -> bool:
        """Check if Hebrew date is a fast day."""
        month_name = hebrew_date.month_name()
        day = hebrew_date.day
        
        # Major fast days
        fast_days = [
            ('Tevet', 10),   # 10 Tevet
            ('Av', 9),       # 9 Av
            ('Tammuz', 17),  # 17 Tammuz
            ('Tishrei', 3),  # 3 Tishrei (Tzom Gedaliah)
        ]
        
        return (month_name, day) in fast_days
    
    def _is_aseret_yemei_teshuvah(self, hebrew_date) -> bool:
        """
        Check if Hebrew date is during Aseret Yemei Teshuvah (Ten Days of Repentance).
        This is the period from Rosh Hashana (1-2 Tishrei) through Yom Kippur (10 Tishrei).
        """
        month_name = hebrew_date.month_name()
        day = hebrew_date.day
        
        # Aseret Yemei Teshuvah is only in Tishrei
        if month_name != 'Tishrei':
            return False
        
        # From 1 Tishrei (Rosh Hashana) through 10 Tishrei (Yom Kippur)
        return 1 <= day <= 10
    
    def _calculate_sefirat_haomer(self, hebrew_date) -> int:
        """
        Calculate the day of Sefirat HaOmer (0-49).
        Sefirat HaOmer is the 49-day count from the second day of Pesach to Shavuot.
        Returns 0 if not in the Omer period.
        """
        month = hebrew_date.month
        day = hebrew_date.day
        
        # Sefirat HaOmer starts on 16 Nisan (second day of Pesach)
        # and ends on 5 Sivan (day before Shavuot)
        
        # Check if we're in Nisan
        if hebrew_date.month_name() == 'Nisan':
            # Omer starts on 16 Nisan
            if day >= 16:
                return day - 15  # Day 16 Nisan = Omer day 1
        
        # Check if we're in Iyar (full month is in Omer)
        elif hebrew_date.month_name() == 'Iyar':
            # Iyar has 29 days, so Omer days 15-43
            return 15 + day  # Day 1 Iyar = Omer day 16
        
        # Check if we're in Sivan
        elif hebrew_date.month_name() == 'Sivan':
            # Omer ends on 5 Sivan (day before Shavuot)
            if day <= 5:
                return 44 + day  # Day 1 Sivan = Omer day 45
        
        # Not in Omer period
        return 0
    
    def _is_mashiv_haruach_period(self, hebrew_date, tefilla_type: str = None) -> bool:
        """
        Determine if we should say Mashiv HaRuach (outside Israel).
        From Maariv of Shemini Atzeret (22 Tishrei) until Shacharit of first day of Pesach (15 Nisan).
        """
        month_name = hebrew_date.month_name()
        day = hebrew_date.day
        
        # From 22 Tishrei (Shemini Atzeret) through end of year
        if month_name == 'Tishrei' and day >= 22:  # Tishrei 22 onwards
            # For Maariv on Shemini Atzeret (22 Tishrei), start saying Mashiv HaRuach
            if day == 22 and tefilla_type == 'maariv':
                return True
            # For all other tefillos on 22 Tishrei and later, say Mashiv HaRuach
            elif day > 22:
                return True
        
        # All of winter months: Cheshvan, Kislev, Tevet, Shevat, Adar
        if month_name in ['Cheshvan', 'Kislev', 'Tevet', 'Shevat', 'Adar', 'Adar 2']:
            return True
        
        # On 15 Nisan (first day of Pesach)
        if month_name == 'Nisan' and day == 15:
            # Stop saying Mashiv HaRuach from Shacharit of Pesach onwards
            if tefilla_type in ['shacharis', 'mincha']:
                return False
            # Maariv on Pesach still says Mashiv HaRuach (it's the previous day's Maariv)
            elif tefilla_type == 'maariv':
                return True
        
        # Until 14 Nisan (day before Pesach)
        if month_name == 'Nisan' and day <= 14:  # Nisan 1-14
            return True
        
        return False
    
    def _is_veten_tal_umattar_period(self, gregorian_date: date) -> bool:
        """
        Determine if we should say VeTen Tal UMattar (outside Israel).
        Start: at Ma'ariv on December 4 most years.
        If the upcoming Gregorian year is a leap year, start at Ma'ariv on December 5.
        End: until Pesach.
        """
        year = gregorian_date.year
        
        # Check if the upcoming year (when we'll be saying the prayer) is a leap year
        upcoming_year = year + 1
        is_leap_year = (upcoming_year % 4 == 0 and upcoming_year % 100 != 0) or (upcoming_year % 400 == 0)
        
        # Set start date: December 4 for regular years, December 5 for leap years
        start_day = 5 if is_leap_year else 4
        veten_tal_start = date(year, 12, start_day)
        
        # Get Pesach date for this Hebrew year
        hebrew_date = dates.HebrewDate.from_pydate(gregorian_date)
        hebrew_year = hebrew_date.year
        
        # Pesach is always 15 Nisan
        pesach_hebrew = dates.HebrewDate(hebrew_year, 7, 15)  # 15 Nisan
        pesach_gregorian = pesach_hebrew.to_pydate()
        
        # VeTen Tal UMattar period: from December 4/5 until Pesach
        return veten_tal_start <= gregorian_date < pesach_gregorian
    
    def _calculate_hallel_type(self, hebrew_date, holiday: Optional[str], rosh_chodesh: bool, sefirat_haomer: int) -> str:
        """Calculate the type of Hallel to be recited.
        
        Returns:
            "full": Complete Hallel (Pesach, Shavuot, Sukkot, Chanukkah)
            "partial": Partial Hallel (Rosh Chodesh, Chol Hamoed)
            "none": No Hallel (regular weekdays, most of Omer period)
        """
        # Full Hallel on major holidays
        if holiday in ['pesach', 'shavuot', 'sukkot', 'chanukkah']:
            return "full"
        
        # Partial Hallel on Rosh Chodesh and Chol Hamoed
        if rosh_chodesh or (holiday and 'chol_hamoed' in str(holiday)):
            return "partial"
        
        # No Hallel during most of Sefirat HaOmer (except last days)
        if sefirat_haomer > 0 and sefirat_haomer < 33:
            return "none"
        
        # Full Hallel on last days of Omer (Lag BaOmer onwards)
        if sefirat_haomer >= 33:
            return "full"
        
        # Default: no Hallel
        return "none"
    
    def _calculate_full_shmoneh_esreh(self, day_of_week: str, holiday: Optional[str]) -> bool:
        """
        Calculate if we need full Shmone Esre (weekday middle brochos).
        
        Returns True for weekdays that are NOT major holidays.
        Major holidays that need different middle brochos:
        - pesach, shavuot, sukkot, rosh_hashana, yom_kippur, shmini_atzeret
        
        Minor holidays that still need full Shmone Esre:
        - chanukkah, purim, rosh_chodesh, chol_hamoed, fast_days
        """
        # Only weekdays can have full Shmone Esre
        if day_of_week != 'weekday':
            return False
        
        # Major holidays that need different middle brochos
        major_holidays = ['pesach', 'shavuot', 'sukkot', 'rosh_hashana', 'yom_kippur', 'shmini_atzeret']
        
        # If it's a major holiday, don't use full Shmone Esre
        if holiday in major_holidays:
            return False
        
        # All other weekdays (including minor holidays like Chanukkah, Purim) use full Shmone Esre
        return True


class TefillaRuleEngine:
    """Rule engine for building prayer services based on conditions."""
    
    def __init__(self, chunk_annotations: List[ChunkAnnotation]):
        self.chunk_annotations = {ann.name: ann for ann in chunk_annotations}
        self.hebrew_calendar = HebrewCalendar()
    
    def build_tefilla(self, tefilla_type: str, target_date: date = None) -> List[str]:
        """Build a tefilla by selecting appropriate chunks based on conditions."""
        if target_date is None:
            target_date = date.today()
        
        date_conditions = self.hebrew_calendar.get_date_conditions(target_date, tefilla_type)
        
        # Select chunks that match the conditions, maintaining TEXT_MAP order
        selected_chunks = []
        for chunk_name, annotation in self.chunk_annotations.items():
            if self._chunk_matches_conditions(annotation, tefilla_type, date_conditions):
                selected_chunks.append(chunk_name)
        
        return selected_chunks
    
    def _chunk_matches_conditions(self, annotation: ChunkAnnotation, tefilla_type: str, date_conditions: DateConditions) -> bool:
        """Check if a chunk matches the given conditions."""
        # Check if chunk applies to this tefilla type
        if tefilla_type not in annotation.tefilla_types:
            return False
        
        # Check all conditions in the annotation
        for condition_key, condition_value in annotation.conditions.items():
            if not self._condition_matches(condition_key, condition_value, date_conditions):
                return False
        
        return True
    
    def _condition_matches(self, condition_key: str, condition_value: Any, date_conditions: DateConditions) -> bool:
        """Check if a specific condition matches the date conditions."""
        if condition_key == 'mashiv_haruach':
            return date_conditions.mashiv_haruach == condition_value
        elif condition_key == 'veten_tal_umattar':
            return date_conditions.veten_tal_umattar == condition_value
        elif condition_key == 'day_of_week':
            return date_conditions.day_of_week == condition_value
        elif condition_key == 'holiday':
            if isinstance(condition_value, list):
                # Handle list of holidays (including None for "no holiday")
                return date_conditions.holiday in condition_value
            else:
                # Handle single holiday
                return date_conditions.holiday == condition_value
        elif condition_key == 'rosh_chodesh':
            return date_conditions.rosh_chodesh == condition_value
        elif condition_key == 'chol_hamoed':
            return date_conditions.chol_hamoed == condition_value
        elif condition_key == 'fast_day':
            return date_conditions.fast_day == condition_value
        elif condition_key == 'aseret_yemei_teshuvah':
            return date_conditions.aseret_yemei_teshuvah == condition_value
        elif condition_key == 'sefirat_haomer':
            # Can match specific day or range
            if isinstance(condition_value, int):
                return date_conditions.sefirat_haomer == condition_value
            elif isinstance(condition_value, dict):
                # Support ranges like {"min": 1, "max": 33} for partial Hallel
                min_day = condition_value.get('min', 0)
                max_day = condition_value.get('max', 49)
                return min_day <= date_conditions.sefirat_haomer <= max_day
        elif condition_key == 'hallel_type':
            if isinstance(condition_value, list):
                # Handle list of hallel types
                return date_conditions.hallel_type in condition_value
            else:
                # Handle single hallel type
                return date_conditions.hallel_type == condition_value
        elif condition_key == 'full_shmoneh_esreh':
            return date_conditions.full_shmoneh_esreh == condition_value
        elif condition_key == 'always':
            return condition_value  # Always include if condition_value is True
        
        return False
    
    def get_tefilla_hash(self, tefilla_type: str, target_date: date = None) -> str:
        """Generate a hash for a tefilla based on its conditions."""
        if target_date is None:
            target_date = date.today()
        
        date_conditions = self.hebrew_calendar.get_date_conditions(target_date, tefilla_type)
        chunk_list = self.build_tefilla(tefilla_type, target_date)
        
        # Create a string representation of the conditions and chunks
        conditions_str = f"{tefilla_type}_{date_conditions.day_of_week}"
        if date_conditions.holiday:
            conditions_str += f"_{date_conditions.holiday}"
        if date_conditions.rosh_chodesh:
            conditions_str += "_rosh_chodesh"
        if date_conditions.chol_hamoed:
            conditions_str += "_chol_hamoed"
        if date_conditions.fast_day:
            conditions_str += "_fast_day"
        if date_conditions.aseret_yemei_teshuvah:
            conditions_str += "_aseret_yemei_teshuvah"
        if date_conditions.sefirat_haomer > 0:
            conditions_str += f"_omer{date_conditions.sefirat_haomer}"
        if date_conditions.mashiv_haruach:
            conditions_str += "_mashiv_haruach"
        if date_conditions.veten_tal_umattar:
            conditions_str += "_veten_tal_umattar"
        if date_conditions.hallel_type != "none":
            conditions_str += f"_hallel_{date_conditions.hallel_type}"
        if date_conditions.full_shmoneh_esreh:
            conditions_str += "_full_shmoneh_esreh"
        
        chunks_str = "_".join(chunk_list)
        hash_input = f"{conditions_str}_{chunks_str}"
        
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]


def load_chunk_annotations() -> List[ChunkAnnotation]:
    """Load chunk annotations from TEXT_MAP structure."""
    from tts_map import TEXT_MAP
    
    annotations = []
    for chunk_name, chunk_data in TEXT_MAP.items():
        annotation = ChunkAnnotation(
            name=chunk_name,
            tefilla_types=chunk_data["tefilla_types"],
            conditions=chunk_data["conditions"]
            # Note: order is no longer needed - chunks are ordered by TEXT_MAP sequence
        )
        annotations.append(annotation)
    
    return annotations
""