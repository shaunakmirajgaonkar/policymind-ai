"""
Safe evaluation of user-supplied arithmetic formulas — reused proven
pattern from DecisionMind AI / ClimateVision AI. AST-walked, no
eval()/exec(). See those projects' test suites for the original
security verification (blocks __import__, open(), attribute-chain escapes).
"""
import ast
import operator

_ALLOWED_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                   ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class FormulaError(ValueError):
    pass


def _eval_node(node, variables):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, variables)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise FormulaError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise FormulaError(f"Unknown variable: {node.id}")
        return variables[node.id]
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BINOPS:
            raise FormulaError(f"Unsupported operator: {op_type.__name__}")
        return _ALLOWED_BINOPS[op_type](_eval_node(node.left, variables), _eval_node(node.right, variables))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_UNARYOPS:
            raise FormulaError(f"Unsupported unary operator: {op_type.__name__}")
        return _ALLOWED_UNARYOPS[op_type](_eval_node(node.operand, variables))
    if isinstance(node, ast.Call):
        allowed = {"min": min, "max": max, "abs": abs}
        if isinstance(node.func, ast.Name) and node.func.id in allowed:
            return allowed[node.func.id](*[_eval_node(a, variables) for a in node.args])
        raise FormulaError("Only min(), max(), abs() function calls are allowed")
    raise FormulaError(f"Unsupported expression: {type(node).__name__}")


def compile_formula(formula: str):
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"Invalid formula syntax: {e}")

    def impact_fn(**variables):
        return float(_eval_node(tree, variables))
    return impact_fn


def extract_variable_names(formula: str) -> set:
    tree = ast.parse(formula, mode="eval")
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
