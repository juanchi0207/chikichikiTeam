import csv, difflib, unicodedata, json, os

def normalize_text(text):
 """
    Objetivo: Normalizar un texto eliminando acentos y convirtiendo todos los caracteres a minúsculas.
    Parámetros de Entrada: text (str): Texto a normalizar.
    Parámetros de Salida: str: Texto normalizado sin acentos y en minúsculas.
"""
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return normalized.casefold()  # convertir a minúsculas

def leer_preguntas_csv(nombre_archivo):

"""
    Objetivo: Leer preguntas y respuestas desde un archivo CSV separado por ';'.
    Parámetros de Entrada:nombre_archivo (str): Nombre del archivo CSV a leer.
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
    Objetivo:Leer preguntas y respuestas desde un archivo de texto, cada línea con formato "pregunta:respuesta".
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
    Objetivo:Leer preguntas y respuestas desde un archivo JSON con objetos que contienen "pregunta" y "respuesta".
    Parámetros de Entrada:nombre_archivo (str): Nombre del archivo JSON a leer.
    Parámetros de Salida:list: Lista de tuplas con pares (pregunta, respuesta).
 """
    preguntas_respuestas = []
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            if isinstance(data, list):
                for entrada in data:
                    if isinstance(entrada, dict):
                        pregunta = entrada.get("pregunta", "")
                        respuesta = entrada.get("respuesta", "")
                        if isinstance(pregunta, str):
                            pregunta = pregunta.strip()
                        else:
                            pregunta = str(pregunta)
                        if isinstance(respuesta, str):
                            respuesta = respuesta.strip()
                        else:
                            respuesta = str(respuesta)
                        preguntas_respuestas.append((pregunta, respuesta))
    except FileNotFoundError:
        return preguntas_respuestas
    except json.JSONDecodeError:
        print(f"Error: El archivo JSON '{nombre_archivo}' no es válido (posiblemente esté malformado o vacío).")
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")
    return preguntas_respuestas

def encontrar_mejor_respuesta(pregunta_usuario, base_preguntas):

"""
    Objetivo: Encontrar la respuesta más similar a la pregunta del usuario usando coincidencia difusa.
    Parámetros de Entrada:
        pregunta_usuario (str): Pregunta realizada por el usuario.
        base_preguntas (list): Lista de tuplas con pares (pregunta, respuesta).
    Parámetros de Salida:
         str or None: La mejor respuesta encontrada o None si no se encontró coincidencia suficiente.
 """
    pregunta_norm = normalize_text(pregunta_usuario)
    preguntas_norm = [normalize_text(p) for p, _ in base_preguntas]
    coincidencias = difflib.get_close_matches(pregunta_norm, preguntas_norm, n=1, cutoff=0.6)
    if coincidencias:
        mejor_coincidencia = coincidencias[0]
        idx = preguntas_norm.index(mejor_coincidencia)
        return base_preguntas[idx][1]
    else:
        return None

def agregar_pregunta_respuesta(nueva_pregunta, nueva_respuesta, nombre_archivo, base_preguntas):
 """
    Objetivo: Agregar una nueva pregunta y su respuesta al archivo correspondiente (CSV, TXT o JSON) y a la base en memoria.
    Parámetros de Entrada:
        nueva_pregunta (str): Pregunta que se desea agregar.
        nueva_respuesta (str): Respuesta asociada a la pregunta.
        nombre_archivo (str): Nombre del archivo donde se almacenará.
        base_preguntas (list): Lista actual de preguntas/respuestas en memoria.
    Parámetros de Salida:
        bool: True si se agregó correctamente, False en caso contrario.
 """
    try:
        if nombre_archivo.endswith('.csv'):
            with open(nombre_archivo, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow([nueva_pregunta, nueva_respuesta])
        elif nombre_archivo.endswith('.txt'):
            with open(nombre_archivo, 'a', encoding='utf-8') as txtfile:
                txtfile.write(f"{nueva_pregunta}:{nueva_respuesta}\n")
        elif nombre_archivo.endswith('.json'):
            data = [ {"pregunta": p, "respuesta": r} for (p, r) in base_preguntas ]
            data.append({"pregunta": nueva_pregunta, "respuesta": nueva_respuesta})
            with open(nombre_archivo, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        else:
            print(f"Formato de archivo no soportado: {nombre_archivo}")
            return False
        base_preguntas.append((nueva_pregunta, nueva_respuesta))
        return True
    except Exception as e:
        print(f"Error al escribir en el archivo {nombre_archivo}: {e}")
        return False

def main():
    NOMBRE_CSV = 'preguntas.csv'
    NOMBRE_TXT = 'preguntas.txt'
    NOMBRE_JSON = 'preguntas.json'

    base_preguntas = []
    file_name = None
    file_found = False

    if os.path.exists(NOMBRE_CSV):
        base_preguntas = leer_preguntas_csv(NOMBRE_CSV)
        file_name = NOMBRE_CSV
        file_found = True
    elif os.path.exists(NOMBRE_TXT):
        base_preguntas = leer_preguntas_txt(NOMBRE_TXT)
        file_name = NOMBRE_TXT
        file_found = True
    elif os.path.exists(NOMBRE_JSON):
        base_preguntas = leer_preguntas_json(NOMBRE_JSON)
        file_name = NOMBRE_JSON
        file_found = True
    else:
        file_name = NOMBRE_CSV
        base_preguntas = []

    if not base_preguntas:
        ejemplos = [
            ("¿Qué es un Gran Premio en Fórmula 1?", "Un Gran Premio es una carrera que forma parte del calendario de la temporada de Fórmula 1, celebrada en circuitos específicos alrededor del mundo."),
            ("¿Qué es la pole position?", "La pole position es la primera plaza de salida en la parrilla, obtenida por el piloto que marca el mejor tiempo en la sesión de clasificación."),
            ("¿Cómo se asignan los puntos en un Gran Premio de Fórmula 1?", "Se otorgan puntos a los diez primeros clasificados: 25 al ganador, 18 al segundo, 15 al tercero, luego 12, 10, 8, 6, 4, 2 y 1 punto del cuarto al décimo."),
        ]
        if file_name.endswith('.csv'):
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(['pregunta', 'respuesta'])  
                writer.writerows(ejemplos)
        elif file_name.endswith('.txt'):
            with open(file_name, 'w', encoding='utf-8') as txtfile:
                for pregunta, respuesta in ejemplos:
                    txtfile.write(f"{pregunta}:{respuesta}\n")
        elif file_name.endswith('.json'):
            data = [ {"pregunta": p, "respuesta": r} for (p, r) in ejemplos ]
            with open(file_name, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        base_preguntas = ejemplos
        if file_found:
            print(f"El archivo '{file_name}' estaba vacío. Se han añadido preguntas de ejemplo.")
        else:
            print(f"Se ha creado el archivo '{file_name}' con preguntas de ejemplo.")

    print("** Chatbot de Preguntas sobre Fórmula 1 **")
    print("Escribe tu pregunta (o 'salir' para terminar):")

   
    while True:
        pregunta_usuario = input("> ").strip()
        if not pregunta_usuario:
            continue  
        if pregunta_usuario.lower() in ["salir", "exit", "quit"]:
            print("¡Hasta luego!")
            break

        respuesta = encontrar_mejor_respuesta(pregunta_usuario, base_preguntas)
        if respuesta:
            print(f"Bot: {respuesta}")
        else:
            print("Bot: Lo siento, no tengo una respuesta para esa pregunta.")
            agregar = input("¿Deseas agregar esta pregunta y respuesta al bot? (s/n): ").strip().lower()
            if agregar in ("s", "si", "sí"):
                nueva_resp = input("Por favor, ingresa la respuesta para esta pregunta: ").strip()
                if nueva_resp:
                    exito = agregar_pregunta_respuesta(pregunta_usuario, nueva_resp, file_name, base_preguntas)
                    if exito:
                        print("Bot: ¡Nueva pregunta y respuesta agregadas con éxito!")
                    else:
                        print("Bot: Hubo un error al guardar la nueva pregunta.")
                else:
                    print("Bot: No se agregó la pregunta porque la respuesta estaba vacía.")
            else:
                print("Bot: Entendido. Pregúntame otra cosa cuando quieras.")
if __name__ == "__main__":
    main()
