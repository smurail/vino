# XXX PEP 563 -- Postponed Evaluation of Annotations
from __future__ import annotations

import re

import Equation

from typing import Iterable, List, Tuple, Union, Optional, Pattern


__all__ = ['Statements', 'Equations', 'Inequations', 'StatementsError']


# XXX Monkey patching to allow "'" in variable names, don't do this at home!
Equation.core.nmatch = re.compile("\\s*([a-zA-Z_][a-zA-Z0-9_']*)")


class Expression(Equation.Expression):
    def __init__(self, expression, argorder=[], *args, **kwargs):
        self.value = expression
        super().__init__(expression, argorder, *args, **kwargs)

    def __str__(self):
        return self.value


class DynamicsLeftExpression(Expression):
    DISCRETE = 1
    CONTINUOUS = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dynamics_type = None
        self.variables = []

        for name in super().__iter__():
            if name.endswith("'"):
                self.variables.append(name[:-1])
                new_dynamics_type = self.CONTINUOUS
            elif name.startswith('next_'):
                self.variables.append(name[5:])
                new_dynamics_type = self.DISCRETE
            else:
                raise StatementsError(
                    "Invalid dynamics left expression: %(name)s.",
                    {'name': name})
            if self.dynamics_type is not None and self.dynamics_type != new_dynamics_type:
                raise StatementsError("Can't mix different dynamics types.")
            self.dynamics_type = new_dynamics_type

    def __iter__(self):
        return iter(self.variables)


class StatementsError(Exception):
    pass


StatementLiteral = Tuple[Expression, str, Expression]
ManyStatementLiterals = Iterable[StatementLiteral]


class Statements:
    RELATIONS: Tuple[str, ...] = ('=', '<=', '>=')
    LEFT = Expression

    _relation: Optional[Pattern] = None

    def __init__(self, statements: Union[str, ManyStatementLiterals]):
        if isinstance(statements, str):
            self.statements = self.parse(statements)
        else:
            self.statements = statements

    @classmethod
    def split(cls, statement: str) -> Tuple[str, ...]:
        # Compile regex used to split relations (ie. "x=y", "a>=b"...)
        if cls._relation is None:
            cls._relation = re.compile(
                r'\s*(%s)\s*' % '|'.join(cls.RELATIONS))
        return tuple(filter(None, map(str.strip, cls._relation.split(statement))))

    def parse(self, value: str) -> ManyStatementLiterals:
        statements = [s for s in (s.strip() for s in value.split(',')) if s]
        splitted_statements = (self.split(stmt) for stmt in statements)
        valid_statements = [s for s in splitted_statements if len(s) == 3]
        typed_statements: List[StatementLiteral] = []

        if len(statements) != len(valid_statements):
            raise StatementsError(
                "Each statement must contain one of: %(relations)s.",
                {'relations': ', '.join(self.RELATIONS)})

        try:
            for i, (left, op, right) in enumerate(valid_statements):
                stmt = (self.LEFT(left), op, Expression(right))
                typed_statements.append(stmt)
        except Exception:
            raise StatementsError(
                "Invalid syntax: %(value)s",
                {'value': right})

        return typed_statements

    def __len__(self):
        return len(self.statements)

    def __iter__(self):
        return iter(self.statements)

    def __setitem__(self, index, value):
        self.statements[index] = value

    def __getitem__(self, index):
        return self.statements[index]

    def __eq__(self, other):
        if isinstance(other, Statements):
            return self.statements == other.statements
        return False

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return ','.join(
            ''.join((str(left), op, str(right)))
            for left, op, right in self.statements)

    def __repr__(self):
        return 'Statements(%r)' % self.statements


class Equations(Statements):
    RELATIONS = ('=',)
    LEFT = DynamicsLeftExpression
    DYNAMICS_TYPE_NAME = {
        DynamicsLeftExpression.DISCRETE: 'discrete',
        DynamicsLeftExpression.CONTINUOUS: 'continuous',
    }

    def __init__(
            self,
            statements: Union[str, ManyStatementLiterals],
            dynamics_type: Optional[int] = None):
        self.dynamics_type = dynamics_type
        super().__init__(statements)

    @property
    def dynamics_type_name(self):
        return self.DYNAMICS_TYPE_NAME.get(self.dynamics_type, '')

    def parse(self, value: str) -> ManyStatementLiterals:
        statements = super().parse(value)
        self.dynamics_type = None

        for i, (left, op, right) in enumerate(statements):
            if self.dynamics_type is None:
                self.dynamics_type = left.dynamics_type
            elif self.dynamics_type != left.dynamics_type:
                raise StatementsError("Can't mix different dynamics types.")

        return statements


class Inequations(Statements):
    RELATIONS = ('<=', '>=')
