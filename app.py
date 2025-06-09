from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv
import logging
import time
import base64
import cv2
from celery.result import AsyncResult
from ultralytics import YOLO

# Import the Celery task
from celery_worker import process_video_task

# Import the S3 utility functions
from s3_utils import upload_file_to_s3, download_file_from_s3, delete_file_from_s3, check_file_exists, generate_presigned_url, get_s3_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
logger.info("Environment variables loaded from .env file")

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.permanent_session_lifetime = timedelta(minutes=30)

# --- Configuration ---
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['FRAME_EXTRACTION_OUTPUT'] = 'static/extracted_frames'
app.config['YOLO_MODEL_PATH'] = 'models/best_weights.pt'

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FRAME_EXTRACTION_OUTPUT'], exist_ok=True)
os.makedirs('models', exist_ok=True)

# S3 Configuration
S3_BUCKET = os.getenv('S3_BUCKET_NAME', 'aispry-project')
S3_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_UPLOAD_FOLDER = os.getenv('S3_UPLOAD_FOLDER', '2024_Oct_CR_WagonDamageDetection/Wagon_H')

logger.info(f"S3 Configuration - Bucket: {S3_BUCKET}, Region: {S3_REGION}, Folder: {S3_UPLOAD_FOLDER}")

# --- Global Variables & Initializations ---

# Initialize S3 client
s3_client = get_s3_client()
if s3_client is None:
    logger.error("Failed to initialize S3 client")
else:
    logger.info(f"S3 client initialized for region: {S3_REGION}")

# --- Optimized Functions ---

def get_system_status():
    """
    Optimized function to get system status with a single S3 paginator call.
    """
    try:
        total_videos_count = 0
        storage_bytes = 0
        
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_UPLOAD_FOLDER)

        for page in pages:
            if 'Contents' in page:
                for item in page['Contents']:
                    storage_bytes += item.get('Size', 0)
                    if item['Key'].lower().endswith(('.mp4', '.avi', '.mov')):
                        total_videos_count += 1
        
        if storage_bytes < 1024:
            storage_usage = f"{storage_bytes} B"
        elif storage_bytes < 1024**2:
            storage_usage = f"{storage_bytes/1024:.1f} KB"
        elif storage_bytes < 1024**3:
            storage_usage = f"{storage_bytes/(1024**2):.1f} MB"
        else:
            storage_usage = f"{storage_bytes/(1024**3):.1f} GB"

        return {
            "last_upload_time": None, "processing_speed": "Optimal",
            "system_status": "Online" if s3_client else "Offline",
            "storage_usage": storage_usage, "total_videos": total_videos_count,
            "total_detections": 0
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {"last_upload_time": None, "processing_speed": "Unknown", "system_status": "Error",
                "storage_usage": "Unknown", "total_videos": 0, "total_detections": 0}

# --- User and Auth Data ---
USERS = {
    "admin": "123",
    "user": "123",
    "admin1": "Uploader@123"
}

ADMIN_ROLES = {
    "admin": "standard",
    "admin1": "s3_uploader"
}

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin1_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('role') != 's3_uploader':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_standard_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('role') == 's3_uploader':
            flash('This page is only available for standard admin users.', 'error')
            if session.get('role') == 's3_uploader':
                return redirect(url_for('s3_dashboard'))
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Routes ---
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 's3_uploader':
        return redirect(url_for('s3_dashboard'))
    return render_template('index.html', username=session.get('username'), system_status=get_system_status())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = ADMIN_ROLES.get(username, 'user')
            if session.get('role') == 's3_uploader':
                return redirect(url_for('s3_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
@admin_standard_required
def upload():
    # This route is primarily for displaying the video retrieval UI.
    # The actual retrieval logic is handled by '/retrieve_videos'
    return render_template('upload.html', username=session.get('username'))

@app.route('/retrieve_videos', methods=['POST'])
@login_required
@admin_standard_required
def retrieve_videos():
    # This function would contain the logic to retrieve video lists from S3
    # based on form data (date, camera, etc.)
    # For now, it returns an empty list as a placeholder.
    return jsonify({"success": True, "folders": []})


@app.route('/frame_extraction', methods=['GET', 'POST'])
@login_required
@admin_standard_required
def frame_extraction():
    if request.method == 'POST':
        if 'video' not in request.files or not request.files['video'].filename:
            return jsonify({'success': False, 'error': 'No file part'})
        
        file = request.files['video']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)
            
            logger.info(f"Video saved to {video_path}, dispatching to Celery worker.")
            
            task = process_video_task.delay(video_path, app.config['YOLO_MODEL_PATH'])
            
            return jsonify({'success': True, 'task_id': task.id})
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'})
    
    return render_template('frame_extraction.html', frames=None)

@app.route('/task-status/<task_id>')
@login_required
def task_status(task_id):
    task = AsyncResult(task_id, app=process_video_task.app)
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending...', 'progress': 0}
    elif task.state != 'FAILURE':
        response = {'state': task.state, 'status': task.info.get('status', ''), 'progress': task.info.get('progress', 0)}
        if task.state == 'SUCCESS':
            response['result'] = task.result
    else:
        response = {'state': task.state, 'status': str(task.info), 'error': True}
    return jsonify(response)

@app.route('/damage_detection', methods=['GET', 'POST'])
@login_required
@admin_standard_required
def damage_detection():
    # Placeholder for the damage detection page
    return render_template('damage_detection.html', videos=[], selected_date=datetime.now().strftime('%Y-%m-%d'))


@app.route('/dashboard')
@login_required
@admin_standard_required
def dashboard():
    reports = [] 
    chart_data = {
        "damage_by_date": [], "damage_types": {"types": [], "counts": []},
        "damage_severity": {"levels": [], "counts": []},
        "damage_locations": {"locations": [], "counts": []}
    }
    return render_template('dashboard.html',
                           reports=reports,
                           username=session.get('username'),
                           system_status=get_system_status(),
                           chart_data=chart_data)

@app.route('/s3_dashboard', methods=['GET', 'POST'])
@login_required
@admin1_required
def s3_dashboard():
    # Placeholder for S3 uploader dashboard
    return render_template('s3_dashboard.html', username=session.get('username'))


if __name__ == '__main__':
    app.run(debug=True)
