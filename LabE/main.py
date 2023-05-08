import re
from collections import defaultdict
from graphviz import Digraph


class LexerRule:
    def __init__(self, name, pattern, action):
        self.name = name
        self.pattern = pattern
        self.action = action


def parse_yalex(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    rule_pattern = re.compile(
        r"let\s+(\w+)\s+=\s+\"(.+?)\"\n", re.MULTILINE | re.DOTALL
    )
    action_pattern = re.compile(r"rule\s+tokens\s*=\s*((?:.|\n)+?)$", re.MULTILINE)
    rule_matches = rule_pattern.findall(content)
    action_match = action_pattern.search(content)
    action_lines = action_match.group(1).strip().split("\n")

    lexer_rules = []
    for name, pattern in rule_matches:
        action = ""
        for line in action_lines:
            if line.startswith(f"| {name}"):
                action = line[len(name) + 3 :].strip()
                break
        lexer_rules.append(LexerRule(name, pattern, action))
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
        content = file.read()

    token_pattern = re.compile(r"%token\s+((?:\w+\s*)+)\n", re.MULTILINE)
    ignore_pattern = re.compile(r"IGNORE\s+((?:\w+\s*)+)\n", re.MULTILINE)
    rule_pattern = re.compile(r"%%\n((?:.|\n)+)$", re.MULTILINE)

    token_match = token_pattern.search(content)
    ignore_match = ignore_pattern.search(content)
    rule_match = rule_pattern.search(content)

    terminals = set(token_match.group(1).strip().split())
    ignored = set(ignore_match.group(1).strip().split())
    rule_lines = rule_match.group(1).strip().split("\n")

    non_terminals = set()
    rules = []

    for line in rule_lines:
        if ":" in line:
            left, right = line.strip().split(":")
            non_terminals.add(left.strip())
            for production in right.strip().split("|"):
                rules.append((left.strip(), production.strip().split()))

    return Grammar(terminals, non_terminals, rules)


class LR0Item:
    def __init__(self, left, right, lookahead):
        self.left = left
        self.right = tuple(right)  # Convertir la lista 'right' en una tupla
        self.lookahead = lookahead

    def __repr__(self):
        return f"{self.left} -> {self.right[:self.lookahead]}.{self.right[self.lookahead:]}"

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


def first(grammar, symbol):
    if symbol in grammar.terminals:
        return {symbol}
    first_set = set()
    for rule in grammar.rules:
        if rule[0] == symbol:
            for s in rule[1]:
                first_set.update(first(grammar, s))
                if s not in grammar.nullables:
                    break
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
            for i, symbol in enumerate(right):
                if symbol in grammar.non_terminals:
                    new_follow = first_star(grammar, right[i + 1 :])
                    if "$" in new_follow:
                        new_follow.remove("$")
                        new_follow |= follow[left]
                    if not new_follow.issubset(follow[symbol]):
                        change = True
                        follow[symbol].update(new_follow)
    return follow


def visualize_lr0_graph(states, transitions, output_filename="lr0_graph.gv"):
    dot = Digraph("LR0", filename=output_filename, format="png")
    dot.attr(rankdir="LR", size="8,5")

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
    grammar = parse_yapar("LabE\yapar_file.txt")
    yalex_rules = parse_yalex("LabE\yalex_file.txt")

    # Validar tokens
    yalex_tokens = {rule.name for rule in yalex_rules}
    yapar_tokens = grammar.terminals
    if not yapar_tokens.issubset(yalex_tokens):
        print(
            "Error: Algunos tokens en el archivo YAPar no están presentes en el archivo YALex."
        )
    else:
        print("Validación de tokens exitosa.")

    # Calcular conjuntos Primero y Siguiente
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

    states, transitions = lr0(grammar)
    visualize_lr0_graph(states, transitions)
