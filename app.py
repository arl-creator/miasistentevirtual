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
os.makedirs("static/audio", exist_ok=True)

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

from pydub import AudioSegment
import tempfile
import os
// Función para iniciar grabación
function iniciarGrabacionIntento() {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        mediaRecorderIntento = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        audioChunksIntento = [];
        mediaRecorderIntento.addEventListener("dataavailable", e => audioChunksIntento.push(e.data));
        mediaRecorderIntento.addEventListener("stop", procesarGrabacionIntento);
        mediaRecorderIntento.start();
        mensajeValidacion.innerText = "🎙️ Grabando tu repetición... ¡Suelta el botón cuando termines!";
    }).catch(() => { mensajeValidacion.innerText = "❌ No se pudo acceder al micrófono."; });
}

// Función para detener grabación
function detenerGrabacionIntento() {
    if (mediaRecorderIntento && mediaRecorderIntento.state === "recording") {
        mediaRecorderIntento.stop();
    }
}

// Escuchar tanto mouse como touch
btnGrabarIntento.addEventListener("mousedown", iniciarGrabacionIntento);
btnGrabarIntento.addEventListener("mouseup", detenerGrabacionIntento);
btnGrabarIntento.addEventListener("touchstart", iniciarGrabacionIntento);
btnGrabarIntento.addEventListener("touchend", detenerGrabacionIntento);

function procesarGrabacionIntento() {
    if (audioChunksIntento.length === 0) return;
    const blob = new Blob(audioChunksIntento, { type: "audio/webm" });
    audioChunksIntento = [];
    const formData = new FormData();
    formData.append("file", blob, "intento.webm");
    mensajeValidacion.innerText = "⏳ Procesando tu repetición, espera un momento...";
    btnGrabarIntento.style.display = "none";

    fetch("/voz", { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {
            const respuestaCorrecta = btnGrabarIntento.dataset.respuesta || btnGrabarIntento.dataset.oracion || "";
            if (data.texto) validarIntento(respuestaCorrecta, data.texto);
            else {
                mensajeValidacion.innerText = "❌ No pude entender lo que dijiste.";
                btnGrabarIntento.style.display = "block";
            }
        })
        .catch(() => {
            mensajeValidacion.innerText = "❌ Hubo un error al procesar tu repetición.";
            btnGrabarIntento.style.display = "block";
        });
}

@app.route("/voz", methods=["POST"])
def voz():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No se recibió audio"})

        audio_file = request.files["file"]

        import tempfile
        from pydub import AudioSegment
        import speech_recognition as sr
        import os

        # Crear archivo temporal WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            # Convertir cualquier formato (webm, mp4, m4a, etc) a WAV
            audio = AudioSegment.from_file(audio_file)
            audio.export(temp_wav_path, format="wav")
        except Exception as e:
            print("Error convirtiendo audio:", e)
            return jsonify({"error": "Error procesando el audio"})

        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(temp_wav_path) as source:
                audio_data = recognizer.record(source)
                texto = recognizer.recognize_google(audio_data, language="es-MX")
        except sr.UnknownValueError:
            print("No se entendió el audio")
            return jsonify({"error": "No se entendió el audio"})
        except Exception as e:
            print("Error reconocimiento:", e)
            return jsonify({"error": "Error al reconocer el audio"})
        finally:
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

        print("Texto reconocido:", texto)
        return jsonify({"texto": texto})

    except Exception as e:
        print("Error general:", e)
        return jsonify({"error": "Ocurrió un error"})


@app.route("/validar", methods=["POST"])
def validar():
    data = request.json
    intento = data.get("intento", "").lower()
    correcta = data.get("respuesta", "").lower()
    
    prompt = "Eres un foniatra para niños. Si el niño dijo algo parecido a la respuesta, responde 'Muy bien'. Si no, anímalo."
    try:
        res = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"Correcta: {correcta}. Niño dijo: {intento}"}],
            temperature=0.3
        )
        mensaje = res['choices'][0]['message']['content'].strip()
    except:
        mensaje = "¡Muy bien hecho!"

    audio_name = f"val_{uuid.uuid4()}.mp3"
    gTTS(mensaje, lang="es").save(os.path.join("static/audio", audio_name))
    
    # Lógica de éxito para el frontend
    exito = any(palabra in mensaje.lower() for palabra in ["muy bien", "perfecto", "excelente", "correcto"])
    return jsonify({"mensaje": mensaje, "audio_url": f"/static/audio/{audio_name}", "correcto": exito})
    
# nuevoooooooo

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

        # 🔥 Limpieza por si DeepSeek responde con ```json
        if "```" in contenido:
            contenido = contenido.split("```")[1]
            contenido = contenido.replace("json", "").strip()

        resultado = json.loads(contenido)

        palabra = resultado["palabra_clave"].strip()
        oracion = resultado["oracion"].strip()

        # 🎵 Crear audio automáticamente
        nombre_audio = f"oracion_{uuid.uuid4()}.mp3"
        ruta_audio = os.path.join(AUDIO_DIR, nombre_audio)

        tts = gTTS(oracion, lang="es")
        tts.save(ruta_audio)

        return jsonify({
            "palabra_clave": palabra,
            "oracion": oracion,
            "audio_url": f"/static/audio/{nombre_audio}"
        })

    except Exception as e:
        print("Error generando oración:", e)

        return jsonify({
            "palabra_clave": "Abeja",
            "oracion": "La abeja vuela en el jardín.",
            "audio_url": ""
        })
        

@app.route("/palabras_vocales", methods=["GET"])
def palabras_vocales():
    vocales = ["a", "e", "i", "o", "u"]
    palabras = []

    for vocal in vocales:
        palabra = generar_palabra_aleatoria(vocal)  # tu función IA
        palabras.append(palabra)

    return jsonify({"palabras": palabras})
    
def generar_palabra_aleatoria(vocal):
    prompt = f"""
    Dame una palabra infantil sencilla que empiece con la letra {vocal}.
    Responde SOLO la palabra.
    """

    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",  # 👈 sigues usando DeepSeek
            messages=[
                {"role": "system", "content": "Responde solo una palabra infantil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=20
        )

        palabra = response['choices'][0]['message']['content'].strip()

        # limpieza por si responde algo extra
        palabra = palabra.replace('"', '').replace('.', '').split()[0]

        return palabra.capitalize()

    except Exception as e:
        print("Error generando palabra:", e)

        # respaldo si falla DeepSeek
        ejemplos = {
            "a": "Abeja",
            "e": "Elefante",
            "i": "Isla",
            "o": "Oso",
            "u": "Uva"
        }

        return ejemplos.get(vocal.lower(), "Abeja")

        
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






















