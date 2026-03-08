from src.identity import build_event_id, canonicalize_url


def test_canonicalize_url_removes_tracking_query_and_www() -> None:
    url = "https://www.meetup.com/awskrug/events/313352636/?eventOrigin=group_events_list&utm_source=test"
    assert canonicalize_url(url) == "https://meetup.com/awskrug/events/313352636"


def test_build_event_id_matches_www_variants() -> None:
    first_id, first_canonical = build_event_id(
        "AI·SW마에스트로 제17기 연수생 모집 - 부산센터",
        "https://swmaestro.ai/sw/main/notifyMentee.do?menuNo=200091",
        "AI·SW마에스트로",
    )
    second_id, second_canonical = build_event_id(
        "2026년도 AI·SW마에스트로 제17기 연수생 모집 - 부산 센터",
        "https://www.swmaestro.ai/sw/main/notifyMentee.do?menuNo=200091&utm_source=ig",
        "AI·SW마에스트로",
    )

    assert first_canonical == second_canonical
    assert first_id == second_id
