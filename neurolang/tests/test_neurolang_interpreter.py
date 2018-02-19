from .. import neurolang as nl
from .. import solver
from typing import Set


def test_assignment_values():
    command = '''
        a = 1
        b = "a"
        c = 1.2
        d = 1.2 + 1.
        e = 1 + 2 * 5
        f = 2. ** 3.
        g = f
    '''

    nli = nl.NeuroLangInterpreter()
    ast = nl.parser(command)
    nli.evaluate(ast)

    assert type(nli.symbol_table['a'].value) == int
    assert nli.symbol_table['a'].value == 1
    assert nli.symbol_table['b'].value == "a"
    assert nli.symbol_table['c'].value == 1.2
    assert nli.symbol_table['d'].value == 2.2
    assert nli.symbol_table['e'].value == 11
    assert nli.symbol_table['f'].value == 8.
    assert nli.symbol_table['g'].value == 8.


def test_queries():

    class FourInts(int, solver.FiniteDomain):
        pass

    class FourIntsSetSolver(solver.SetBasedSolver):
        type_name = 'four_int'
        type = FourInts

        def predicate_equal_to(self, value: int)->FourInts:
            return FourInts(value)

        def predicate_singleton_set(self, value_it: int)->Set[FourInts]:
            return {FourInts(1)}

    nli = nl.NeuroLangInterpreter(
        category_solvers=[FourIntsSetSolver()],
    )

    script = '''
    one is a four_int equal_to 1
    two is a four_int equal_to 2
    three is a four_int equal_to 3
    oneset are four_ints singleton_set 1
    '''

    ast = nl.parser(script)
    nli.evaluate(ast)

    assert nli.symbol_table['one'].value == 1
    assert nli.symbol_table['two'].value == 2
    assert nli.symbol_table['three'].value == 3
    assert len(nli.symbol_table['oneset'].value) == 1
    assert next(iter(nli.symbol_table['oneset'].value)) == 1