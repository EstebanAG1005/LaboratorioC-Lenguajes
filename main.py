import re
from graphviz import Digraph


class Token:
    def __init__(self, name, regex):
        self.name = name
        self.regex = regex


TOKENS = [
    Token("Identificador", r"\b[a-zA-Z_]\w*\b"),
    Token("Operador de suma", r"\+"),
    Token("Operador de resta", r"-"),
    Token("Operador de multiplicación", r"\*"),
    Token("Operador de asignación", r"="),
    Token("Número", r"\b\d+\b"),
]


def read_input_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
    return content


def generate_automaton():
    combined_regex = "|".join(
        "(?P<{}>{})".format(t.name.replace(" ", "_"), t.regex) for t in TOKENS
    )
    automaton = re.compile(combined_regex)
    return automaton


def analyze_input(automaton, input_str):
    tokens = []
    current_pos = 0
    line_number = 1
    column_number = 1

    while current_pos < len(input_str):
        match = automaton.match(input_str, current_pos)
        if match:
            token_type = match.lastgroup
            tokens.append((line_number, column_number, token_type))
            column_number += match.end() - match.start()
            current_pos = match.end()
        elif input_str[current_pos] == "\n":
            line_number += 1
            column_number = 1
            current_pos += 1
        elif input_str[current_pos].isspace():
            column_number += 1
            current_pos += 1
        else:
            print(
                f"Error léxico en la línea {line_number}, columna {column_number}: caracter no válido."
            )
            column_number += 1
            current_pos += 1

    return tokens


def analyze_file(input_file_path):
    input_str = read_input_file(input_file_path)
    automaton = generate_automaton()
    analysis_result = analyze_input(automaton, input_str)

    for line, column, token in analysis_result:
        print(f"{token.replace('_', ' ')} en línea {line}, columna {column}")


def main():
    # Especifica la ruta del archivo de entrada aquí
    # input_file_path = "yalex1.yal"
    input_file_path = "yalex2.yal"
    # input_file_path = "yalex3.yal"

    analyze_file(input_file_path)


if __name__ == "__main__":
    main()
