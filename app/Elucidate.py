"""
Script:- Elucidate.py
Usage:- python Elucidate.py
"""

import os
from flask import Flask, render_template, request, send_file, abort, jsonify, Response, stream_with_context
from app.Operations import get_pdf_list, initialize_pdf, ask_pdf, add_tokens, get_models, set_model, get_active_model
app = Flask(__name__, template_folder="./templates")

PDF_DIR = os.path.join(os.path.dirname(__file__), '..', 'pdf')


@app.route("/")
def index():
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


@app.route('/<pdf_name>')
def show_pdf(pdf_name):
    return render_template('book.html')


@app.route('/pdf/<pdf_name>')
def serve_pdf(pdf_name):
    path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype='application/pdf')


@app.route('/api/pdfs', methods=['GET'])
def list_pdfs():
    files = get_pdf_list()
    return jsonify({"pdfs": files})


@app.route('/api/initialise', methods=['POST'])
def initialise():
    pdf_name = request.form.get('pdf_name') or request.json and request.json.get('pdf_name')
    if not pdf_name:
        return jsonify({"error": "pdf_name required"}), 400

    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        dest = os.path.join(PDF_DIR, file.filename)
        file.save(dest)
        pdf_name = file.filename

    result = initialize_pdf(pdf_name)
    return jsonify(result)


@app.route('/api/models', methods=['GET'])
def list_models():
    return jsonify({"models": get_models(), "active": get_active_model()})


@app.route('/api/model', methods=['POST'])
def select_model():
    data = request.get_json() or {}
    model = data.get('model') or request.form.get('model')
    if not model:
        return jsonify({"error": "model required"}), 400
    set_model(model)
    return jsonify({"status": "ok", "model": model})


@app.route('/api/ask', methods=['POST'])
def ask():
    question = request.form.get('question') or (request.json or {}).get('question')
    if not question:
        return jsonify({"error": "question required"}), 400

    pdf_name = request.form.get('pdf_name') or (request.json or {}).get('pdf_name', '')

    def generate():
        try:
            for token in ask_pdf(question):
                if token.startswith('\x00'):
                    try:
                        add_tokens(pdf_name, int(token[1:]))
                    except ValueError:
                        pass
                elif token.startswith('\x01'):
                    yield token[1:]  # forward error message as plain text
                else:
                    yield token
        except Exception as e:
            yield f"// error: {e}"

    resp = Response(stream_with_context(generate()), mimetype='text/plain')
    resp.headers['X-Accel-Buffering'] = 'no'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
