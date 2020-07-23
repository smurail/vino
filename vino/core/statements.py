# XXX PEP 563 -- Postponed Evaluation of Annotations
from __future__ import annotations

import re

import Equation  # type: ignore

from typing import Iterable, List, Tuple, Union, Optional, Pattern
from itertools import chain


__all__ = ['Statements', 'Equations', 'Inequations', 'StatementsError']


# XXX Monkey patching to allow "'" in variable names, don't do this at home!
Equation.core.nmatch = re.compile("\\s*([a-zA-Z_][a-zA-Z0-9_']*)")


class Expression(Equation.Expression):
    def __init__(self, expression, argorder=[], *args, **kwargs):
        self.value = expression
        super().__init__(expression, argorder, *args, **kwargs)

    def __str__(self):
        return self.value


StatementLiteral = Tuple[Expression, str, Expression]
ManyStatementLiterals = Iterable[StatementLiteral]


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


class Statements:
    RELATIONS: Tuple[str, ...] = ('=', '<=', '>=')
    LEFT = Expression

    _relation: Optional[Pattern] = None

    def __init__(self, statements: Union[str, ManyStatementLiterals]):
        if isinstance(statements, str):
            self.statements = self.parse(statements)
        else:
            self.statements = list(statements)

    @classmethod
    def split(cls, statement: str) -> Tuple[str, ...]:
        # Compile regex used to split relations (ie. "x=y", "a>=b"...)
        if cls._relation is None:
            cls._relation = re.compile(
                r'\s*(%s)\s*' % '|'.join(cls.RELATIONS))
        return tuple(filter(None, map(str.strip, cls._relation.split(statement))))

    def parse(self, value: str) -> List[StatementLiteral]:
        statements = [s for s in (s.strip() for s in value.split(',')) if s]
        splitted_statements = (self.split(stmt) for stmt in statements)
        valid_statements = [s for s in splitted_statements if len(s) == 3]
        typed_statements: List[StatementLiteral] = []

        if len(statements) != len(valid_statements):
            raise StatementsError(
                "Each statement must contain one of: %(relations)s.",
                {'relations': ', '.join(self.RELATIONS)})

        for i, (left, op, right) in enumerate(valid_statements):
            # Process left expression
            try:
                left_expr = self.LEFT(left)
                # XXX Hack to trigger all potential errors...
                repr(left_expr)
            except StatementsError:
                raise
            except Exception:
                raise StatementsError(
                    "Invalid syntax: %(value)s",
                    {'value': left})

            # Process right expression
            try:
                right_expr = Expression(right)
                # XXX Hack to trigger all potential errors...
                repr(right_expr)
            except Exception:
                raise StatementsError(
                    "Invalid syntax: %(value)s",
                    {'value': right})

            typed_statements.append((left_expr, op, right_expr))

        return typed_statements

    def _unparse(self, statement) -> str:
        left, op, right = statement
        return ''.join((str(left), op, str(right)))

    def unparse(self, index: Optional[int] = None) -> str:
        assert index is None or 0 <= index < len(self.statements)
        if index is not None:
            return self._unparse(self.statements[index])
        return ','.join(self._unparse(stmt) for stmt in self.statements)

    @property
    def unparsed_statements(self) -> List[str]:
        return [self.unparse(i) for i in range(len(self.statements))]

    def __len__(self):
        return len(self.statements)

    def __iter__(self):
        return iter(self.statements)

    def __setitem__(self, index: int, value: StatementLiteral):
        assert 0 <= index < len(self.statements)
        self.statements[index] = value

    def __getitem__(self, index: int) -> StatementLiteral:
        assert 0 <= index < len(self.statements)
        return self.statements[index]

    def __eq__(self, other: object):
        if not isinstance(other, Statements):
            return NotImplemented
        return self.statements == other.statements

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return self.unparse()

    def __repr__(self):
        return 'Statements(%r)' % self.statements


class Equations(Statements):
    RELATIONS = ('=',)
    LEFT = DynamicsLeftExpression
    DYNAMICS_TYPE_NAME = {
        DynamicsLeftExpression.DISCRETE: 'discrete',
        DynamicsLeftExpression.CONTINUOUS: 'continuous',
    }

    _show: Optional[Pattern] = None

    def __init__(
            self,
            statements: Union[str, ManyStatementLiterals],
            dynamics_type: Optional[int] = None):
        self.dynamics_type = dynamics_type
        super().__init__(statements)

    @property
    def dynamics_type_name(self):
        return self.DYNAMICS_TYPE_NAME.get(self.dynamics_type, '')

    def parse(self, value):
        statements = super().parse(value)
        self.dynamics_type = None

        for i, (left, op, right) in enumerate(statements):
            if self.dynamics_type is None:
                self.dynamics_type = left.dynamics_type
            elif self.dynamics_type != left.dynamics_type:
                raise StatementsError("Can't mix different dynamics types.")

        variables = chain.from_iterable([stmt[0].variables for stmt in statements])
        self._show = re.compile(r'\b(' + '|'.join(variables) + r')\b')

        return statements

    def _unparse(self, statement):
        left, op, right = statement

        if left.dynamics_type == left.DISCRETE:
            left = left.variables[0] + '_{n+1}'
            right = self._show.sub(r'\1_n', str(right))
        else:
            left, right = str(left), str(right)

        return ''.join((left, op, right))


class Inequations(Statements):
    RELATIONS = ('<=', '>=')
