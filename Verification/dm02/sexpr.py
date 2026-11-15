"""Small lossless-value S-expression reader for KiCad files (not a schematic editor)."""
import json
import re


def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', text)
    stack, result = [], None
    for token in tokens:
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
        elif token == ')':
            if not stack:
                raise ValueError('Unbalanced S-expression')
            result = stack.pop()
        else:
            if not stack:
                raise ValueError('Value outside S-expression')
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if stack or result is None:
        raise ValueError('Incomplete S-expression')
    return result


def children(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == name]


def child(node, name, default=None):
    return next(iter(children(node, name)), default)


def quote(value):
    return json.dumps(str(value), ensure_ascii=False)
