def list_to_str(ls):
    return ''.join(ls)

def compose(inner, outer):
    return lambda x: outer(inner(x))

