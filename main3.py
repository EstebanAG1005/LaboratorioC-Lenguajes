import re
import graphviz

# Función para leer un archivo y devolver su contenido como una cadena
def leer_archivo(nombre_archivo):
    with open(nombre_archivo, "r") as f:
        contenido = f.read()
    return contenido


# Función para obtener las definiciones regulares del archivo YALex
def obtener_definiciones_regulares(contenido):
    patron_definicion = r"let\s+(\w+)\s*=\s*\"(.+?)\""
    definiciones_regulares = {}
    for match in re.finditer(patron_definicion, contenido):
        nombre = match.group(1)
        expresion_regular = match.group(2)
        definiciones_regulares[nombre] = expresion_regular
    return definiciones_regulares


# Función para construir un diagrama de transición de estados a partir de una expresión regular
def construir_diagrama(expresion_regular):
    # Implementar aquí la construcción del diagrama de transición de estados
    # usando la teoría de autómatas finitos

    # El siguiente código muestra un ejemplo de cómo se puede construir el
    # diagrama usando la librería graphviz
    g = graphviz.Digraph(format="png")
    g.node("0", shape="circle")
    g.node("1", shape="doublecircle")
    g.edge("0", "1", label="a")
    g.render(filename="diagrama", directory="output", cleanup=True)
    return "output/diagrama.png"


# Función principal del programa
def generar_analizador_lexico(nombre_archivo):
    contenido = leer_archivo(nombre_archivo)
    definiciones_regulares = obtener_definiciones_regulares(contenido)
    for nombre, expresion_regular in definiciones_regulares.items():
        print(f"Definición regular: {nombre} = {expresion_regular}")
        diagrama = construir_diagrama(expresion_regular)
        print(f"Diagrama de transición de estados: {diagrama}")


# Ejemplo de uso
generar_analizador_lexico("yalex1.yal")
