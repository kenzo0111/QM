from constants import LABO_BARANGAYS


def test_labo_barangays_dict_complete():
    """Ensure the LABO_BARANGAYS constant contains 52 barangays as expected."""
    assert isinstance(LABO_BARANGAYS, dict)
    assert len(LABO_BARANGAYS) == 52
