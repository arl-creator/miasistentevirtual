import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from gtts import gTTS
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

AUDIO_DIR = "/tmp"  # Render SOLO permite escribir aquí

# ----------------------------
# HOME
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------
# SPEECH TO TEXT (WHISPER)
# ----------------------------
@app.route("/voz", methods=["POST"])
def voz():
    if "file" not in request.files:
        return jsonify({"error": "No se recibió audio"})

    audio_file = request.files["file"]
    filename = f"{uuid.uuid4()}.webm"
    path = os.path.join(AUDIO_DIR, filename)
    audio_file.save(path)

    try:
        with open(path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                file=f,
                model="whisper-1",
                language="es"
            )
        return jsonify({"texto": transcript.text})
    except Exception as e:
        return jsonify({"error": str(e)})

# ----------------------------
# TEXTO A VOZ (gTTS)
# ----------------------------
@app.route("/tts", methods=["POST"])
def tts():
    texto = request.json.get("texto", "")
    if not texto:
        return jsonify({"error": "Texto vacío"})

    filename = f"{uuid.uuid4()}.mp3"
    path = os.path.join(AUDIO_DIR, filename)

    tts = gTTS(text=texto, lang="es")
    tts.save(path)

    return jsonify({"audio_url": f"/audio/{filename}"})

@app.route("/audio/<filename>")
def audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

# ----------------------------
# CHAT
# ----------------------------
@app.route("/preguntar", methods=["POST"])
def preguntar():
    pregunta = request.json.get("pregunta", "")

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente educativo para niños pequeños."},
            {"role": "user", "content": pregunta}
        ]
    )

    respuesta = completion.choices[0].message.content

    return jsonify({
        "respuesta": respuesta,
        "imagenes": [],
        "audio_url": generar_audio(respuesta),
        "repetir_url": generar_audio("Ahora repite lo que escuchaste")
    })

def generar_audio(texto):
    filename = f"{uuid.uuid4()}.mp3"
    path = os.path.join(AUDIO_DIR, filename)
    gTTS(text=texto, lang="es").save(path)
    return f"/audio/{filename}"

# ----------------------------
# VALIDACIÓN
# ----------------------------
@app.route("/validar", methods=["POST"])
def validar():
    correcta = request.json.get("respuesta", "").lower()
    intento = request.json.get("intento", "").lower()

    if correcta in intento:
        mensaje = "¡Muy bien! 🌟 Lo hiciste excelente."
    else:
        mensaje = "Casi, inténtalo de nuevo 😊"

    return jsonify({"mensaje": mensaje})

# ----------------------------
# EJERCICIOS
# ----------------------------
@app.route("/ejercicios_frases")
def ejercicios():
    return jsonify({"palabras": ["avión", "elefante", "iguana", "oso", "uva"]})

@app.route("/oracion_vocal", methods=["POST"])
def oracion_vocal():
    vocal = request.json.get("vocal", "A")
    return jsonify({
        "palabra_clave": "avión",
        "oracion": "El avión vuela alto en el cielo"
    })

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
