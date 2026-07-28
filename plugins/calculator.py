import ast
import operator
import re

OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.USub: operator.neg}


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("Unsupported expression")


def handle_calculate(query):
    expression = query.lower().replace("calculate", "").replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/").strip()
    if not re.fullmatch(r"[\d\s+*/().-]+", expression):
        return "I couldn't calculate that. Try something like '5 plus 3'."
    try:
        return f"The answer is {_evaluate(ast.parse(expression, mode='eval').body)}."
    except (ValueError, SyntaxError, ZeroDivisionError):
        return "I couldn't calculate that. Try something like '5 plus 3'."


def register(router_registry):
    router_registry["calculate"] = handle_calculate
