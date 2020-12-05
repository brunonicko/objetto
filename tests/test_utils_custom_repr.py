# -*- coding: utf-8 -*-

import pytest

from objetto.utils.custom_repr import custom_iterable_repr, custom_mapping_repr


def test_custom_mapping_repr():
    assert (
        custom_mapping_repr(
            {1: 4, "2": 3, 3: 2, "4": "1"},
            prefix="Mapping<",
            template="{key}=={value}",
            separator="; ",
            suffix=">",
            sorting=True,
            sort_key=lambda i: str(i[1]),
            reverse=True,
            key_repr=lambda k: repr("K" + str(k)),
            value_repr=lambda v: str("V" + str(v)),
        )
        == "Mapping<'K1'==V4; 'K2'==V3; 'K3'==V2; 'K4'==V1>"
    )


def test_custom_iterable_repr():
    assert (
        custom_iterable_repr(
            ["a", 1, 2.0, "3.0", 4, None],
            prefix="Iterable -",
            template="> {value} <",
            separator="-",
            suffix="-",
            sorting=True,
            sort_key=lambda v: str(v),
            reverse=True,
            value_repr=lambda v: str("V" + str(v)),
        )
        == "Iterable -> Va <-> VNone <-> V4 <-> V3.0 <-> V2.0 <-> V1 <-"
    )


if __name__ == "__main__":
    pytest.main()
