import os
import mimetypes
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import google.generativeai as genai

# --- Config ---
UPLOAD_FOLDER = "static/uploads"
FALLBACK_FOLDER = "static/fallback"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload dir exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Gemini API Setup ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_image", methods=["POST"])
def generate_image():
    data = request.json
    animal = data.get("animal")

    if not animal:
        return jsonify({"error": "No animal selected"}), 400

    try:
        # Call Gemini Image API
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"A high quality realistic photo of a {animal}"
        response = model.generate_images(prompt=prompt)

        if response.generated_images:
            image_base64 = response.generated_images[0].image_base64
            return jsonify({"image_base64": image_base64})

    except Exception as e:
        # Fallback to local image
        return jsonify({"fallback": f"/static/fallback/{animal}.jpg"})

    return jsonify({"error": "Image generation failed"}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        file_size = os.path.getsize(filepath)
        file_type = mimetypes.guess_type(filepath)[0] or "Unknown"

        return jsonify({
            "filename": filename,
            "file_size": f"{file_size / 1024:.2f} KB",
            "file_type": file_type,
            "file_url": f"/static/uploads/{filename}"
        })

    return jsonify({"error": "File type not allowed"}), 400

@app.route("/ask_gemini", methods=["POST"])
def ask_gemini():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(question)
        return jsonify({"answer": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
