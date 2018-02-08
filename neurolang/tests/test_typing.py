import pytest

import typing

from .. import symbols_and_types


def test_typing_callable_from_annotated_function():
    def fun(a: int, b: str)->float:
        pass

    t = symbols_and_types.typing_callable_from_annotated_function(fun)

    assert t.__origin__ == typing.Callable
    assert (t.__args__[0] == int) and (t.__args__[1] == str)
    assert t.__args__[2] == float


def test_get_type_args():
    args = symbols_and_types.get_type_args(typing.Set)
    assert args == tuple()

    args = symbols_and_types.get_type_args(typing.Set[int])
    assert args == (int,)


def test_is_subtype_base_types():
    assert symbols_and_types.is_subtype(int, int)
    assert symbols_and_types.is_subtype(int, float)
    assert symbols_and_types.is_subtype(str, str)
    assert not symbols_and_types.is_subtype(str, int)
    assert symbols_and_types.is_subtype(int, typing.Any)
    assert symbols_and_types.is_subtype(int, typing.Union[int, str])
    assert symbols_and_types.is_subtype(str, typing.Union[int, str])
    assert not symbols_and_types.is_subtype(typing.Set, typing.Union[int, str])

    assert symbols_and_types.is_subtype(
        typing.Callable[[int], int],
        typing.Callable[[int], int]
    )
    assert symbols_and_types.is_subtype(
        typing.Callable[[int], int],
        typing.Callable[[int], float]
    )
    assert not symbols_and_types.is_subtype(
        typing.Set,
        typing.Callable
    )

    assert symbols_and_types.is_subtype(
        typing.AbstractSet[int], typing.AbstractSet[int]
    )
    assert symbols_and_types.is_subtype(
        typing.AbstractSet[int], typing.AbstractSet[float]
    )

    with pytest.raises(ValueError, message="typing Generic not supported"):
        assert symbols_and_types.is_subtype(
            typing.Set[int],
            typing.Generic[typing.T]
        )


def test_replace_subtype():
    assert (
        typing.Set ==
        symbols_and_types.replace_type_variable(int, typing.Set, typing.T)
    )
    assert (
        str ==
        symbols_and_types.replace_type_variable(int, str, typing.T)
    )

    assert (
        typing.Set[float] ==
        symbols_and_types.replace_type_variable(
            int, typing.Set[float], typing.T
        )
    )

    assert (
        typing.Set[float] ==
        symbols_and_types.replace_type_variable(
            float, typing.Set[typing.T], typing.T
        )
    )

    assert (
        typing.Tuple[float, int] ==
        symbols_and_types.replace_type_variable(
            float, typing.Tuple[typing.T, int], typing.T
        )
    )

    assert (
        typing.Set[str] !=
        symbols_and_types.replace_type_variable(
            float, typing.Set[typing.T], typing.T
        )
    )


def test_get_type_and_value():
    type_, value = symbols_and_types.get_type_and_value(3)
    assert type_ == int
    assert value == 3

    type_, value = symbols_and_types.get_type_and_value(
        symbols_and_types.Symbol(int, 3)
    )
    assert type_ == int
    assert value == 3

    type_, value = symbols_and_types.get_type_and_value(
        symbols_and_types.Identifier('a'),
        {symbols_and_types.Identifier('a'): symbols_and_types.Symbol(int, 3)}
    )
    assert type_ == int
    assert value == 3

    def f(a: int)->int:
        return 0

    type_, value = symbols_and_types.get_type_and_value(f)

    assert type_ == typing.Callable[[int], int]
    assert value == f


def test_type_validation_value():
    def f(a: int)->int:
        return 0

    symbol_table = {
        symbols_and_types.Identifier('r'): symbols_and_types.Symbol(
             typing.AbstractSet[str],
             {'a'}
        )
    }

    values = (
        3, {3, 8}, 'try', f, (3, 'a'),
        symbols_and_types.Symbol(typing.Tuple[str, float], ('a', 3.)),
        symbols_and_types.Identifier('r'),
        {'a': 3}
    )
    types_ = (
        int, typing.AbstractSet[int],
        typing.Text, typing.Callable[[int], int],
        typing.Tuple[int, str], typing.Tuple[str, float],
        symbol_table[symbols_and_types.Identifier('r')].type,
        typing.Mapping[str, int]
    )

    for i, v in enumerate(values):
        assert symbols_and_types.type_validation_value(
            v, typing.Any,
            symbol_table=symbol_table
        )

        for j, t in enumerate(types_):
            if i == j:
                assert symbols_and_types.type_validation_value(
                    v, t, symbol_table=symbol_table
                )
                assert symbols_and_types.type_validation_value(
                    v, typing.Union[t, types_[(i + 1) % len(types_)]],
                    symbol_table=symbol_table
                )
            else:
                assert not symbols_and_types.type_validation_value(
                    v, t, symbol_table=symbol_table
                )
                assert not symbols_and_types.type_validation_value(
                    v, typing.Union[t, types_[(i + 1) % len(types_)]],
                    symbol_table=symbol_table
                )

    with pytest.raises(ValueError, message="typing Generic not supported"):
        assert symbols_and_types.type_validation_value(
            None,
            typing.Generic[typing.T]
        )


def test_Symbol():
    v = 3
    t = int
    s = symbols_and_types.Symbol(t, v)
    assert s.value == v
    assert s.type == t

    with pytest.raises(symbols_and_types.NeuroLangTypeException):
        s = symbols_and_types.Symbol(t, 'a')


def test_Identifier():
    a = symbols_and_types.Identifier('a')
    assert a == a
    assert a == symbols_and_types.Identifier('a')
    assert a == 'a'
    assert hash(a) == hash('a')
    assert a['b'] == symbols_and_types.Identifier('a.b')
    assert a['b'].parent() == a


def test_SymbolTable():
    st = symbols_and_types.SymbolTable()
    s1 = symbols_and_types.Symbol(int, 3)
    s2 = symbols_and_types.Symbol(int, 4)
    s3 = symbols_and_types.Symbol(float, 5.)
    s4 = symbols_and_types.Symbol(int, 5)
    s6 = symbols_and_types.Symbol(str, 'a')

    assert len(st) == 0

    st[symbols_and_types.Identifier('s1')] = s1
    assert len(st) == 1
    assert 's1' in st
    assert st['s1'] == s1
    assert st.symbols_by_type(s1.type) == {'s1': s1}

    st[symbols_and_types.Identifier('s2')] = s2
    assert len(st) == 2
    assert 's2' in st
    assert st['s2'] == s2
    assert st.symbols_by_type(s1.type) == {'s1': s1, 's2': s2}

    st[symbols_and_types.Identifier('s3')] = s3
    assert len(st) == 3
    assert 's3' in st
    assert st['s3'] == s3
    assert st.symbols_by_type(s1.type) == {'s1': s1, 's2': s2}
    assert st.symbols_by_type(s3.type) == {'s3': s3}

    del st['s1']
    assert len(st) == 2
    assert 's1' not in st
    assert 's1' not in st.symbols_by_type(s1.type)

    assert {int, float} == st.types()

    stb = st.create_scope()
    assert 's2' in stb
    assert 's3' in stb
    stb[symbols_and_types.Identifier('s4')] = s4
    assert 's4' in stb
    assert 's4' not in st

    stb[symbols_and_types.Identifier('s5')] = None
    assert 's5' in stb
    assert stb[symbols_and_types.Identifier('s5')] is None

    stc = stb.create_scope()
    stc[symbols_and_types.Identifier('s6')] = s6
    assert {int, float, str} == stc.types()
    assert stc.symbols_by_type(int) == {'s2': s2, 's4': s4}

    assert set(iter(stc)) == {'s2', 's3', 's4', 's5', 's6'}

    with pytest.raises(ValueError):
        stb[symbols_and_types.Identifier('s6')] = 5


def test_get_callable_arguments_and_return():
    c = typing.Callable[[int, str], float]
    args, ret = symbols_and_types.get_Callable_arguments_and_return(c)
    assert args == (int, str)
    assert ret == float