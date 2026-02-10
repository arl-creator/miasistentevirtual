import os
import openai
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from gtts import gTTS
import uuid
from pydub import AudioSegment
import tempfile
import json

# 1. CARGA DE CONFIGURACIÓN
load_dotenv()
openai.api_key = os.environ.get("DEEPSEEK_API_KEY")
openai.api_base = "https://api.deepseek.com/v1"

app = Flask(__name__)

# Asegurar que la carpeta de audios exista
AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

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
            try:
                tts = gTTS(datos["texto"], lang="es") 
                tts.save(ruta_audio)
            except: pass

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
def reconocer_voz():
    recognizer = sr.Recognizer()
    if "file" not in request.files: 
        return jsonify({"error": "No file"}), 400
    
    audio_file = request.files["file"]
    # Detectamos la extensión real que envía el navegador
    extension = ".webm" if "webm" in audio_file.content_type else ".mp4"
    
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp_input:
        audio_file.save(tmp_input.name)
        tmp_wav = tmp_input.name.replace(extension, ".wav")
        try:
            # Forzamos la conversión a WAV para que Google lo entienda siempre
            audio_segment = AudioSegment.from_file(tmp_input.name)
            audio_segment.export(tmp_wav, format="wav")
            
            with sr.AudioFile(tmp_wav) as source:
                audio_data = recognizer.record(source)
                # Usamos un timeout para que no se quede colgado
                texto = recognizer.recognize_google(audio_data, language="es-ES")
                return jsonify({"texto": texto.strip()})
        except Exception as e:
            print(f"Error reconocimiento: {e}")
            return jsonify({"texto": ""}) # Si no entiende nada, devuelve vacío
        finally:
            if os.path.exists(tmp_input.name): os.remove(tmp_input.name)
            if os.path.exists(tmp_wav): os.remove(tmp_wav)

@app.route("/validar", methods=["POST"])
def validar():
    data = request.json
    intento = data.get("intento", "").lower()
    correcta = data.get("respuesta", "").lower()
    
    prompt_fonia = "Eres un foniatra. Si el niño dijo algo parecido a la respuesta, felicítalo con 'Muy bien'. Si no, anímalo."
    mensaje = obtener_respuesta_deepseek(f"Correcta: {correcta}. Niño dijo: {intento}", prompt_fonia, 0.4)
    
    audio_name = f"val_{uuid.uuid4()}.mp3"
    gTTS(mensaje, lang="es").save(os.path.join(AUDIO_DIR, audio_name))
    
    es_correcto = "muy bien" in mensaje.lower() or "perfecto" in mensaje.lower()
    return jsonify({"mensaje": mensaje, "audio_url": f"/static/audio/{audio_name}", "correcto": es_correcto, "avanzar": es_correcto})

@app.route("/ejercicios_frases")
def ejercicios_frases():
    sys = "Responde SOLO un JSON: {'palabras': ['pal1', 'pal2', 'pal3', 'pal4', 'pal5']}"
    res = obtener_respuesta_deepseek("5 palabras que empiecen con A, E, I, O, U", sys)
    try:
        if "```json" in res: res = res.split("```json")[1].split("```")[0].strip()
        return jsonify(json.loads(res))
    except:
        return jsonify({"palabras": ["Avión", "Elefante", "Isla", "Oso", "Uva"]})

@app.route("/oracion_vocal", methods=["POST"])
def oracion_vocal():
    vocal = request.json.get("vocal", "A")
    sys = "Responde SOLO JSON: {'oracion': '...', 'palabra_clave': '...'}"
    res = obtener_respuesta_deepseek(f"Oración corta con la vocal {vocal}", sys)
    try:
        if "```json" in res: res = res.split("```json")[1].split("```")[0].strip()
        return jsonify(json.loads(res))
    except:
        return jsonify({"oracion": f"El {vocal}migo es bueno.", "palabra_clave": "Amigo"})

# 5. INICIO DE LA APP
if __name__ == "__main__":
    generar_audios_pregrabados()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

