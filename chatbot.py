import difflib
import json
import datetime
import unicodedata
import os
import csv
from nltk.stem.snowball import SnowballStemmer
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

# =========================================
# Configuración y constantes
# =========================================
stemmer = SnowballStemmer('spanish')

# Archivos de datos ubicados en el mismo directorio que este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOMBRE_CSV = os.path.join(BASE_DIR, 'preguntas.csv')
NOMBRE_TXT = os.path.join(BASE_DIR, 'preguntas.txt')
NOMBRE_JSON = os.path.join(BASE_DIR, 'preguntas.json')
LOG_FILE = os.path.join(BASE_DIR, 'log.txt')
SIMILARITY_THRESHOLD = 0.7

# =========================================
# Funciones originales de lectura y procesamiento
# =========================================

def leer_preguntas_csv(nombre_archivo):
    """
    Objetivo: Leer preguntas y respuestas desde un archivo CSV separado por ';'.
    Parámetros de Entrada: nombre_archivo (str): Nombre del archivo CSV a leer.
    Parámetros de Salida: list: Lista de tuplas con pares (pregunta, respuesta).
    """
    preguntas_respuestas = []
    try:
        with open(nombre_archivo, newline='', encoding='utf-8-sig') as csvfile:
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
        with open(nombre_archivo, 'r', encoding='utf-8-sig') as txtfile:
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
        with open(nombre_archivo, 'r', encoding='utf-8-sig') as jsonfile:
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
# Interfaz gráfica con Tkinter
# =========================================
global base_preguntas, file_name, root, chat_area, suggestions_frame, entry
base_preguntas = []
file_name = None


# =========================================

def load_base_preguntas():
    """
    Carga la base de preguntas desde el archivo CSV, JSON o TXT.
    Si no se encuentra ninguno, crea un archivo CSV por defecto.
    Parámetros de Entrada: None
    Parámetros de Salida: None
    """
    global base_preguntas, file_name
    if os.path.exists(NOMBRE_CSV):
        base_preguntas = leer_preguntas_csv(NOMBRE_CSV)
        file_name = NOMBRE_CSV
    elif os.path.exists(NOMBRE_JSON):
        base_preguntas = leer_preguntas_json(NOMBRE_JSON)
        file_name = NOMBRE_JSON
    elif os.path.exists(NOMBRE_TXT):
        base_preguntas = leer_preguntas_txt(NOMBRE_TXT)
        file_name = NOMBRE_TXT
    else:
        file_name = NOMBRE_CSV
        defaults = [
            ("¿Qué es un Gran Premio en Fórmula 1?", "Un Gran Premio es una carrera del campeonato de F1 que se celebra en diferentes países."),
            ("¿Qué significa pole position?", "La pole position es la primera posición de largada obtenida por el piloto más rápido en clasificación."),
            ("¿Cuántos puntos se otorgan al ganador de una carrera de F1?", "Al ganador se le otorgan 25 puntos en el campeonato.")
        ]
        with open(file_name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['pregunta', 'respuesta'])
            writer.writerows(defaults)
        base_preguntas = defaults

def update_chat(speaker, text):
    """
    Actualiza el área de chat con el texto proporcionado.
    Parámetros de Entrada:
        speaker (str): Nombre del hablante (Usuario o Bot).
        text (str): Texto a mostrar en el área de chat.
        Parámetros de Salida: None
    """
    chat_area.config(state='normal')
    chat_area.insert(tk.END, f"{speaker}: {text}\n")
    chat_area.see(tk.END)
    chat_area.config(state='disabled')

def show_suggestions(suggestions, allow_add=False, original_q=None):
    """
    Muestra un marco de sugerencias con botones para cada sugerencia.
    Parámetros de Entrada: 
        suggestions (list): Lista de sugerencias a mostrar.
        allow_add (bool): Si se permite agregar una nueva respuesta.
        original_q (str): Pregunta original para la cual se muestran las sugerencias.
        Parámetros de Salida: None
    """
    suggestions_frame.grid()
    for w in suggestions_frame.winfo_children():
        w.destroy()
    tk.Label(suggestions_frame, text="Sugerencias:", font=('Arial',10,'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
    for i, s in enumerate(suggestions[:3]):
        btn = tk.Button(suggestions_frame, text=s, wraplength=180,
                        command=lambda txt=s: on_suggestion_click(txt))
        btn.grid(row=1, column=i, padx=5, pady=2, sticky='ew')
    if allow_add:
        btn_add = tk.Button(suggestions_frame, text="Agregar nueva respuesta",
                            command=lambda: prompt_new_answer(original_q))
        btn_add.grid(row=2, column=0, columnspan=3, pady=5, sticky='ew')

def clear_suggestions():
    """
    Oculta el marco de sugerencias.
    Parámetros de Entrada: None
    Parámetros de Salida: None
    """
    suggestions_frame.grid_remove()

def on_suggestion_click(suggestion):
    """
    Maneja el clic en una sugerencia, completando el campo de entrada con la sugerencia seleccionada.
    Parámetros de Entrada: suggestion (str): Sugerencia seleccionada.
    Parámetros de Salida: None
    """
    entry.delete(0, tk.END)
    entry.insert(0, suggestion)
    on_send()

def prompt_new_answer(question):
    """
    Muestra un cuadro de diálogo para agregar una nueva respuesta a una pregunta.
    Parámetros de Entrada: question (str): Pregunta para la cual se desea agregar una respuesta.
    Parámetros de Salida: None
    """
    answer = simpledialog.askstring("Agregar respuesta", f"Ingresa la respuesta para:\n'{question}'", parent=root)
    if not answer:
        update_chat("Bot", "No se agregó ninguna respuesta.")
        return
    base_preguntas.append((question, answer))
    try:
        if file_name.endswith('.json'):
            with open(file_name, 'w', encoding='utf-8-sig') as f:
                json.dump([{"pregunta": p, "respuesta": r} for p, r in base_preguntas], f, ensure_ascii=False, indent=4)
        elif file_name.endswith('.csv'):
            with open(file_name, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow([question, answer])
        else:
            with open(file_name, 'a', encoding='utf-8-sig') as f:
                f.write(f"{question}:{answer}\n")
        update_chat("Bot", "¡Pregunta y respuesta agregadas!")
        registrar_en_log(question, "(Agregada por usuario)", 0.0)
        clear_suggestions()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar la nueva respuesta: {e}")

def on_send(event=None):
    """
    Maneja el evento de enviar un mensaje.
    Parámetros de Entrada: event (tk.Event): Evento de teclado (opcional).
    Parámetros de Salida: None
    """
    user_q = entry.get().strip()
    if not user_q:
        return
    update_chat("Usuario", user_q)
    entry.delete(0, tk.END)
    if user_q.lower() in ["salir", "exit", "quit"]:
        update_chat("Bot", "¡Hasta luego!")
        root.destroy()
        return
    sugerencias = obtener_mejores_coincidencias(user_q, base_preguntas)
    mejor = sugerencias[0] if sugerencias else (None, None, 0)
    if mejor[2] >= SIMILARITY_THRESHOLD:
        respuesta = mejor[1]
        update_chat("Bot", f"{respuesta} (Similitud {int(mejor[2]*100)}%)")
        registrar_en_log(user_q, respuesta, mejor[2])
        clear_suggestions()
    else:
        update_chat("Bot", "No encontré una respuesta exacta.")
        registrar_en_log(user_q, "SIN RESPUESTA", 0.0)
        textos = [p for p, r, s in sugerencias]
        show_suggestions(textos, allow_add=True, original_q=user_q)

def setup_gui():
    """
    Configura la interfaz gráfica de usuario.
    """
    global root, chat_area, suggestions_frame, entry
    root = tk.Tk()
    root.title("ChikiChiki Bot")
    root.geometry("600x500")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled')
    chat_area.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

    suggestions_frame = tk.Frame(root)
    suggestions_frame.grid(row=1, column=0, sticky='ew', padx=5)
    suggestions_frame.grid_remove()
    suggestions_frame.grid_columnconfigure((0,1,2), weight=1)

    input_frame = tk.Frame(root)
    input_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
    input_frame.grid_columnconfigure(0, weight=1)
    entry = tk.Entry(input_frame)
    entry.grid(row=0, column=0, sticky='ew')
    send_btn = tk.Button(input_frame, text="Enviar", command=on_send)
    send_btn.grid(row=0, column=1, padx=(5,0))
    root.bind('<Return>', on_send)
    entry.focus()

    update_chat("Bot", "¡Hola! Soy ChikiChiki Bot de F1. ¿En qué puedo ayudarte hoy?")
    root.mainloop()

if __name__ == '__main__':
    load_base_preguntas()
    setup_gui()
    
