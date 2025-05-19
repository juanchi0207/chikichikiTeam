import difflib
import json
import datetime
import unicodedata
import os
import csv
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer('spanish')

NOMBRE_CSV = 'preguntas.csv'
NOMBRE_TXT = 'preguntas.txt'
NOMBRE_JSON = 'preguntas.json'
LOG_FILE = 'log.txt'

# =========================================
# Funciones para leer archivos
# =========================================

def leer_preguntas_csv(nombre_archivo):
    """
    Objetivo: Leer preguntas y respuestas desde un archivo CSV separado por ';'.
    Parámetros de Entrada: nombre_archivo (str): Nombre del archivo CSV a leer.
    Parámetros de Salida: list: Lista de tuplas con pares (pregunta, respuesta).
    """
    preguntas_respuestas = []
    try:
        with open(nombre_archivo, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            try:
                first_row = next(reader)
            except StopIteration:
                return preguntas_respuestas
            if first_row and first_row[0].strip().lower() == 'pregunta':
                pass
            else:
                preguntas_respuestas.append((first_row[0], first_row[1]) if len(first_row) >= 2 else (first_row[0], ""))
            for row in reader:
                if not row:
                    continue
                pregunta = row[0].strip()
                respuesta = row[1].strip() if len(row) > 1 else ""
                preguntas_respuestas.append((pregunta, respuesta))
    except FileNotFoundError:
        return preguntas_respuestas
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
    return preguntas_respuestas

def leer_preguntas_txt(nombre_archivo):
    """
    Objetivo: Leer preguntas y respuestas desde un archivo de texto, cada línea con formato "pregunta:respuesta".
    Parámetros de Entrada: nombre_archivo (str): Nombre del archivo TXT a leer.
    Parámetros de Salida: list: Lista de tuplas con pares (pregunta, respuesta).
    """
    preguntas_respuestas = []
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as txtfile:
            for line in txtfile:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(':', 1)
                pregunta = parts[0].strip()
                respuesta = parts[1].strip() if len(parts) > 1 else ""
                preguntas_respuestas.append((pregunta, respuesta))
    except FileNotFoundError:
        return preguntas_respuestas
    except Exception as e:
        print(f"Error al leer el archivo de texto: {e}")
    return preguntas_respuestas

def leer_preguntas_json(nombre_archivo):
    """
    Objetivo: Leer preguntas y respuestas desde un archivo JSON con objetos que contienen "pregunta" y "respuesta".
    Parámetros de Entrada: nombre_archivo (str): Nombre del archivo JSON a leer.
    Parámetros de Salida: list: Lista de tuplas con pares (pregunta, respuesta).
    """
    preguntas_respuestas = []
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            if isinstance(data, list):
                for entrada in data:
                    pregunta = entrada.get("pregunta", "").strip()
                    respuesta = entrada.get("respuesta", "").strip()
                    preguntas_respuestas.append((pregunta, respuesta))
    except FileNotFoundError:
        return preguntas_respuestas
    except json.JSONDecodeError:
        print(f"Error: El archivo JSON '{nombre_archivo}' no es válido.")
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")
    return preguntas_respuestas

# =========================================
# Funciones de procesamiento y comparación
# =========================================

def normalizar_texto(texto):
    """
    Objetivo: Normalizar un texto eliminando acentos, puntuación, convirtiendo a minúsculas y aplicando stemización.
    Parámetros de Entrada: texto (str): Texto a normalizar.
    Parámetros de Salida: str: Texto normalizado con stemming.
    """
    texto = texto.lower()
    texto = ''.join(ch for ch in unicodedata.normalize('NFD', texto) if unicodedata.category(ch) != 'Mn')
    texto = texto.translate(str.maketrans('', '', '¿¡!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~'))
    palabras = texto.split()
    stems = [stemmer.stem(palabra) for palabra in palabras]
    return ' '.join(stems)

def calcular_similitud(pregunta1, pregunta2):
    """
    Objetivo: Calcular el puntaje de similitud entre dos preguntas usando difflib.
    Parámetros de Entrada: pregunta1 (str), pregunta2 (str): Preguntas a comparar.
    Parámetros de Salida: float: Puntaje de similitud entre 0 y 1.
    """
    norm1 = normalizar_texto(pregunta1)
    norm2 = normalizar_texto(pregunta2)
    return difflib.SequenceMatcher(None, norm1, norm2).ratio()

def obtener_mejores_coincidencias(pregunta_usuario, base_preguntas, n=3):
    """
    Objetivo: Obtener las n preguntas más similares de la base.
    Parámetros de Entrada: 
        pregunta_usuario (str): Pregunta ingresada por el usuario.
        base_preguntas (list): Lista de preguntas y respuestas.
        n (int): Cantidad de sugerencias a devolver.
    Parámetros de Salida: list: Lista de tuplas (pregunta, respuesta, similitud).
    """
    resultados = []
    for preg, resp in base_preguntas:
        sim = calcular_similitud(pregunta_usuario, preg)
        resultados.append((preg, resp, sim))
    resultados.sort(key=lambda x: x[2], reverse=True)
    return resultados[:n]

def registrar_en_log(pregunta, respuesta, similitud):
    """
    Objetivo: Registrar una interacción en el archivo log.txt.
    Parámetros de Entrada: 
        pregunta (str): Pregunta del usuario.
        respuesta (str): Respuesta entregada.
        similitud (float): Puntaje de similitud.
    Parámetros de Salida: None
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}\tPregunta: \"{pregunta}\"\tRespuesta: \"{respuesta}\"\tSimilitud: {similitud:.2f}\n")

# =========================================
# Main
# =========================================

file_name = None
base_preguntas = []

if os.path.exists(NOMBRE_CSV):
    base_preguntas = leer_preguntas_csv(NOMBRE_CSV)
    file_name = NOMBRE_CSV
elif os.path.exists(NOMBRE_TXT):
    base_preguntas = leer_preguntas_txt(NOMBRE_TXT)
    file_name = NOMBRE_TXT
elif os.path.exists(NOMBRE_JSON):
    base_preguntas = leer_preguntas_json(NOMBRE_JSON)
    file_name = NOMBRE_JSON
else:
    file_name = NOMBRE_JSON
    base_preguntas = []
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

print("Bienvenido al asistente. Escriba su pregunta o 'salir' para terminar.")

while True:
    entrada = input("Usuario: ").strip()
    if entrada.lower() == 'salir':
        print("Asistente: ¡Hasta luego!")
        break
    if not entrada:
        continue

    sugerencias = obtener_mejores_coincidencias(entrada, base_preguntas)
    mejor = sugerencias[0] if sugerencias else (None, None, 0)

    if mejor[2] >= 0.6:
        print(f"Asistente: (Similitud {int(mejor[2]*100)}%)")
        print(f"Asistente: {mejor[1]}")
        registrar_en_log(entrada, mejor[1], mejor[2])
    else:
        print("Asistente: No encontré una respuesta exacta.")
        if sugerencias:
            print("Asistente: ¿Quizás quiso decir:")
            for i, (preg, _, sim) in enumerate(sugerencias, 1):
                print(f"  {i}. {preg} (similitud: {int(sim*100)}%)")
        registrar_en_log(entrada, "SIN RESPUESTA", 0.0)
        op = input("¿Desea agregar esta pregunta y su respuesta? (s/n): ").strip().lower()
        if op == 's':
            nueva_resp = input("Ingrese la respuesta: ").strip()
            if nueva_resp:
                base_preguntas.append((entrada, nueva_resp))
                if file_name.endswith('.json'):
                    with open(file_name, 'w', encoding='utf-8') as f:
                        json.dump([{"pregunta": p, "respuesta": r} for p, r in base_preguntas], f, ensure_ascii=False, indent=4)
                elif file_name.endswith('.csv'):
                    with open(file_name, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=';')
                        writer.writerow([entrada, nueva_resp])
                elif file_name.endswith('.txt'):
                    with open(file_name, 'a', encoding='utf-8') as f:
                        f.write(f"{entrada}:{nueva_resp}\n")
                print("Asistente: ¡Pregunta y respuesta agregadas!")
                registrar_en_log(entrada, "(Agregada por usuario)", 0.0)
            else:
                print("Asistente: Respuesta vacía. No se agregó nada.")