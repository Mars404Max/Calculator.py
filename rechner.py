import ast
import operator as op
import math
import sys

# /Users/mars404/HomeWork/rechner.py

# Supported binary operators
# Whitelisting System
_BINOPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.LShift: op.lshift,
    ast.RShift: op.rshift,
}

# Supported unary operators
_UNARYOPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
    ast.Invert: op.invert,
}

# Whitelisted math functions and constants
_ALLOWED_FUNCS = {
    name: getattr(math, name)
    for name in (
        "sin", "cos", "tan", "asin", "acos", "atan",
        "sinh", "cosh", "tanh",
        "log", "log10", "log2", "exp", "sqrt", "ceil", "floor", "fabs",
        "degrees", "radians", "pow", "factorial"
    )
}
_ALLOWED_CONSTS = {"pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf, "nan": math.nan}


class EvalError(ValueError):
    pass

# Recursive evaluation of AST nodes
def _eval_node(node, names):
    # Numbers / constants
    if isinstance(node, ast.Constant):  # Python 3.8+
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise EvalError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.Num):  # older Python
        return node.n

    # Names (variables or allowed constants)
    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        if node.id in _ALLOWED_CONSTS:
            return _ALLOWED_CONSTS[node.id]
        raise EvalError(f"Unknown identifier: {node.id}")

    # Unary operations
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _UNARYOPS:
            val = _eval_node(node.operand, names)
            return _UNARYOPS[op_type](val)
        raise EvalError(f"Unsupported unary operator: {op_type}")

    # Binary operations
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, names)
        right = _eval_node(node.right, names)
        op_type = type(node.op)
        if op_type in _BINOPS:
            return _BINOPS[op_type](left, right)
        raise EvalError(f"Unsupported binary operator: {op_type}")

    # Function calls (only allowed simple names)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EvalError("Only direct function calls are allowed")
        fname = node.func.id
        if fname not in _ALLOWED_FUNCS:
            raise EvalError(f"Function not allowed: {fname}")
        args = [_eval_node(a, names) for a in node.args]
        # no kwargs allowed
        return _ALLOWED_FUNCS[fname](*args)

    # Parentheses/grouping are represented by the contained node in AST; no special handling needed

    raise EvalError(f"Unsupported expression element: {type(node)}")


def evaluate(expr, /, **variables):
    """
    Safely evaluate a math expression string and return the result.
    Supported: numbers, + - * / // % **, bit shifts/xor, unary +/-, parentheses,
    math.* functions listed in _ALLOWED_FUNCS, and constants pi/e/tau.
    Pass variables as keyword args to provide identifiers.
    Example: evaluate("sin(pi/2) + x", x=1)
    """
    if not isinstance(expr, str):
        raise TypeError("expr must be a string")
    try:
        parsed = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise EvalError(f"Syntax error: {e}")

    # Walk AST to ensure only allowed node types appear
    for node in ast.walk(parsed):
        if isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call,
                             ast.Load, ast.Name, ast.Constant, ast.Num,
                             ast.Pow, ast.Add, ast.Sub, ast.Mult, ast.Div,
                             ast.Mod, ast.FloorDiv, ast.UAdd, ast.USub,
                             ast.Invert, ast.LShift, ast.RShift, ast.BitXor,
                             ast.Tuple)):
            continue
        # Allow ast.Attribute only for math.*? We disallow attributes to be safe
        raise EvalError(f"Disallowed expression element: {type(node)}")

    return _eval_node(parsed.body, variables)


if __name__ == "__main__":
    # Simple CLI: evaluate expression passed as args, or read lines from stdin
    if len(sys.argv) > 1:
        expr = " ".join(sys.argv[1:])
        try:
            result = evaluate(expr)
        except Exception as e:
            print("Error:", e)
            sys.exit(2)
        print(result)
    else:
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    print(evaluate(line))
                except Exception as e:
                    print("Error:", e)
        except KeyboardInterrupt:
            pass