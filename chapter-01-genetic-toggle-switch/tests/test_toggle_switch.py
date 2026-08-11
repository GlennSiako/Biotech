from models.toggle_switch import simulate


def test_bistability():
    """With symmetric, high-cooperativity parameters the toggle switch is bistable."""
    params = (2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 4.0, 4.0)
    t1, a1, b1 = simulate(params, y0=[0.1, 2.0], t_span=(0, 100), t_eval=[100])
    t2, a2, b2 = simulate(params, y0=[2.0, 0.1], t_span=(0, 100), t_eval=[100])
    assert a1[-1] < b1[-1]  # settles A-off, B-on
    assert a2[-1] > b2[-1]  # settles A-on, B-off
