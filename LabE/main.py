import re
from collections import defaultdict, deque
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
                if "|" in line and "return" in line:
                    # Extract the token name after 'return' and remove unnecessary characters
                    token_name = (
                        line.split("return")[1]
                        .strip()
                        .replace("}", "")
                        .replace("{", "")
                        .strip()
                    )
                    lexer_rules.append(LexerRule(token_name, "", None))

    return lexer_rules


class Grammar:
    def __init__(self, terminals, non_terminals, rules):
        self.terminals = terminals
        self.non_terminals = non_terminals
        self.rules = rules
        self.nullables = self.compute_nullables()

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

    rule_lines = "".join([line.strip() for line in rule_lines]).split(";")

    for line in rule_lines:
        line = line.strip()
        if ":" in line:
            left, right = re.split(r"\s*:\s*", line.strip(), 1)
            non_terminals.add(left.strip())

    for line in rule_lines:
        line = line.strip()
        if ":" in line:
            left, right = re.split(r"\s*:\s*", line.strip(), 1)
            productions = re.split(r"\s*\|\s*", right.strip())
            if not productions or (len(productions) == 1 and not productions[0]):
                print(f"Error: regla sin producciones '{line}'")
                errors_found = True
            else:
                for production in productions:
                    rule = (left.strip(), production.split())
                    for symbol in rule[1]:
                        if symbol not in terminals and symbol not in non_terminals:
                            print(
                                f"Error: símbolo no definido '{symbol}' usado en la regla '{line}'"
                            )
                    rules.append(rule)
        elif line != "":
            print(f"Error: regla sin producciones '{line}'")

    return Grammar(terminals, non_terminals, rules)


class LR0Item:
    def __init__(self, left, right, lookahead):
        self.left = left
        self.right = tuple(right)
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
    queue = deque(items)
    while queue:
        item = queue.popleft()
        if (
            item.lookahead < len(item.right)
            and item.right[item.lookahead] in grammar.non_terminals
        ):
            non_terminal = item.right[item.lookahead]
            for rule in grammar.rules:
                if rule[0] == non_terminal:
                    new_item = LR0Item(rule[0], rule[1], 0)
                    if new_item not in closure_set:
                        closure_set.add(new_item)
                        queue.append(new_item)
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

    if symbol in grammar.terminals:
        first_set.add(symbol)
        return first_set

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


def visualize_lr0_graph(states, transitions, output_filename="lr1_graph.gv"):
    dot = Digraph("LR0", filename=output_filename, format="pdf")
    dot.attr(rankdir="LR", size="15,10")
    dot.attr(fontsize="14")
    dot.attr(ranksep="1")
    dot.attr(nodesep="1")

    for i, state in enumerate(states):
        state_label = f"State {i}\n"
        state_label += "\n".join(
            [
                f"{item}"
                for item in sorted(state, key=lambda x: (x.left, x.right, x.lookahead))
            ]
        )
        dot.node(str(i), label=state_label, shape="rectangle")

    for t in sorted(
        transitions, key=lambda x: (states.index(x[0]), x[1], states.index(x[2]))
    ):
        dot.edge(str(states.index(t[0])), str(states.index(t[2])), label=t[1])

    dot.view()


def slr_table(grammar, states, transitions):
    table = []
    for i, state in enumerate(states):
        action = {}
        goto = {}
        for item in state:
            if item.lookahead < len(item.right):
                symbol = item.right[item.lookahead]
                if symbol in grammar.terminals:
                    for t in transitions:
                        if t[0] == state and t[1] == symbol:
                            action[symbol] = ("S", states.index(t[2]))
                elif symbol in grammar.non_terminals:
                    for t in transitions:
                        if t[0] == state and t[1] == symbol:
                            goto[symbol] = states.index(t[2])
            else:
                if item.left == grammar.rules[0][0]:
                    action["$"] = ("ACC",)
                else:
                    for idx, rule in enumerate(grammar.rules):
                        if rule[0] == item.left and tuple(rule[1]) == item.right:
                            for symbol in follow_sets[item.left]:
                                if symbol in action and action[symbol][0] != "R":
                                    raise Exception(
                                        f"Error: conflicto en estado {i}, acción {action[symbol]}"
                                    )
                                if symbol != "":
                                    action[symbol] = ("R", idx)
        table.append((action, goto))
    return table


def visualize_slr_table(grammar, table):
    symbols = list(grammar.terminals) + ["$"] + list(grammar.non_terminals)
    col_widths = [max(len(sym), 3) for sym in symbols]

    header = (
        f"| {'State':^10} |"
        + " | ".join([f"{sym:^{col_widths[i]}}" for i, sym in enumerate(symbols)])
        + " |"
    )
    print(header)
    print("-" * len(header))

    for i, (action, goto) in enumerate(table):
        row = f"| {str(i):^10} |"

        for j, symbol in enumerate(symbols):
            if j < len(grammar.terminals) + 1 and symbol in action:
                act_str = action[symbol][0]
                if len(action[symbol]) > 1:
                    act_str += str(action[symbol][1])
                row += f" {act_str:^{col_widths[j]}} |"

            elif j >= len(grammar.terminals) + 1 and symbol in goto:
                row += f" {goto[symbol]:^{col_widths[j]}} |"

            else:
                row += " " * (col_widths[j] + 2) + "|"
        print(row)


def tokenize(file, rules):
    with open(file, "r") as f:
        content = f.read()

    position = 0
    tokens = []
    while position < len(content):
        match = None
        for token_expr in rules:
            pattern = token_expr.pattern
            tag = token_expr.name
            regex = re.compile(pattern)
            match = regex.match(content, position)
            if match:
                text = match.group(0)
                if tag == "PLUS" and text == "+":
                    # Tratar "PLUS" como un token de identificador
                    tag = "ID"
                if tag:
                    token = (text, tag)
                    tokens.append(token)
                break
        if not match:
            raise Exception(f"Carácter ilegal en la posición {position}")
        else:
            position = match.end()

    print("Tokens generados:")
    for token in tokens:
        print(token)

    return tokens


def slr_parse(grammar, table, input_string):
    stack = [0]
    position = 0
    tokens = input_string.split()  # Divide la cadena de entrada en tokens
    token_count = len(tokens)
    errors = []

    while stack:
        state = stack[-1]

        # Obtener el símbolo actual de entrada como un bloque (token)
        if position < token_count:
            token = tokens[position]
        else:
            token = ""

        if token not in table[state][0]:
            if token == "":
                errors.append("Error sintáctico: final inesperado de la entrada.")
                break
            else:
                errors.append(
                    f"Error sintáctico: token inesperado '{token}' en la entrada."
                )
                position += 1
                continue

        action = table[state][0].get(token)

        if action is None:
            errors.append(
                f"Error sintáctico: no se encontró una acción para el token '{token}' en el estado {state}."
            )
            position += 1
            continue

        if action[0] == "S":
            stack.append(action[1])
            position += 1
        elif action[0] == "R":
            rule = grammar.rules[action[1]]
            for _ in range(len(rule[1])):
                stack.pop()
            stack.append(table[stack[-1]][1][rule[0]])
            print(f"Reduce: {rule[0]} -> {' '.join(rule[1])}")
        elif action[0] == "ACC":
            print("Entrada aceptada.")
            break
        else:
            errors.append(
                f"Error sintáctico: acción no reconocida '{action}' en la tabla."
            )
            position += 1

    if errors:
        print("Errores sintácticos:")
        for error in errors:
            print(error)
    else:
        print("Análisis sintáctico completado sin errores.")

    return errors


if __name__ == "__main__":
    grammar = parse_yapar("LabE/slr-1.yalp")
    yalex_rules = parse_yalex("LabE/slr-1.yal")
    with open("LabE/entry.txt", "r") as f:
        tokens = f.read().split()

    yalex_tokens = {rule.name for rule in yalex_rules}
    yapar_tokens = grammar.terminals

    print("Tokens in YALex:")
    print(yalex_tokens)
    print("Tokens in YAPar:")
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
        exit()

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
    visualize_lr0_graph(states, transitions, "lr0_graph.gv")

    table = slr_table(grammar, states, transitions)
    visualize_slr_table(grammar, table)

    print(tokens)
    slr_parse(
        grammar, table, " ".join(tokens)
    )  # Unir los tokens en una cadena de texto para evaluarla como una entrada completa
