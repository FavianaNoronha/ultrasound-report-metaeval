import pytest
from usmeta import graders

def test_ratescore_runs_on_cpu_and_ranks_error_lower():
    pytest.importorskip('RaTEScore'); pytest.importorskip('medspacy')
    g = graders.make('ratescore')  # regression: used to crash with "Torch not compiled with CUDA"
    ref = 'Solid hypoechoic nodule, BI-RADS 3.'
    same, wrong = g.batch([ref, ref], [ref, 'Cystic nodule, BI-RADS 5.'])
    assert same > 0.99 and wrong < same

def test_green_missing_package_gives_clear_error():
    try: import green_score  # noqa
    except ImportError:
        with pytest.raises(RuntimeError, match='green-score'): graders.make('green')
    else: pytest.skip('green_score installed')
