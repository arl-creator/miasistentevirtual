import os
import openai
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from gtts import gTTS
import uuid
from pydub import AudioSegment
import tempfile
#import difflib
import json


# Cargar API Key
load_dotenv()
openai.api_key = os.environ.get("DEEPSEEK_API_KEY")
#openai.api_key = os.getenv("DEEPSEEK_API_KEY")
#print("DEEPSEEK_API_KEY:", os.getenv("DEEPSEEK_API_KEY"))

openai.api_base = "https://api.deepseek.com/v1"


app = Flask(__name__)
os.makedirs("static/audio", exist_ok=True)

# URLs de imágenes para cada categoría (debes poner esas imágenes en static/img/)
imagenes_fijas = {
    "vocales": [
        "/static/img/a.png",
        "/static/img/e.png",
        "/static/img/i.png",
        "/static/img/o.png",
        "/static/img/u.png"
    ],
    "abecedario": [
        "/static/img/a.png",
        "/static/img/b.png",
        "/static/img/c.png",
        "/static/img/d.png",
        "/static/img/e.png",
        "/static/img/f.png",
        "/static/img/g.png",
        "/static/img/h.png",
        "/static/img/i.png",
        "/static/img/j.png",
        "/static/img/k.png",
        "/static/img/l.png",
        "/static/img/m.png",
        "/static/img/n.png",
        "/static/img/ñ.png",
        "/static/img/o.png",
        "/static/img/p.png",
        "/static/img/q.png",
        "/static/img/r.png",
        "/static/img/s.png",
        "/static/img/t.png",
        "/static/img/u.png",
        "/static/img/v.png",
        "/static/img/w.png",
        "/static/img/x.png",
        "/static/img/y.png",
        "/static/img/z.png"
    ],
    "colores": [
        "/static/img/rojo.png",
        "/static/img/azul.png",
        "/static/img/verde.png",
        "/static/img/amarillo.png",
        "/static/img/naranja.png",
        "/static/img/morado.png"
    ],
    "números": [
        "/static/img/1.png",
        "/static/img/2.png",
        "/static/img/3.png",
        "/static/img/4.png",
        "/static/img/5.png",
        "/static/img/6.png",
        "/static/img/7.png",
        "/static/img/8.png",
        "/static/img/9.png",
        "/static/img/10.png"
    ],
    "animales": [
        "/static/img/perro.png",
        "/static/img/gato.png",
        "/static/img/elefante.png",
        "/static/img/leon.png",
        "/static/img/jirafa.png"
    ],
    "frutas": [
        "/static/img/manzana.png",
        "/static/img/platano.png",
        "/static/img/uva.png",
        "/static/img/fresa.png",
        "/static/img/sandia.png"
    ],
    "formas": [
        "/static/img/circulo.png",
        "/static/img/cuadrado.png",
        "/static/img/triangulo.png",
        "/static/img/rectangulo.png"
    ]
}

# Textos y audios pre-generados para cada categoría
respuestas_fijas = {
    "vocales": {
        "texto": "las vocales son A, E, I, O, U",
        "audio": "static/audio/vocales.mp3",
        "imagenes": imagenes_fijas["vocales"]
    },
    "abecedario": {
        "texto": "Hola, el abecedario es A, B, C, D, E, F, G, H, I, J, K, L, M, N, Ñ, O, P, Q, R, S, T, U, V, W, X, Y, Z",
        "audio": "static/audio/abecedario.mp3",
        "imagenes": imagenes_fijas["abecedario"]
    },
    "colores": {
        "texto": "Hola, los colores son rojo, azul, verde, amarillo, naranja, morado",
        "audio": "static/audio/colores.mp3",
        "imagenes": imagenes_fijas["colores"]
    },
    "números": {
        "texto": "Hola, los números son 1, 2, 3, 4, 5, 6, 7, 8, 9, 10",
        "audio": "static/audio/numeros.mp3",
        "imagenes": imagenes_fijas["números"]
    },
    "animales": {
        "texto": "Hola, los animales son perro, gato, elefante, león, jirafa",
        "audio": "static/audio/animales.mp3",
        "imagenes": imagenes_fijas["animales"]
    },
    "frutas": {
        "texto": "Hola, las frutas son manzana, plátano, uva, fresa, sandía",
        "audio": "static/audio/frutas.mp3",
        "imagenes": imagenes_fijas["frutas"]
    },
    "formas": {
        "texto": "Hola, las formas son círculo, cuadrado, triángulo, rectángulo",
        "audio": "static/audio/formas.mp3",
        "imagenes": imagenes_fijas["formas"]
    }
}

# Generar audios pregrabados si no existen 
def generar_audios_pregrabados(): 
    for clave, datos in respuestas_fijas.items(): 
        ruta_audio = datos["audio"] 
        if not os.path.exists(ruta_audio): 
            print(f"Generando audio para: {clave}") 
            tts = gTTS(datos["texto"], lang="es") 
            os.makedirs(os.path.dirname(ruta_audio), exist_ok=True) 
            tts.save(ruta_audio)
            
@app.route("/") 
def index(): 
    return render_template("index.html")


# --- FUNCIONES CENTRALES ---

def obtener_respuesta_deepseek(pregunta, system_prompt="Eres un asistente amigable y educativo para niños. Responde de forma breve clara y alegre.", temperature=0.7):
    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pregunta}
            ],
            temperature=temperature,
            max_tokens=100
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error en DeepSeek: {e}")
        return "Lo siento, hubo un problema al obtener la respuesta."


@app.route("/tts", methods=["POST"])
def generar_tts():
    data = request.get_json()
    texto = data.get("texto", "")

    if not texto:
        return jsonify({"error": "No se recibió texto"}), 400

    try:
        filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join("static", "audio", filename)

        tts = gTTS(text=texto, lang="es")
        tts.save(audio_path)

        return jsonify({
            "audio_url": f"/static/audio/{filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- ENDPOINTS DE OPERACIÓN ---

@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.json
    pregunta = data.get("pregunta", "").strip().lower()
    if not pregunta:
        return jsonify({"error": "No se recibió una pregunta válida"}), 400
        
    # Búsqueda de respuestas fijas
    for clave in respuestas_fijas.keys():
        if clave in pregunta:
            respuesta = respuestas_fijas[clave]["texto"]
            audio_url = "/" + respuestas_fijas[clave]["audio"]
            repetir_texto = "Ahora dilo tú."
            repetir_filename = f"{uuid.uuid4()}.mp3"
            repetir_path = os.path.join("static", "audio", repetir_filename)
            tts2 = gTTS(repetir_texto, lang="es")
            tts2.save(repetir_path)
            return jsonify({
                "respuesta": respuesta,
                "audio_url": audio_url,
                "repetir_url": f"/static/audio/{repetir_filename}",
                "imagenes": respuestas_fijas[clave]["imagenes"]
            })

    # Respuesta con API
    respuesta = obtener_respuesta_deepseek(pregunta)
    #audio_filename = f"{uuid.uuid4()}.mp3"
    #audio_path = "/tmp/audio_respuesta.mp3"
    #tts = gTTS(respuesta, lang="es")
    #tts.save(audio_path)
    audio_filename = f"{uuid.uuid4()}.mp3"
    audio_path = os.path.join("static", "audio", audio_filename)
    tts = gTTS(respuesta, lang="es")
    tts.save(audio_path)

    repetir_texto = "Ahora dilo tú."
    repetir_filename = f"{uuid.uuid4()}.mp3"
    repetir_path = os.path.join("static", "audio", repetir_filename)
    tts2 = gTTS(repetir_texto, lang="es")
    tts2.save(repetir_path)

    return jsonify({
        "respuesta": respuesta,
        "audio_url": f"/static/audio/{audio_filename}",
        "repetir_url": f"/static/audio/{repetir_filename}",
        "imagenes": []
    })


@app.route("/voz", methods=["POST"])
def reconocer_voz():
    print("FILES:", request.files)
    print("CONTENT TYPE:", request.content_type)

    recognizer = sr.Recognizer()

    # ✅ Validar que venga archivo
    if "file" not in request.files:
        return jsonify({"error": "No se recibió archivo de audio"}), 400

    audio_file = request.files["file"]
    audio_content = audio_file.read()

    if not audio_content:
        return jsonify({"error": "Audio vacío"}), 400

    content_type = audio_file.content_type or ""

    # Detectar formato
    if "webm" in content_type:
        extension = ".webm"
        audio_format = "webm"
    else:
        extension = ".mp4"   # Safari / Android
        audio_format = "mp4"

    input_path = tempfile.NamedTemporaryFile(delete=False, suffix=extension).name
    wav_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

    try:
        # Guardar audio original
        with open(input_path, "wb") as f:
            f.write(audio_content)

        # Convertir a WAV (ffmpeg)
        AudioSegment.from_file(input_path, format=audio_format).export(
            wav_path, format="wav"
        )

        # Reconocimiento
        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.record(source)

        try:
            texto = recognizer.recognize_google(audio, language="es-ES").strip()
        except sr.UnknownValueError:
            return jsonify({"texto": ""})
        except sr.RequestError:
            return jsonify({"error": "Servicio de reconocimiento no disponible"}), 500

        return jsonify({"texto": texto})

    except Exception as e:
        return jsonify({"error": f"No se pudo procesar la voz: {str(e)}"}), 400

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)




@app.route("/validar", methods=["POST"])
def validar():
    data = request.json
    respuesta_correcta = data.get("respuesta", "").lower()
    intento_nino = data.get("intento", "").lower()

    if not respuesta_correcta or not intento_nino:
        return jsonify({
            "mensaje": "Intenta otra vez",
            "correcto": False
        })

    system_prompt = (
        "Eres un foniatra experto y motivador para niños pequeños. "
        "Si el intento es correcto, felicita brevemente. "
        "NO uses las frases: 'eres un campeón', 'campeón', 'excelente campeón', "
        "'increíble', ni sinónimos similares. "
        "Usa únicamente frases simples como: "
        "'Muy bien, lo hiciste perfecto.' o 'Muy bien'. "
        "Si no es correcto, anima a intentarlo otra vez."
    )

    user_prompt = (
        f"Respuesta correcta: {respuesta_correcta}\n"
        f"Intento del niño: {intento_nino}"
    )

    mensaje = obtener_respuesta_deepseek(
        user_prompt,
        system_prompt=system_prompt,
        temperature=0.4
    )

    correcto = "muy bien" in mensaje.lower() or "perfecto" in mensaje.lower()

    # 🔊 AQUÍ HACEMOS QUE HABLE
    audio_name = f"{uuid.uuid4()}.mp3"
    audio_path = os.path.join("static", "audio", audio_name)
    gTTS(mensaje, lang="es").save(audio_path)

    return jsonify({
        "mensaje": mensaje,
        "audio_url": f"/static/audio/{audio_name}",
        "correcto": correcto,
        "mostrar_boton_repetir": True,
        "avanzar": correcto
    })

# --- ENDPOINT PARA EJERCICIOS DE FONÉTICA ---

@app.route("/ejercicios_frases")
def ejercicios_frases():
    system_prompt = (
        "Eres un experto en fonética y educación infantil. Tu ÚNICO trabajo es responder con un objeto JSON. "
        "No incluyas explicaciones, encabezados de Markdown ni texto adicional. Las palabras deben ser sencillas y aptas para niños (ej. 'uña', 'oso', 'isla')."
    )
    
    user_prompt = (
        "Genera una lista de 5 palabras en español, donde la primera palabra empiece con 'A', la segunda con 'E', la tercera con 'I', "
        "la cuarta con 'O', y la quinta con 'U'. El formato de salida debe ser exactamente: "
        "{'palabras': ['Palabra_A', 'Palabra_E', 'Palabra_I', 'Palabra_O', 'Palabra_U']}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        contenido = response['choices'][0]['message']['content'].strip()

        if contenido.startswith("```json"):
            contenido = contenido.lstrip("```json").rstrip("```").strip()
            
        import json
        resultado = json.loads(contenido)
        
        if 'palabras' in resultado and isinstance(resultado['palabras'], list) and len(resultado['palabras']) == 5:
            return jsonify({"palabras": resultado['palabras']})
        else:
            raise ValueError(f"El JSON de la IA no contiene una lista de 5 'palabras'. Respuesta: {contenido[:50]}...")
            
    except Exception as e:
        return jsonify({"error": f"Error al generar palabras: {str(e)}"}), 500


@app.route("/oracion_vocal", methods=["POST"])
def oracion_vocal():
    data = request.json
    vocal = data.get("vocal", "").upper()
    if vocal not in ["A","E","I","O","U"]:
        return jsonify({"error": "Vocal no válida"}), 400

    system_prompt = (
        "Eres un experto en educación infantil. Tu ÚNICO trabajo es responder con un objeto JSON. "
        "No incluyas explicaciones, encabezados de Markdown ni texto adicional."
    )
    
    user_prompt = (
        f"Genera una oración corta y sencilla para un niño que contenga la letra '{vocal}'. "
        f"Indica claramente cuál es la palabra que empieza con esa letra. "
        "El formato de salida debe ser exactamente: {'oracion': 'Tu oración aquí.', 'palabra_clave': 'Tu palabra clave aquí.'}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=50
        )
        contenido = response['choices'][0]['message']['content'].strip()
        
        if contenido.startswith("```json"):
            contenido = contenido.lstrip("```json").rstrip("```").strip()
        
        import json
        resultado = json.loads(contenido)
        return jsonify(resultado)
        
    except json.JSONDecodeError as e:
        error_msg = f"Error de formato JSON: La IA devolvió texto inválido. Texto: {contenido}"
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500 


if __name__ == "__main__":
    # Primero genera los audios una sola vez
    # generar_audios_pregrabados() 
    
    # Render asigna un puerto automáticamente en la variable PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)




















