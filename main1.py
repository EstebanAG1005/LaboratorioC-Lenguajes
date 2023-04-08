import re
import numpy as np
from copy import deepcopy
import time
import networkx as nx
import matplotlib.pyplot as plt
from graphviz import Digraph

# stack para hacer las acciones del postfix
class Stack:
    def __init__(self):
        self.items = []

    def empty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items) - 1]

    def size(self):
        return len(self.items)


# Clase para regresar los diferentes errores del ingreso de REGEX
class InvalidRegexException(Exception):
    pass

    def __init__(self, message):
        super().__init__(message)


# Se reescribe de la expresión para poder ser evaluada y convertida en PostFix
def reescribiendoExpr(regex):
    try:
        if re.search(r"\s", regex):
            raise InvalidRegexException(
                "La expresión regular no puede contener espacios."
            )
        regex = regex.replace("ϵ", " ")
        # ignore non-valid characters
        regex = re.sub(r"[^a-zA-Z0-9()|+*?]", "", regex)
        # add dot for concatenation
        newExpr = regex[0]
        for i in range(1, len(regex)):
            if (
                ((regex[i].isalpha() or regex[i].isdigit()) and regex[i - 1] != "(")
                or regex[i] == "("
            ) and (regex[i - 1] != "|" and regex[i - 1] != "(" and regex[i - 1] != "."):
                newExpr += "." + regex[i]
            else:
                newExpr += regex[i]
        print("Reescribiendo la expresion regular: " + newExpr)
        # Compila la expresión y muestra la expresión
        re.compile(newExpr)
        return newExpr
    except re.error as e:
        # ... (rest of the code)
        error_msg = str(e)
        if "nothing to repeat" in error_msg:
            raise InvalidRegexException(
                "La expresión regular contiene un operador que se repite cero veces."
            ) from e
        elif "unbalanced parenthesis" in error_msg:
            raise InvalidRegexException(
                "La expresión regular contiene paréntesis desbalanceados."
            ) from e
        else:
            raise InvalidRegexException(
                "La expresión regular ingresada no es válida."
            ) from e


# Funcion para convertir a postfix
def topostfix(regex):
    # definir jerarquia de simbolos
    jerar = {}
    jerar["+"] = 4
    jerar["*"] = 4
    jerar["?"] = 4
    jerar["|"] = 3
    jerar["."] = 2
    jerar["("] = 1
    lista = list(regex)
    output = []

    stack = Stack()

    for item in lista:
        if item.isalpha() or item.isdigit() or item == " ":
            output.append(item)
        elif item == "(":
            stack.push(item)
        elif item == ")":
            top = stack.pop()
            while top != "(":
                output.append(top)
                top = stack.pop()
        else:
            while (not stack.empty()) and (jerar[stack.peek()] >= jerar[item]):
                output.append(stack.pop())
            stack.push(item)
    while not stack.empty():
        output.append(stack.pop())

    return "".join(output)


# AFN
class AFN:
    def __init__(self):
        self.estadoInicial = None
        self.estados = set()
        self.estadoFinal = None
        self.transiciones = []
        self.accept_states = set()

    def basic(self, input):
        self.estadoInicial = 0
        self.estadoFinal = 1
        self.estados.add(self.estadoInicial)
        self.estados.add(self.estadoFinal)
        transition = {
            "desde": self.estadoInicial,
            "=>": input,
            "hacia": [self.estadoFinal],
        }
        self.transiciones.append(transition)
        return self

    def display(self):
        object = {
            "estados": self.estados,
            "Estado Inicial": self.estadoInicial,
            "Estado Final": self.estadoFinal,
            "transiciones": self.transiciones,
        }
        print("estados:", self.estados)
        print("Estado Inicial: ", self.estadoInicial)
        print("Estado Final:", self.estadoFinal)
        print("transiciones:", self.transiciones)
        return object


def to_graphviz_vertical(nfa):
    dot = Digraph()
    dot.node(
        "", style="invisible", shape="none"
    )  # Add an empty invisible node at the start
    for state in nfa.estados:
        if state == nfa.estadoInicial:
            dot.edge("", str(state), label="start")
        elif state == nfa.estadoFinal:
            dot.node(str(state), str(state), shape="doublecircle")
        else:
            dot.node(str(state), str(state))
    for transition in nfa.transiciones:
        for hacia in transition["hacia"]:
            if transition["=>"] == " ":
                dot.edge(str(transition["desde"]), str(hacia), label="ε")
            else:
                dot.edge(str(transition["desde"]), str(hacia), label=transition["=>"])
    return dot


def to_graphviz_horizontal(afn):
    dot = Digraph()
    dot.format = "pdf"  # Cambiar el formato a PDF

    dot.attr(rankdir="LR", size="8,5")
    dot.attr("node", shape="doublecircle")
    for (
        accept_state
    ) in afn.accept_states:  # Marcar estados de aceptación con doble círculo
        dot.node(str(accept_state))

    dot.attr("node", shape="circle")
    dot.node("start", "", width="0.1", height="0.1")
    dot.edge("start", str(afn.estadoInicial), label="")

    for transicion in afn.transiciones:
        for hacia in transicion["hacia"]:
            if transicion["=>"] == " ":
                label = "ε"
            else:
                label = transicion["=>"]
            dot.edge(str(transicion["desde"]), str(hacia), label=label)

    return dot


def concat(nfa1, nfa2):
    afn = AFN()
    # work on nfa2
    maximum = max(nfa1.estados)
    for i in range(0, len(nfa2.transiciones)):
        nfa2.transiciones[i]["desde"] += maximum
        nfa2.transiciones[i]["hacia"] = list(
            np.add(maximum, nfa2.transiciones[i]["hacia"])
        )
    # work on self
    newStates = np.add(maximum, np.array(list(nfa2.estados)))
    newStates = set(set(newStates).union(nfa1.estados))
    afn.estados = newStates
    afn.estadoInicial = nfa1.estadoInicial
    afn.estadoFinal = nfa2.estadoFinal + maximum
    for transition in nfa1.transiciones:
        afn.transiciones.append(transition)
    for transition in nfa2.transiciones:
        if transition["=>"] == " ":
            # avoid adding ε transitions to the initial state of the second NFA
            if transition["desde"] != nfa2.estadoInicial:
                afn.transiciones.append(transition)
        else:
            afn.transiciones.append(transition)
    return afn


def union(nfa1, nfa2):
    afn = AFN()
    # trabaja el AFN1
    newStates1 = np.add(np.array(list(nfa1.estados)), 1)
    maximum = max(newStates1)
    nfa1.estadoInicial += 1
    nfa1.estadoFinal += 1
    for i in range(0, len(nfa1.transiciones)):
        nfa1.transiciones[i]["desde"] += 1
        nfa1.transiciones[i]["hacia"] = list(np.add(1, nfa1.transiciones[i]["hacia"]))
    # trabaja el AFN2
    nfa2.estadoInicial += maximum + 1
    nfa2.estadoFinal += maximum + 1
    newStates2 = np.add(np.array(list(nfa2.estados)), maximum + 1)
    for i in range(0, len(nfa2.transiciones)):
        nfa2.transiciones[i]["desde"] += maximum + 1
        nfa2.transiciones[i]["hacia"] = list(
            np.add(maximum + 1, nfa2.transiciones[i]["hacia"])
        )
    # trabaja el self
    afn.estadoInicial = 0
    afn.estadoFinal = nfa2.estadoFinal + 1
    afn.estados.add(afn.estadoInicial)
    for state in newStates1:
        afn.estados.add(state)
    for state in newStates2:
        afn.estados.add(state)
    afn.estados.add(afn.estadoFinal)

    initialTransition = {
        "desde": afn.estadoInicial,
        "=>": " ",
        "hacia": [nfa1.estadoInicial, nfa2.estadoInicial],
    }
    finalTransition1 = {
        "desde": nfa1.estadoFinal,
        "=>": " ",
        "hacia": [afn.estadoFinal],
    }
    finalTransition2 = {
        "desde": nfa2.estadoFinal,
        "=>": " ",
        "hacia": [afn.estadoFinal],
    }
    afn.transiciones.append(initialTransition)
    for transition in nfa1.transiciones:
        afn.transiciones.append(transition)
    for transition in nfa2.transiciones:
        afn.transiciones.append(transition)
    afn.transiciones.append(finalTransition1)
    afn.transiciones.append(finalTransition2)
    return afn


def kleene(afn):
    nfaMain = AFN()
    # Make a deep copy of the original NFA
    nfaCopy = deepcopy(afn)
    # Increment all states by 1 to avoid conflicts with nfaMain
    nfaCopy.estados = set([s + 1 for s in nfaCopy.estados])
    nfaCopy.estadoInicial += 1
    nfaCopy.estadoFinal += 1
    for transicion in nfaCopy.transiciones:
        transicion["desde"] += 1
        transicion["hacia"] = [s + 1 for s in transicion["hacia"]]
    # Set up the new NFA
    nfaMain.estadoInicial = 0
    nfaMain.estadoFinal = nfaCopy.estadoFinal + 1
    nfaMain.estados = set(
        [nfaMain.estadoInicial, nfaMain.estadoFinal] + list(nfaCopy.estados)
    )
    initialTransition = {
        "desde": nfaMain.estadoInicial,
        "=>": " ",
        "hacia": [nfaCopy.estadoInicial, nfaMain.estadoFinal],
    }
    finalTransition1 = {
        "desde": nfaCopy.estadoFinal,
        "=>": " ",
        "hacia": [nfaCopy.estadoInicial, nfaMain.estadoFinal],
    }
    for state in nfaCopy.accept_states:
        finalTransition1["hacia"].append(state + 1)
        transition = {
            "desde": state,
            "=>": " ",
            "hacia": [nfaCopy.estadoInicial, nfaMain.estadoFinal],
        }
        nfaCopy.transiciones.append(transition)
    nfaMain.transiciones.append(initialTransition)
    for transition in nfaCopy.transiciones:
        nfaMain.transiciones.append(transition)
    nfaMain.transiciones.append(finalTransition1)
    return nfaMain


def plus(afn):
    nfa1 = deepcopy(afn)
    nfa2 = deepcopy(afn)
    star = AFN()
    star = kleene(nfa2)
    result = AFN()
    result = concat(nfa1, star)
    return result


def conditional(afn):
    # a? = (a|epsilon)
    nfa1 = deepcopy(afn)
    epsilon = AFN()
    epsilon = epsilon.basic(" ")
    result = AFN()
    result = union(nfa1, epsilon)
    return result


def evaluatePostfix(regex):
    if len(regex) == 1:
        afn = AFN()
        afn = afn.basic(regex)
        return afn
    stack = Stack()
    for token in regex:
        if token.isalnum() or token == " ":
            afn = AFN()
            afn = afn.basic(token)
            stack.push(afn)
        else:
            if token == "*":
                afn = stack.pop()
                result = kleene(afn)
                print("*")
                result.display()
                # If the kleene result is the only element in the stack,
                # return it directly to avoid adding extra nodes
                if stack.empty():
                    return result
                stack.push(result)
            elif token == ".":
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                result = concat(nfa1, nfa2)
                print(".")
                result.display()
                stack.push(result)
            elif token == "|":
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                result = union(nfa1, nfa2)
                print("|")
                result.display()
                stack.push(result)
            elif token == "?":
                afn = stack.pop()
                result = conditional(afn)
                print("?")
                result.display()
                # Add the epsilon transition from the initial state to the final state
                epsilon_transition = {
                    "desde": result.estadoInicial,
                    "=>": " ",
                    "hacia": [result.estadoFinal],
                }
                result.transiciones.append(epsilon_transition)
                stack.push(result)
            elif token == "+":
                afn = stack.pop()
                result = plus(afn)
                print("+")
                result.display()
                stack.push(result)
    afn = AFN()
    afn = stack.pop()
    # print (afn)
    with open("resultadoAFN.txt", "w") as f:
        for state in afn.estados:
            f.write(str(state) + ", ")
        f.write("\n")
        # for loop language
        lang = []
        for i in range(0, len(afn.transiciones)):
            lang.append(str(afn.transiciones[i]["=>"]))
        lang = set(lang)
        f.write(str(lang))
        print(lang)
        f.write("\n")
        f.write(str(afn.estadoInicial))
        f.write("\n")
        f.write(str(afn.estadoFinal))
        f.write("\n")
        for transition in afn.transiciones:
            f.write(str(transition) + ", ")
    # to_graphviz_vertical(afn).render("nfa.gv", view=True)
    return afn


def generate_mega_automata(automatas):
    mega_afn = AFN()
    mega_afn.estadoInicial = 0
    mega_afn.estados.add(mega_afn.estadoInicial)

    current_max_state = 0

    for idx, afn in enumerate(automatas):
        current_max_state += 1
        for state in afn.estados:
            mega_afn.estados.add(state + current_max_state)

        for transition in afn.transiciones:
            new_transition = {
                "desde": transition["desde"] + current_max_state,
                "=>": transition["=>"],
                "hacia": [hacia + current_max_state for hacia in transition["hacia"]],
            }
            mega_afn.transiciones.append(new_transition)

        epsilon_transition = {
            "desde": mega_afn.estadoInicial,
            "=>": " ",
            "hacia": [afn.estadoInicial + current_max_state],
        }
        mega_afn.transiciones.append(epsilon_transition)

        # Añadir estados de aceptación del autómata actual al mega autómata
        for accept_state in afn.accept_states:
            mega_afn.accept_states.add(accept_state + current_max_state)

        # Imprimir estados de aceptación del autómata actual
        print(
            f"Estados de aceptación del autómata {idx + 1}: {[state + current_max_state for state in afn.accept_states]}"
        )

        current_max_state = max(mega_afn.estados)

    # Imprimir estados de aceptación del mega autómata
    print(f"Estados de aceptación del mega autómata: {mega_afn.accept_states}")

    return mega_afn


graph_counter = 0

# Ejecutar Todo
def ejecutar(regex):
    global graph_counter
    print("\nExpresion regular ingresada: " + regex)
    regexprocess = reescribiendoExpr(regex)
    postfix = topostfix(regexprocess)
    print("Postfix: " + postfix)
    afn = evaluatePostfix(postfix)
    afn.accept_states.add(afn.estadoFinal)  # Añadir esta línea
    to_graphviz_horizontal(afn).render("nfa{}.gv".format(graph_counter), view=True)
    graph_counter += 1
    return afn


def read_yalex_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    rules = []
    for line in content.split("\n"):
        if line.startswith("let"):
            _, expr_name, regex = line.split(" ", 2)
            rules.append((expr_name, regex))
    return rules


def convert_yalex_regex(yalex_regex):
    converted_regex = yalex_regex.replace("=", "").replace('"', "")
    return converted_regex.strip()


import re


def convertir_lex(archivo):
    # Abrir el archivo y leer todas las líneas
    with open(archivo, "r") as f:
        lineas = f.readlines()

    # Lista para almacenar los tokens
    tokens = []

    # Expresión regular para extraer el nombre y la expresión regular de cada token
    token_regex = r'let\s+([a-zA-Z0-9]+)\s+=\s+"(.*)"'

    # Leer cada línea y almacenar los tokens
    for n_linea, linea in enumerate(lineas, start=1):
        match = re.match(token_regex, linea.strip())
        if match:

            nombre = match.group(1)
            valor = match.group(2)
            # Verificar que no haya parentesis mal cerrados
            if valor.count("(") != valor.count(")"):
                raise Exception(
                    f"Error en línea {n_linea}: hay un número desigual de paréntesis en la definición de {nombre}."
                )
            # Verificar que no haya llaves mal cerradas
            if valor.count("{") != valor.count("}"):
                raise Exception(
                    f"Error en línea {n_linea}: hay un número desigual de llaves en la definición de {nombre}."
                )
            # Verificar que no haya corchetes mal cerrados
            if valor.count("[") != valor.count("]"):
                raise Exception(
                    f"Error en línea {n_linea}: hay un número desigual de corchetes en la definición de {nombre}."
                )
            # Verificar que no haya comillas mal cerradas
            if valor.count('"') % 2 != 0:
                raise Exception(
                    f"Error en línea {n_linea}: hay un número impar de comillas en la definición de {nombre}."
                )
            # Verificar que solo haya caracteres válidos
            if any(c in "@#$%" for c in valor):
                raise Exception(
                    f"Error en línea {n_linea}: la definición de {nombre} contiene caracteres inválidos."
                )
            tokens.append((nombre, valor))
            # Verificar que el valor de cada token no esté vacío
            for n_linea, (nombre, valor) in enumerate(tokens, start=1):
                if valor == "":
                    raise Exception(
                        f"Error en línea {n_linea}: el valor del token {nombre} está vacío."
                    )

    # Actualizar las definiciones en cada valor
    for i, (nombre, valor) in enumerate(tokens):
        for j, (def_nombre, def_valor) in enumerate(tokens):
            valor = valor.replace(def_nombre, "(" + def_valor + ")")
            tokens[i] = (nombre, valor)

    # Escribir las definiciones actualizadas en un nuevo archivo
    archivo_actualizado = "yalex_actualizado.lex"
    with open(archivo_actualizado, "w") as f:
        for nombre, valor in tokens:
            definicion_actualizada = f'let {nombre} = "{valor}"\n'
            f.write(definicion_actualizada)

    # Imprimir las definiciones actualizadas en la consola
    for nombre, valor in tokens:
        definicion_actualizada = f"{nombre} = {valor}"
        print(definicion_actualizada)


automatas = []
# Leemos el archivo .yal y extraemos las reglas
convertir_lex = convertir_lex("yalex3.lex")
rules = read_yalex_file("yalex_actualizado.lex")
print(rules)
mega_automaton = None
for expr_name, yalex_regex in rules:
    print(f"Procesando expresión: {expr_name} -> {yalex_regex}")

    # Convertimos la expresión regular de YALex a una expresión regular compatible
    regex = convert_yalex_regex(yalex_regex)

    print(f"Expresión regular convertida: {regex}")

    # Creamos un AFN para la expresión regular
    afn = ejecutar(regex)

    # Añadir el autómata actual a la lista de autómatas
    automatas.append(afn)

# Mostramos el "mega autómata"
print("\nMega Autómata:")
# Generar el Mega Autómata y visualizarlo
mega_automaton = generate_mega_automata(automatas)
to_graphviz_horizontal(mega_automaton).render("mega_automaton.gv", view=True)
