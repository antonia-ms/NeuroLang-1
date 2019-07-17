from .. import expressions
from .. import solver_datalog_naive as sdb
from .. import solver_datalog_extensional_db
from .. import expression_walker as ew
from .. import datalog_chase as dc


C_ = expressions.Constant
S_ = expressions.Symbol
Imp_ = sdb.Implication
Fact_ = sdb.Fact
Eb_ = expressions.ExpressionBlock


class Datalog(
    sdb.DatalogBasic,
    solver_datalog_extensional_db.ExtensionalDatabaseSolver,
    ew.ExpressionBasicEvaluator
):
    def function_gt(self, x: int, y: int)->bool:
        return x > y


def test_non_recursive_predicate_chase_step():
    Q = S_('Q')
    T = S_('T')
    S = S_('S')
    gt = S_('gt')
    x = S_('x')
    y = S_('y')
    z = S_('z')

    datalog_program = Eb_((
        Fact_(Q(C_(1), C_(2))),
        Fact_(Q(C_(2), C_(3))),
        Fact_(Q(C_(8), C_(6))),
        Imp_(T(x, y), Q(x, z) & Q(z, y)),
        Imp_(S(x, y), Q(x, y) & gt(x, y))
    ))

    dl = Datalog()
    dl.walk(datalog_program)

    instance_0 = dl.extensional_database()

    rule = datalog_program.expressions[-1]
    instance_update = dc.chase_step(dl, instance_0, dl.builtins(), rule)
    assert instance_update == {
        S: C_({C_((C_(8), C_(6)))}),
    }

    rule = datalog_program.expressions[-2]
    instance_update = dc.chase_step(dl, instance_0, dl.builtins(), rule)
    assert instance_update == {
        T: C_({C_((C_(1), C_(3)))}),
    }

    instance_1 = dc.merge_instances(instance_0, instance_update)
    instance_update = dc.chase_step(dl, instance_1, dl.builtins(), rule)
    assert len(instance_update) == 0


def test_non_recursive_predicate_chase():
    Q = S_('Q')
    T = S_('T')
    x = S_('x')
    y = S_('y')
    z = S_('z')

    datalog_program = Eb_((
        Fact_(Q(C_(1), C_(2))),
        Fact_(Q(C_(2), C_(3))),
        Imp_(T(x, y), Q(x, z) & Q(z, y))
    ))

    dl = Datalog()
    dl.walk(datalog_program)

    res = dc.build_chase_tree(dl)

    instance_update = {
        T: C_({C_((C_(1), C_(3)))})
    }

    instance_1 = instance_update.copy()
    instance_1.update(dl.extensional_database())

    assert res.instance == dl.extensional_database()
    assert res.children == {
        datalog_program.expressions[-1]: dc.ChaseNode(instance_1, dict())
    }


def test_recursive_predicate_chase_tree():
    Q = S_('Q')
    T = S_('T')
    x = S_('x')
    y = S_('y')
    z = S_('z')

    datalog_program = Eb_((
        Fact_(Q(C_(1), C_(2))),
        Fact_(Q(C_(2), C_(3))),
        Imp_(T(x, y), Q(x, y)),
        Imp_(T(x, y), Q(x, z) & T(z, y))
    ))

    dl = Datalog()
    dl.walk(datalog_program)

    res = dc.build_chase_tree(dl)

    instance_update = {T: dl.extensional_database()[Q]}

    instance_1 = instance_update.copy()
    instance_1.update(dl.extensional_database())

    assert res.instance == dl.extensional_database()
    assert len(res.children) == 1
    first_child = res.children[datalog_program.expressions[-2]]
    assert first_child.instance == instance_1
    assert len(first_child.children) == 1
    second_child = first_child.children[datalog_program.expressions[-1]]

    instance_2 = {
        Q: C_({
            C_((C_(1), C_(2))),
            C_((C_(2), C_(3))),
        }),
        T: C_({
            C_((C_(1), C_(2))),
            C_((C_(2), C_(3))),
            C_((C_(1), C_(3)))
        })
    }

    assert len(second_child.children) == 0
    assert second_child.instance == instance_2


def test_nonrecursive_predicate_chase_solution(N=10):
    Q = S_('Q')
    T = S_('T')
    x = S_('x')
    y = S_('y')
    z = S_('z')

    datalog_program = Eb_(
        tuple(
            Fact_(Q(C_(i), C_(i + 1)))
            for i in range(N)
        ) +
        (Imp_(T(x, y), Q(x, z) & Q(z, y)),)
    )

    dl = Datalog()
    dl.walk(datalog_program)

    solution_instance = dc.build_chase_solution(dl)

    final_instance = {
        Q: C_({
            C_((C_(i), C_(i + 1)))
            for i in range(N)
        }),
        T: C_({
            C_((C_(i), C_(i + 2)))
            for i in range(N - 1)
        })
    }

    assert solution_instance == final_instance


def test_recursive_predicate_chase_solution():
    Q = S_('Q')
    T = S_('T')
    x = S_('x')
    y = S_('y')
    z = S_('z')

    datalog_program = Eb_((
        Fact_(Q(C_(1), C_(2))),
        Fact_(Q(C_(2), C_(3))),
        Imp_(T(x, y), Q(x, y)),
        Imp_(T(x, y), Q(x, z) & T(z, y))
    ))

    dl = Datalog()
    dl.walk(datalog_program)

    solution_instance = dc.build_chase_solution(dl)

    final_instance = {
        Q: C_({
            C_((C_(1), C_(2))),
            C_((C_(2), C_(3))),
        }),
        T: C_({
            C_((C_(1), C_(2))),
            C_((C_(2), C_(3))),
            C_((C_(1), C_(3)))
        })
    }

    assert solution_instance == final_instance