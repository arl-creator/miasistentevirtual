import os
import openai
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from gtts import gTTS
import uuid
# from pydub import AudioSegment
import tempfile
import json
#import shutil
import random

# Configurar ffmpeg automáticamente si existe en el sistema
#AudioSegment.converter = shutil.which("ffmpeg")

# 1. CARGA DE CONFIGURACIÓN
load_dotenv()
openai.api_key = os.environ.get("DEEPSEEK_API_KEY")
openai.api_base = "https://api.deepseek.com/v1"

app = Flask(__name__)
os.makedirs("static/audio", exist_ok=True)

AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

USE_API = bool(openai.api_key)

# 2. TUS DATOS (Imágenes y Respuestas)
imagenes_fijas = {
    "vocales": ["/static/img/a.png", "/static/img/e.png", "/static/img/i.png", "/static/img/o.png", "/static/img/u.png"],
    "abecedario": ["/static/img/a.png", "/static/img/b.png", "/static/img/c.png", "/static/img/d.png", "/static/img/e.png", "/static/img/f.png", "/static/img/g.png", "/static/img/h.png", "/static/img/i.png", "/static/img/j.png", "/static/img/k.png", "/static/img/l.png", "/static/img/m.png", "/static/img/n.png", "/static/img/ñ.png", "/static/img/o.png", "/static/img/p.png", "/static/img/q.png", "/static/img/r.png", "/static/img/s.png", "/static/img/t.png", "/static/img/u.png", "/static/img/v.png", "/static/img/w.png", "/static/img/x.png", "/static/img/y.png", "/static/img/z.png"],
    "colores": ["/static/img/rojo.png", "/static/img/azul.png", "/static/img/verde.png", "/static/img/amarillo.png", "/static/img/naranja.png", "/static/img/morado.png"],
    "números": ["/static/img/1.png", "/static/img/2.png", "/static/img/3.png", "/static/img/4.png", "/static/img/5.png", "/static/img/6.png", "/static/img/7.png", "/static/img/8.png", "/static/img/9.png", "/static/img/10.png"],
    "animales": ["/static/img/perro.png", "/static/img/gato.png", "/static/img/elefante.png", "/static/img/leon.png", "/static/img/jirafa.png"],
    "frutas": ["/static/img/manzana.png", "/static/img/platano.png", "/static/img/uva.png", "/static/img/fresa.png", "/static/img/sandia.png"],
    "formas": ["/static/img/circulo.png", "/static/img/cuadrado.png", "/static/img/triangulo.png", "/static/img/rectangulo.png"]
}

respuestas_fijas = {
    "vocales": {"texto": "las vocales son A, E, I, O, U", "audio": "static/audio/vocales.mp3", "imagenes": imagenes_fijas["vocales"]},
    "abecedario": {"texto": "Hola, el abecedario es A, B, C, D, E, F, G, H, I, J, K, L, M, N, Ñ, O, P, Q, R, S, T, U, V, W, X, Y, Z", "audio": "static/audio/abecedario.mp3", "imagenes": imagenes_fijas["abecedario"]},
    "colores": {"texto": "Hola, los colores son rojo, azul, verde, amarillo, naranja, morado", "audio": "static/audio/colores.mp3", "imagenes": imagenes_fijas["colores"]},
    "números": {"texto": "Hola, los números son 1, 2, 3, 4, 5, 6, 7, 8, 9, 10", "audio": "static/audio/numeros.mp3", "imagenes": imagenes_fijas["números"]},
    "animales": {"texto": "Hola, los animales son perro, gato, elefante, león, jirafa", "audio": "static/audio/animales.mp3", "imagenes": imagenes_fijas["animales"]},
    "frutas": {"texto": "Hola, las frutas son manzana, plátano, uva, fresa, sandía", "audio": "static/audio/frutas.mp3", "imagenes": imagenes_fijas["frutas"]},
    "formas": {"texto": "Hola, las formas son círculo, cuadrado, triángulo, rectángulo", "audio": "static/audio/formas.mp3", "imagenes": imagenes_fijas["formas"]}
}

# 3. FUNCIONES DE APOYO
def generar_audios_pregrabados(): 
    for clave, datos in respuestas_fijas.items(): 
        ruta_audio = datos["audio"] 
        if not os.path.exists(ruta_audio): 
            print(f"Generando audio para: {clave}") 
            tts = gTTS(datos["texto"], lang="es") 
            os.makedirs(os.path.dirname(ruta_audio), exist_ok=True) 
            tts.save(ruta_audio)

def obtener_respuesta_deepseek(pregunta, system_prompt="Eres un asistente amigable.", temperature=0.7):
    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": pregunta}],
            temperature=temperature, max_tokens=100
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "Lo siento, tuve un problema. ¿Me repites?"

def generar_palabra_aleatoria(vocal):
    try:
        prompt = f"Dame una palabra infantil sencilla que empiece con la letra {vocal}. Responde SOLO la palabra."

        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Responde solo una palabra infantil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=20
        )

        palabra = response['choices'][0]['message']['content'].strip()
        palabra = palabra.replace('"', '').replace('.', '').split()[0]
        return palabra.capitalize()

    except Exception as e:
        print("⚠️ Error con API en palabra aleatoria, usando respaldo:", e)
        PALABRAS_RESPALDO = {
            "a": ["Abeja", "Avión", "Árbol", "Araña"],
            "e": ["Elefante", "Escuela", "Estrella", "Espejo"],
            "i": ["Iguana", "Isla", "Iglesia", "Imán"],
            "o": ["Oso", "Oveja", "Ola", "Ojo"],
            "u": ["Uva", "Unicornio", "Uniforme", "Uno"]
        }
        return random.choice(PALABRAS_RESPALDO.get(vocal.lower(), ["Abeja"]))

# 4. RUTAS (ENDPOINTS)
@app.route("/") 
def index(): 
    return render_template("index.html")

@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.json
    pregunta = data.get("pregunta", "").strip().lower()
    
    # Buscar en fijas
    for clave in respuestas_fijas:
        if clave in pregunta:
            d = respuestas_fijas[clave]
            # Crear audio "Ahora dilo tú"
            rep_name = f"rep_{uuid.uuid4()}.mp3"
            gTTS("Ahora dilo tú.", lang="es").save(os.path.join(AUDIO_DIR, rep_name))
            return jsonify({"respuesta": d["texto"], "audio_url": "/" + d["audio"], "repetir_url": f"/static/audio/{rep_name}", "imagenes": d["imagenes"]})

    # Si no es fija, usar IA
    res_texto = obtener_respuesta_deepseek(pregunta)
    res_name = f"{uuid.uuid4()}.mp3"
    gTTS(res_texto, lang="es").save(os.path.join(AUDIO_DIR, res_name))
    
    rep_name = f"rep_{uuid.uuid4()}.mp3"
    gTTS("Ahora dilo tú.", lang="es").save(os.path.join(AUDIO_DIR, rep_name))

    return jsonify({"respuesta": res_texto, "audio_url": f"/static/audio/{res_name}", "repetir_url": f"/static/audio/{rep_name}", "imagenes": []})

@app.route("/voz", methods=["POST"])
def voz():
    from pydub import AudioSegment
    import imageio_ffmpeg

    recognizer = sr.Recognizer()
    
    # Declaramos las variables al inicio para que el "finally" no falle
    input_path = None
    wav_path = None

    try:
        if "file" not in request.files:
            return jsonify({"texto": ""})

        file = request.files["file"]

        # Guardar archivo original
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_input:
            file.save(temp_input.name)
            input_path = temp_input.name

        # Configurar ffmpeg interno
        AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

        # Convertir a WAV
        audio = AudioSegment.from_file(input_path)
        wav_path = input_path + ".wav"
        audio.export(wav_path, format="wav")

        # Leer WAV con SpeechRecognition
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)

        texto = recognizer.recognize_google(audio_data, language="es-ES")
        print("Texto reconocido:", texto)

        return jsonify({"texto": texto})

    except sr.UnknownValueError:
        # Esto pasa cuando hay ruido pero no se entiende lo que dicen
        return jsonify({"texto": ""})

    except Exception as e:
        print("Error en voz:", repr(e))
        return jsonify({"texto": ""})
        
    finally:
        # 🔥 Limpieza segura sin errores de indentación
        try:
            if input_path and os.path.exists(input_path):
                os.remove(input_path)
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception as e:
            pass

@app.route("/validar", methods=["POST"])
def validar():
    from difflib import SequenceMatcher

    data = request.json
    intento = data.get("intento", "").lower().strip()
    correcta = data.get("respuesta", "").lower().strip()

    mensaje = ""
    correcto = False

    # 🔵 1️⃣ INTENTAR USAR API PRIMERO
    try:
        prompt = "Eres un foniatra para niños. Si el niño dijo algo parecido a la respuesta, responde solo 'Muy bien'. Si no, anímalo."

        res = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Correcta: {correcta}. Niño dijo: {intento}"}
            ],
            temperature=0.2
        )

        mensaje = res['choices'][0]['message']['content'].strip()
        correcto = "muy bien" in mensaje.lower()

        print("✅ Validación hecha con API")

    except Exception as e:
        print("⚠️ API falló, usando validación local:", e)

        # 🟢 2️⃣ SI FALLA LA API → VALIDACIÓN LOCAL

        # 🔸 CASO ESPECIAL VOCALes
        if "a, e, i, o, u" in correcta or "las vocales son" in correcta:
            intento_limpio = intento.replace(",", "").replace(".", "")
            letras_dichas = intento_limpio.split()

            vocales_correctas = ["a", "e", "i", "o", "u"]
            aciertos = sum(1 for v in vocales_correctas if v in letras_dichas)

            if aciertos >= 4:
                mensaje = "¡Muy bien! Dijiste las vocales."
                correcto = True
            else:
                mensaje = "Intenta decir A, E, I, O, U."
                correcto = False
        else:
            # 🔸 Validación normal por similitud
            similitud = SequenceMatcher(None, intento, correcta).ratio()

            if similitud > 0.6:
                mensaje = "¡Muy bien hecho!"
                correcto = True
            else:
                mensaje = "Casi lo logras, intenta otra vez."
                correcto = False

    # 🔊 Crear audio SIEMPRE
    audio_name = f"val_{uuid.uuid4()}.mp3"
    gTTS(mensaje, lang="es").save(os.path.join(AUDIO_DIR, audio_name))

    return jsonify({
        "mensaje": mensaje,
        "audio_url": f"/static/audio/{audio_name}",
        "correcto": correcto
    })
    
@app.route("/oracion_vocal", methods=["POST"])
def oracion_vocal():
    data = request.json
    vocal = data.get("vocal", "").lower()

    if vocal not in ["a", "e", "i", "o", "u"]:
        return jsonify({"error": "Vocal inválida"}), 400

    prompt = f"""
    Genera:
    1) Una palabra infantil sencilla que empiece con la letra {vocal}.
    2) Una oración corta y fácil para niños que incluya esa palabra.

    Responde SOLO en formato JSON así:
    {{
        "palabra_clave": "...",
        "oracion": "..."
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un maestro de preescolar creativo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.95,
            max_tokens=150
        )

        contenido = response['choices'][0]['message']['content'].strip()

        # Limpieza JSON
        if "```" in contenido:
            contenido = contenido.split("```")[1]
            contenido = contenido.replace("json", "").strip()

        resultado = json.loads(contenido)
        palabra = resultado["palabra_clave"].strip()
        oracion = resultado["oracion"].strip()

    except Exception as e:
        print("⚠️ Error con API en oración, usando respaldo:", e)

        PALABRAS_RESPALDO = {
            "a": ["Abeja", "Avión", "Árbol", "Araña"],
            "e": ["Elefante", "Escuela", "Estrella", "Espejo"],
            "i": ["Iguana", "Isla", "Iglesia", "Imán"],
            "o": ["Oso", "Oveja", "Ola", "Ojo"],
            "u": ["Uva", "Unicornio", "Uniforme", "Uno"]
        }

        ORACIONES_RESPALDO = {
            "a": ["La abeja vuela en el jardín.", "Ana ama a su gato."],
            "e": ["El elefante es grande.", "Elena estudia en la escuela."],
            "i": ["La iguana está en la isla.", "Isabel pinta un dibujo."],
            "o": ["El oso come miel.", "Oscar juega fútbol."],
            "u": ["La uva es dulce.", "La luna brilla en la noche."]
        }

        palabra = random.choice(PALABRAS_RESPALDO.get(vocal, ["Abeja"]))
        oracion = random.choice(ORACIONES_RESPALDO.get(vocal, ["La casa es bonita."]))

    # 🔊 Crear audio SIEMPRE (API o respaldo)
    nombre_audio = f"oracion_{uuid.uuid4()}.mp3"
    ruta_audio = os.path.join(AUDIO_DIR, nombre_audio)

    tts = gTTS(oracion, lang="es")
    tts.save(ruta_audio)

    return jsonify({
        "palabra_clave": palabra,
        "oracion": oracion,
        "audio_url": f"/static/audio/{nombre_audio}"
    })
        
@app.route("/palabras_vocales", methods=["GET"])
def palabras_vocales():
    vocales = ["a", "e", "i", "o", "u"]
    palabras = []

    for v in vocales:
        palabra = generar_palabra_aleatoria(v)
        palabras.append(palabra)

    return jsonify({"palabras": palabras})

@app.route("/tts", methods=["POST"])
def tts():
    data = request.json
    texto = data.get("texto", "")

    if not texto:
        return jsonify({"error": "Texto vacío"}), 400

    try:
        nombre_audio = f"tts_{uuid.uuid4()}.mp3"
        ruta_audio = os.path.join(AUDIO_DIR, nombre_audio)

        tts = gTTS(texto, lang="es")
        tts.save(ruta_audio)

        return jsonify({"audio_url": f"/static/audio/{nombre_audio}"})
    except Exception as e:
        print("Error TTS:", e)
        return jsonify({"error": "Error generando audio"}), 500

# 5. INICIO DE LA APP
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)






