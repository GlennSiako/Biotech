from models.single_gene import simulate


def test_steady_state():
    t, x = simulate(alpha=2.0, beta=0.5, x0=0.0, t_span=(0, 50), t_eval=[50])
    assert abs(x[-1] - 4.0) < 0.01  # 2.0 / 0.5 = 4.0
