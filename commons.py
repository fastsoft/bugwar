
def commons_iter(table):
    table = [row for row in table if row]
    while table:
        choice = table[-1][0]
        table = [
            [cell for cell in row if cell != choice]
            for row in table
        ]
        table = [row for row in table if row]
        yield choice

def commons(table):
    return list(commons_iter(table))

def only(values):
    if len(values): return values[0]

