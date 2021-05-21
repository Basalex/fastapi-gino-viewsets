import pytest

from fastapi_gino_viewsets.utils import camel_to_snake_case


@pytest.mark.parametrize('input, output', (
        ('Case', 'case'),
        ('CaseCamel', 'case_camel'),
        ('CCaseCamel', 'ccase_camel'),
))
def test_camel_to_snake_case(input, output):
    assert camel_to_snake_case(input) == output
