from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from paintclouds.PointCloudInterpreter import PointCloudInterpreter
from BestCutAlgorithm.BranchPruner import BranchPruner
from GUI.GUIModel import ModelBackend

app = Flask(__name__)
CORS(app)

# Inizializza componenti
interpreter = PointCloudInterpreter()
pruner = BranchPruner()
model = ModelBackend(interpreter, pruner)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set_dataset_folder", methods=["POST"])
def set_dataset_folder():
    folder = request.json.get("folder")
    if not folder:
        return jsonify({"error": "No folder provided"}), 400
    try:
        model.set_dataset_folder(folder)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/load_dataset", methods=["POST"])
def load_dataset():
    try:
        result = model.load_dataset_folder()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_params_weights", methods=["GET"])
def get_params_weights():
    """Restituisce i parametri e i pesi attuali."""
    try:
        return jsonify(model.get_parameters_weights())
    except Exception as e:
        # Assicurati che il tuo ModelBackend.get_parameters_weights non dia errori
        # anche se non è stato caricato nessun dataset
        return jsonify({"error": str(e)}), 500

@app.route("/dataset/<int:index>", methods=["GET"])
def show_dataset(index):
    try:
        return jsonify(model.show_dataset(index))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/update_algorithm", methods=["POST"])
def update_algorithm():
    feedback = request.json or {}
    model.better_algorithm(feedback.get("estimation", {}), feedback.get("weights", {}))
    return jsonify({"status": "updated"})

@app.route("/save_algorithm", methods=["POST"])
def save_algorithm():
    model.save_algorithm()
    return jsonify({"status": "saved"})

@app.route("/cut_document", methods=["GET"])
def cut_document():
    # ritorna il documento reale dei rami da tagliare
    return jsonify(model.get_cut_document())

if __name__ == "__main__":
    app.run(debug=True)
