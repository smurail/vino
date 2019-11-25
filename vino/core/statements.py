import re

from Equation import Expression as _Expression


__all__ = ['Statements', 'Equations', 'Inequations', 'StatementsError']


class Expression(_Expression):
    def __init__(self, expression, argorder=[], *args, **kwargs):
        self.value = expression
        super().__init__(expression, argorder, *args, **kwargs)

    def __str__(self):
        return self.value


class StatementsError(Exception):
    pass


class Statements:
    DISCRETE = 1
    CONTINUOUS = 2

    RELATIONS = ('=', '<=', '>=')
    NAME = {
        None: '%s',
        DISCRETE: 'next_%s',
        CONTINUOUS: "%s'"
    }

    def __init__(self, statements, time_type=None):
        if isinstance(statements, str):
            self.statements, self.time_type = self.parse(statements)
        else:
            self.statements = statements
            self.time_type = time_type

    @classmethod
    def dynamics_variable(cls, name):
        if name.endswith("'"):
            return name[:-1], cls.CONTINUOUS
        if name.startswith('next_'):
            return name[5:], cls.DISCRETE
        raise StatementsError(
            "Invalid dynamics left side: %(name)s.",
            {'name': name})

    @classmethod
    def split(cls, statement):
        # Compile regex used to split relations (ie. "x=y", "a>=b"...)
        if not hasattr(cls, '_relation'):
            cls._relation = re.compile(
                r'\s*(%s)\s*' % '|'.join(cls.RELATIONS))
        return tuple(filter(None, map(str.strip, cls._relation.split(statement))))

    @classmethod
    def parse(cls, value):
        statements = [s for s in (s.strip() for s in value.split(',')) if s]
        splitted_statements = (cls.split(stmt) for stmt in statements)
        valid_statements = [s for s in splitted_statements if len(s) == 3]

        if len(statements) != len(valid_statements):
            raise StatementsError(
                "Each statement must contain one of: %(relations)s.",
                {'relations': ', '.join(cls.RELATIONS)})

        try:
            for i, (left, op, right) in enumerate(valid_statements):
                valid_statements[i] = (left, op, Expression(right))
        except: # noqa
            raise StatementsError(
                "Invalid syntax: %(value)s",
                {'value': right})

        return valid_statements, None

    @classmethod
    def from_string(cls, value):
        return Statements(*cls.parse(value))

    def __len__(self):
        return len(self.statements)

    def __iter__(self):
        return iter(self.statements)

    def __setitem__(self, index, value):
        self.statements[index] = value

    def __getitem__(self, index):
        return self.statements[index]

    def __eq__(self, other):
        return (isinstance(other, Statements) and
            (self.statements, self.time_type) == (other.statements, other.time_type))

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return ','.join(
            ''.join((self.NAME[self.time_type] % left, op, str(right)))
            for left, op, right in self.statements)

    def __repr__(self):
        return 'Statements(%r)' % self.statements


class Equations(Statements):
    RELATIONS = ('=')

    @classmethod
    def parse(cls, value):
        statements, time_type = super().parse(value)

        for i, (left, op, right) in enumerate(statements):
            left, new_time_type = Statements.dynamics_variable(left)
            statements[i] = (left, op, right)
            if time_type is None:
                time_type = new_time_type
            elif time_type != new_time_type:
                raise StatementsError("Can't mix different dynamics types.")

        return statements, time_type


class Inequations(Statements):
    RELATIONS = ('<=', '>=')
