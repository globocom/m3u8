import pytest

@pytest.mark.xfail
def test_should_fail_if_first_line_not_EXTM3U():
    assert 0

@pytest.mark.xfail
def test_should_fail_if_expected_ts_chunk_line_is_not_valid():
    assert 0

@pytest.mark.xfail
def test_should_fail_if_EXT_X_MEDIA_SEQUENCE_is_diffent_from_sequence_number_of_first_uri():
    assert 0

@pytest.mark.xfail
def test_should_fail_if_more_than_one_EXT_X_MEDIA_SEQUENCE():
    assert 0

@pytest.mark.xfail
def test_should_fail_if_EXT_X_MEDIA_SEQUENCE_is_not_a_number():
    assert 0

@pytest.mark.xfail
def test_should_validate_supported_EXT_X_VERSION():
    assert 0

@pytest.mark.xfail
def test_should_fail_if_any_EXTINF_duration_is_greater_than_TARGET_DURATION():
    assert 0

@pytest.mark.xfail
def test_should_fail_if_TARGET_DURATION_not_found():
    assert 0
