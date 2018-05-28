# Copyright (c) 2018 CEA
# Author: Yann Leprince <yann.leprince@cea.fr>
#
# This software is made available under the MIT licence, see LICENCE.txt.

import numpy as np
import pytest

from neuroglancer_scripts.data_types import (
    NG_DATA_TYPES,
    NG_INTEGER_DATA_TYPES,
    get_chunk_dtype_transformer,
)


def test_data_types_lists():
    for data_type in NG_DATA_TYPES:
        np.dtype(data_type)
    for data_type in NG_INTEGER_DATA_TYPES:
        assert np.issubdtype(data_type, np.integer)


@pytest.mark.parametrize("float_dtype", [
    np.float32,
    np.float64,
    pytest.param("float96",
                 marks=pytest.mark.skipif(not hasattr(np, "float96"),
                                          reason="no float96 dtype")),
    pytest.param("float128",
                 marks=pytest.mark.skipif(not hasattr(np, "float128"),
                                          reason="no float128 dtype")),
])
def test_dtype_conversion_float_to_int(float_dtype):
    reference_test_data = np.array(
        [-100, 0.4, 0.6, 2**8, 2**16, 2**32, 2**63],
        dtype=float_dtype
    )
    test_data = np.copy(reference_test_data)
    t = get_chunk_dtype_transformer(test_data.dtype, "uint8")
    assert np.array_equal(
        t(test_data),
        np.array([0, 0, 1, 255, 255, 255, 255], dtype="uint8")
    )
    # Ensure that the input data was not modified in-place
    assert np.array_equal(test_data, reference_test_data)

    t = get_chunk_dtype_transformer(test_data.dtype, "uint16")
    assert np.array_equal(
        t(test_data),
        np.array([0, 0, 1, 256, 65535, 65535, 65535], dtype="uint16")
    )
    # Ensure that the input data was not modified in-place
    assert np.array_equal(test_data, reference_test_data)

    t = get_chunk_dtype_transformer(test_data.dtype, "uint32")
    assert np.array_equal(
        t(test_data),
        np.array([0, 0, 1, 256, 65536, 2**32-1, 2**32-1], dtype="uint32")
    )
    # Ensure that the input data was not modified in-place
    assert np.array_equal(test_data, reference_test_data)

    # Test with 2**64 is expected to fail, see below.
    t = get_chunk_dtype_transformer(test_data.dtype, "uint64")
    assert np.array_equal(
        t(test_data),
        np.array([0, 0, 1, 256, 65536, 2**32, 2**63], dtype="uint64")
    )
    # Ensure that the input data was not modified in-place
    assert np.array_equal(test_data, reference_test_data)


@pytest.mark.xfail(reason="known bug in NumPy", strict=True)
def test_dtype_conversion_float_to_uint64():
    # Conversion to uint64 may result in loss of precision, because of a known
    # bug / approximation in NumPy, where dtype promotion between a 64-bit
    # (u)int and any float will return float64, even though this type can only
    # hold all integers up to 2**53 (see e.g.
    # https://github.com/numpy/numpy/issues/8851).
    test_data = np.array([2**64])
    t = get_chunk_dtype_transformer(test_data.dtype, "uint64")
    assert np.array_equal(
        t(test_data),
        np.array([2**64-1], dtype="uint64")
    )


@pytest.mark.parametrize("dtype", NG_DATA_TYPES)
def test_dtype_conversion_identity(dtype):
    if np.issubdtype(dtype, np.integer):
        iinfo = np.iinfo(dtype)
        test_data = np.array([iinfo.min, 0, iinfo.max], dtype=dtype)
    else:
        finfo = np.finfo(dtype)
        test_data = np.array([finfo.min, 0, finfo.max, np.inf],
                             dtype=dtype)
    t = get_chunk_dtype_transformer(dtype, dtype)
    res = t(test_data)
    assert np.array_equal(res, test_data)


@pytest.mark.parametrize("dtype", NG_INTEGER_DATA_TYPES)
def test_dtype_conversion_integer_upcasting(dtype):
    iinfo = np.iinfo(dtype)
    test_data = np.array([iinfo.min, iinfo.max], dtype=dtype)
    t = get_chunk_dtype_transformer(test_data.dtype, "uint64")
    assert np.array_equal(t(test_data), test_data)
