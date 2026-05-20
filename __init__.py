from flask import Flask, render_template, Response, request, redirect, url_for, make_response
from .utils.video_processing import VideoProcessor
from .utils.stats import Stats
import json
import io
import csv
import os

app = Flask(__name__)
results = []
stats = Stats()
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        model = request.form['model']
        return redirect(url_for('processing', filename=filename, model=model))

@app.route('/processing/<filename>/<model>')
def processing(filename, model):
    return render_template('processing.html', filename=filename, model=model)

@app.route('/video_feed/<filename>/<model>')
def video_feed(filename, model):
    results.clear()
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weights', model)
    return Response(VideoProcessor(model_path=model_path, stats=stats, results_storage=results).process_video(video_path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_stats')
def get_stats():
    return Response(json.dumps({
        'total_count': stats.get_total_count(),
        'type_counts': stats.get_type_counts()
    }), mimetype='application/json')

@app.route('/export_results')
def export_results():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['frame', 'vehicle_id', 'class'])
    cw.writerows([(r['frame'], r['vehicle_id'], r['class']) for r in results])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output
