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

NOMBRE_CSV = 'preguntas.csv'
NOMBRE_TXT = 'preguntas.txt'
NOMBRE_JSON = 'preguntas.json'
LOG_FILE = 'log.txt'
SIMILARITY_THRESHOLD = 0.6

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
class ChatbotGUI:
    def __init__(self):
        self.base_preguntas = []
        self.file_name = None
        self.load_base_preguntas()

        self.root = tk.Tk()
        self.root.title("ChikiChiki Bot")
        self.root.geometry("600x500")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Frame para historial de chat
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.chat_area.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Frame para sugerencias
        self.suggestions_frame = tk.Frame(self.root)
        self.suggestions_frame.grid(row=1, column=0, sticky='ew', padx=5)
        self.suggestions_frame.grid_remove()  # ocultar inicialmente
        self.suggestions_frame.grid_columnconfigure((0,1,2), weight=1)

        # Frame para entrada de texto y botón
        input_frame = tk.Frame(self.root)
        input_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)
        self.entry = tk.Entry(input_frame)
        self.entry.grid(row=0, column=0, sticky='ew')
        send_btn = tk.Button(input_frame, text="Enviar", command=self.on_send)
        send_btn.grid(row=0, column=1, padx=(5,0))
        self.root.bind('<Return>', lambda event: self.on_send())
        self.entry.focus()

    def load_base_preguntas(self):
        if os.path.exists(NOMBRE_CSV):
            self.base_preguntas = leer_preguntas_csv(NOMBRE_CSV)
            self.file_name = NOMBRE_CSV
        elif os.path.exists(NOMBRE_TXT):
            self.base_preguntas = leer_preguntas_txt(NOMBRE_TXT)
            self.file_name = NOMBRE_TXT
        elif os.path.exists(NOMBRE_JSON):
            self.base_preguntas = leer_preguntas_json(NOMBRE_JSON)
            self.file_name = NOMBRE_JSON
        else:
            self.file_name = NOMBRE_CSV
            defaults = [
                ("¿Qué es un Gran Premio en Fórmula 1?", "Un Gran Premio es una carrera del campeonato deF1 que se celebra en diferentes países."),
                ("¿Qué significa pole position?", "La pole position es la primera posición de largada obtenida por el piloto más rápido en clasificación."),
                ("¿Cuántos puntos se otorgan al ganador de una carrera de F1?", "Al ganador se le otorgan 25 puntos en el campeonato.")
            ]
            with open(self.file_name, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['pregunta', 'respuesta'])
                writer.writerows(defaults)
            self.base_preguntas = defaults

    def on_send(self):
        user_q = self.entry.get().strip()
        if not user_q:
            return
        self.update_chat("Usuario", user_q)
        self.entry.delete(0, tk.END)

        if user_q.lower() in ["salir", "exit", "quit"]:
            self.update_chat("Bot", "¡Hasta luego!")
            self.root.destroy()
            return

        sugerencias = obtener_mejores_coincidencias(user_q, self.base_preguntas)
        mejor = sugerencias[0] if sugerencias else (None, None, 0)

        if mejor[2] >= SIMILARITY_THRESHOLD:
            respuesta = mejor[1]
            self.update_chat("Bot", f"{respuesta} (Similitud {int(mejor[2]*100)}%)")
            registrar_en_log(user_q, respuesta, mejor[2])
            self.clear_suggestions()
        else:
            self.update_chat("Bot", "No encontré una respuesta exacta.")
            registrar_en_log(user_q, "SIN RESPUESTA", 0.0)
            textos = [p for p, r, s in sugerencias]
            self.show_suggestions(textos, allow_add=True, original_q=user_q)

    def update_chat(self, speaker, text):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{speaker}: {text}\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def show_suggestions(self, suggestions, allow_add=False, original_q=None):
        """
        Muestra sugerencias y botón de agregar en el grid.
        """
        # Mostrar frame de sugerencias
        self.suggestions_frame.grid()
        # Limpiar contenido previo
        for w in self.suggestions_frame.winfo_children():
            w.destroy()
        # Label
        tk.Label(self.suggestions_frame, text="Sugerencias:", font=('Arial',10,'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
        # Botones de sugerencias (hasta 3)
        for i, s in enumerate(suggestions[:3]):
            btn = tk.Button(self.suggestions_frame, text=s, wraplength=180, command=lambda txt=s: self.on_suggestion_click(txt))
            btn.grid(row=1, column=i, padx=5, pady=2, sticky='ew')
        # Botón agregar respuesta
        if allow_add:
            btn_add = tk.Button(self.suggestions_frame, text="Agregar nueva respuesta", command=lambda: self.prompt_new_answer(original_q))
            btn_add.grid(row=2, column=0, columnspan=3, pady=5, sticky='ew')

    def clear_suggestions(self):
        self.suggestions_frame.grid_remove()

    def on_suggestion_click(self, suggestion):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, suggestion)
        self.on_send()

    def prompt_new_answer(self, question):
        answer = simpledialog.askstring("Agregar respuesta", f"Ingresa la respuesta para:\n'{question}'", parent=self.root)
        if answer:
            self.base_preguntas.append((question, answer))
            try:
                if self.file_name.endswith('.json'):
                    with open(self.file_name, 'w', encoding='utf-8') as f:
                        json.dump([{"pregunta": p, "respuesta": r} for p, r in self.base_preguntas], f, ensure_ascii=False, indent=4)
                elif self.file_name.endswith('.csv'):
                    with open(self.file_name, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=';')
                        writer.writerow([question, answer])
                elif self.file_name.endswith('.txt'):
                    with open(self.file_name, 'a', encoding='utf-8') as f:
                        f.write(f"{question}:{answer}\n")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la nueva respuesta: {e}")
                return
            self.update_chat("Bot", "¡Pregunta y respuesta agregadas!")
            registrar_en_log(question, "(Agregada por usuario)", 0.0)
            self.clear_suggestions()
        else:
            self.update_chat("Bot", "No se agregó ninguna respuesta.")

if __name__ == '__main__':
    app = ChatbotGUI()
    app.root.mainloop()
