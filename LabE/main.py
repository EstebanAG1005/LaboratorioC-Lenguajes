import re
from collections import defaultdict
from graphviz import Digraph


class LexerRule:
    def __init__(self, name, pattern, action):
        self.name = name
        self.pattern = pattern
        self.action = action


def parse_yalex(file_path):
    lexer_rules = []
    inside_tokens_rule = False

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()

            if line.startswith("rule tokens"):
                inside_tokens_rule = True
                continue

            if inside_tokens_rule:
                if ("|" in line or "ws" in line) and "return" in line:
                    # Se extrae el nombre del token que está después de 'return'
                    token_name = line.split("return")[1].split("}")[0].strip()
                    lexer_rules.append(LexerRule(token_name, None, None))

    return lexer_rules


class Grammar:
    def __init__(self, terminals, non_terminals, rules):
        self.terminals = terminals
        self.non_terminals = non_terminals
        self.rules = rules
        self.nullables = self.compute_nullables()  # Agrega esta línea

    # Agrega este método a la clase `Grammar`
    def compute_nullables(self):
        nullables = set()
        change = True
        while change:
            change = False
            for left, right in self.rules:
                if left not in nullables and all(s in nullables for s in right):
                    nullables.add(left)
                    change = True
        return nullables


def parse_yapar(file_path):
    with open(file_path, "r") as file:
        content = file.readlines()

    token_pattern = re.compile(r"^%token\s+((?:\w+\s*)+)$")
    ignore_pattern = re.compile(r"^IGNORE\s+((?:\w+\s*)+)$")
    rule_pattern = re.compile(r"%%\n((?:.|\n)+)$")

    terminals = set()
    ignored = set()

    for line in content:
        token_match = token_pattern.match(line)
        if token_match:
            terminals.update(token_match.group(1).strip().split())

        ignore_match = ignore_pattern.match(line)
        if ignore_match:
            ignored.update(ignore_match.group(1).strip().split())

    terminals -= ignored

    rule_content_index = content.index("%%\n") + 1
    rule_lines = content[rule_content_index:]

    non_terminals = set()
    rules = []

    # Concatenar todas las líneas de una misma regla en una sola línea
    rule_lines = "".join([line.strip() for line in rule_lines]).split(";")

    for line in rule_lines:
        line = line.strip()
        if ":" in line:
            left, right = re.split(r"\s*:\s*", line.strip(), 1)
            non_terminals.add(left.strip())
            productions = re.split(r"\s*\|\s*", right.strip())
            for production in productions:
                rules.append((left.strip(), production.split()))

    return Grammar(terminals, non_terminals, rules)


class LR0Item:
    def __init__(self, left, right, lookahead):
        self.left = left
        self.right = tuple(right)  # Convertir la lista 'right' en una tupla
        self.lookahead = lookahead

    def __repr__(self):
        right_repr = list(map(str, self.right))
        right_repr.insert(self.lookahead, ".")
        return f"{self.left} -> {' '.join(right_repr)}"

    def __eq__(self, other):
        return (
            self.left == other.left
            and self.right == other.right
            and self.lookahead == other.lookahead
        )

    def __hash__(self):
        return hash((self.left, self.right, self.lookahead))


def closure(grammar, items):
    closure_set = set(items)
    for item in items:
        if (
            item.lookahead < len(item.right)
            and item.right[item.lookahead] in grammar.non_terminals
        ):
            new_items = [
                LR0Item(rule[0], rule[1], 0)
                for rule in grammar.rules
                if rule[0] == item.right[item.lookahead]
            ]
            # Comprobar si los nuevos elementos ya están en 'closure_set'
            new_items = [item for item in new_items if item not in closure_set]

            if new_items:
                closure_set |= closure(grammar, new_items)
    return closure_set


def goto(grammar, items, symbol):
    new_items = [
        LR0Item(item.left, item.right, item.lookahead + 1)
        for item in items
        if item.lookahead < len(item.right) and item.right[item.lookahead] == symbol
    ]
    return closure(grammar, new_items)


def lr0(grammar):
    initial_items = [
        LR0Item(rule[0], rule[1], 0)
        for rule in grammar.rules
        if rule[0] == grammar.rules[0][0]
    ]
    states = [closure(grammar, initial_items)]
    transitions = []

    stack = [states[0]]
    while stack:
        state = stack.pop()
        for symbol in grammar.terminals | grammar.non_terminals:
            new_state = goto(grammar, state, symbol)
            if new_state and new_state not in states:
                states.append(new_state)
                stack.append(new_state)
            if new_state:
                transitions.append((state, symbol, new_state))
    return states, transitions


def visualize_lr0(states, transitions):
    print("States:")
    for i, state in enumerate(states):
        print(f"State {i}:")
        for item in sorted(state, key=lambda x: (x.left, x.right, x.lookahead)):
            print(f"  {item}")

    print("\nTransitions:")
    for t in sorted(
        transitions, key=lambda x: (states.index(x[0]), x[1], states.index(x[2]))
    ):
        print(f"State {states.index(t[0])} --{t[1]}--> State {states.index(t[2])}")


def first(grammar, symbol, seen=None):
    if seen is None:
        seen = set()
    elif symbol in seen:
        return set()

    seen.add(symbol)

    first_set = set()

    # Si el símbolo es terminal, agregarlo al conjunto FIRST y retornarlo
    if symbol in grammar.terminals:
        first_set.add(symbol)
        return first_set

    # Si el símbolo es no terminal, calcular FIRST para cada regla que comienza con ese símbolo
    for rule in grammar.rules:
        if rule[0] == symbol:
            for s in rule[1]:
                if s in grammar.terminals:
                    first_set.add(s)
                    break
                else:
                    first_set |= first(grammar, s, seen)
                    if "" not in first_set:
                        break
            else:
                first_set.add("")

    return first_set


def first_star(grammar, sequence):
    first_set = set()
    for symbol in sequence:
        first_set.update(first(grammar, symbol))
        if symbol not in grammar.nullables:
            break
    return first_set


def compute_follow(grammar):
    follow = defaultdict(set)
    follow[grammar.rules[0][0]].add("$")
    change = True
    while change:
        change = False
        for left, right in grammar.rules:
            follow_set = follow[left]
            for symbol in reversed(right):
                if symbol in grammar.non_terminals:
                    if not follow_set.issubset(follow[symbol]):
                        follow[symbol].update(follow_set)
                        change = True
                    if "" in first(grammar, symbol):
                        follow_set = follow_set.union(first(grammar, symbol) - {""})
                    else:
                        follow_set = first(grammar, symbol)
                else:
                    follow_set = {symbol}
    return follow


def visualize_lr0_graph(states, transitions, output_filename="lr0_graph.gv"):
    dot = Digraph("LR0", filename=output_filename, format="pdf")
    dot.attr(rankdir="LR", size="15,10")  # aumenta el tamaño del gráfico
    dot.attr(fontsize="14")  # aumenta el tamaño de la fuente
    dot.attr(ranksep="1")  # aumenta el espacio entre los rangos de nodos
    dot.attr(nodesep="1")  # aumenta el espacio entre los nodos en el mismo rango

    # Agrega los estados al gráfico
    for i, state in enumerate(states):
        state_label = f"State {i}\n"
        state_label += "\n".join(
            [
                f"{item}"
                for item in sorted(state, key=lambda x: (x.left, x.right, x.lookahead))
            ]
        )
        dot.node(str(i), label=state_label, shape="rectangle")

    # Agrega las transiciones al gráfico
    for t in sorted(
        transitions, key=lambda x: (states.index(x[0]), x[1], states.index(x[2]))
    ):
        dot.edge(str(states.index(t[0])), str(states.index(t[2])), label=t[1])

    # Genera y guarda el gráfico
    dot.view()


if __name__ == "__main__":
    grammar = parse_yapar("LabE/slr-1.yalp")
    yalex_rules = parse_yalex("LabE/slr-1.yal")

    # Validar tokens
    yalex_tokens = {rule.name for rule in yalex_rules}
    yapar_tokens = grammar.terminals

    print("Tokens en YALex:")
    print(yalex_tokens)
    print("Tokens en YAPar:")
    print(yapar_tokens)

    if not yapar_tokens.issubset(yalex_tokens):
        print(
            "Error: Algunos tokens en el archivo YAPar no están presentes en el archivo YALex."
        )
    else:
        print("Validación de tokens exitosa.")

    missing_tokens = yapar_tokens - yalex_tokens
    if missing_tokens:
        print(f"Tokens faltantes en YALex: {missing_tokens}")

    # Aquí, después de procesar YALex, calcular los conjuntos Primero y Siguiente
    first_sets = {symbol: first(grammar, symbol) for symbol in grammar.non_terminals}
    follow_sets = compute_follow(grammar)

    print("\nConjuntos Primero:")
    for symbol, first_set in first_sets.items():
        print(f"  {symbol}: {first_set}")

    print("\nConjuntos Siguiente:")
    for symbol, follow_set in follow_sets.items():
        print(f"  {symbol}: {follow_set}")

    states, transitions = lr0(grammar)
    visualize_lr0(states, transitions)

    visualize_lr0_graph(states, transitions)
