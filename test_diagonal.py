from loopscope.diagonal import diagonal_demo


def test_diagonal_construction_inverts_every_candidate():
    rows = diagonal_demo()
    assert len(rows) == 4
    assert all(row.is_wrong for row in rows)
    assert all(row.predict != row.actual_diagonal_behaviour for row in rows)
