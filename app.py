from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv
import logging
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

# S3 Configuration from environment variables
S3_BUCKET = os.getenv('S3_BUCKET_NAME', 'aispry-project')
S3_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_UPLOAD_FOLDER = os.getenv('S3_UPLOAD_FOLDER', '2024_Oct_CR_WagonDamageDetection/Wagon_H')  # previously hardcoded

logger.info(f"S3 Configuration - Bucket: {S3_BUCKET}, Region: {S3_REGION}, Folder: {S3_UPLOAD_FOLDER}")

# Check if AWS credentials are available
if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
    logger.info("AWS credentials found in environment variables")
else:
    logger.warning("AWS credentials not found in environment variables")

# Initialize S3 client using the utility function
s3_client = get_s3_client()

# Log connection status
if s3_client is None:
    logger.error("Failed to initialize S3 client")
else:
    logger.info(f"S3 client initialized for region: {S3_REGION}")
    logger.info(f"Target S3 folder: {S3_UPLOAD_FOLDER} in bucket: {S3_BUCKET}")
# Check upload folder configuration
if not S3_UPLOAD_FOLDER:
    logger.warning(f"The S3 upload folder path is empty. Please check configuration.")

# User authentication data
USERS = {
    "admin": "123",  # Production should use hashed passwords stored in database
    "user": "123",
    "admin1": "Uploader@123"  
}

# User role assignments
ADMIN_ROLES = {
    "admin": "standard",
    "admin1": "s3_uploader"
}

# Function to get videos from S3 based on date
def get_videos_by_date_from_s3(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d-%m-%Y')
        prefix = f"{S3_UPLOAD_FOLDER}/{formatted_date}/"
        
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix
        )
        
        if 'Contents' in response:
            # Extract video filenames from keys
            videos = []
            for item in response.get('Contents', []):
                key = item.get('Key', '')
                if key.lower().endswith(('.mp4', '.avi', '.mov')):
                    filename = key.split('/')[-1]
                    videos.append(filename)
            return videos
        return []
    except Exception as e:
        logger.error(f"Error fetching videos from S3: {str(e)}")
        return []

# Function to get damage reports from actual data
def get_damage_reports():
    # In production, this would retrieve from a database
    return []

# Function to get system status with real data
def get_system_status():
    try:
        # Get real count of videos from S3
        total_videos_count = 0
        try:
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=S3_UPLOAD_FOLDER
            )
            if 'Contents' in response:
                # Count only video files
                for item in response.get('Contents', []):
                    key = item.get('Key', '')
                    if key.lower().endswith(('.mp4', '.avi', '.mov')):
                        total_videos_count += 1
        except Exception as e:
            logger.error(f"Error counting videos: {str(e)}")
            
        # Calculate storage usage
        storage_bytes = 0
        try:
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=S3_UPLOAD_FOLDER
            )
            if 'Contents' in response:
                for item in response.get('Contents', []):
                    storage_bytes += item.get('Size', 0)
        except Exception as e:
            logger.error(f"Error calculating storage: {str(e)}")
            
        # Convert bytes to human-readable format
        if storage_bytes < 1024:
            storage_usage = f"{storage_bytes} B"
        elif storage_bytes < 1024 * 1024:
            storage_usage = f"{storage_bytes/1024:.1f} KB"
        elif storage_bytes < 1024 * 1024 * 1024:
            storage_usage = f"{storage_bytes/(1024*1024):.1f} MB"
        else:
            storage_usage = f"{storage_bytes/(1024*1024*1024):.1f} GB"
            
        return {
            "last_upload_time": None,
            "processing_speed": "Optimal",
            "system_status": "Online" if s3_client is not None else "Offline",
            "storage_usage": storage_usage,
            "total_videos": total_videos_count,
            "total_detections": 0
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "last_upload_time": None,
            "processing_speed": "Unknown",
            "system_status": "Error",
            "storage_usage": "Unknown",
            "total_videos": 0,
            "total_detections": 0
        }

# Initialize system status
SYSTEM_STATUS = get_system_status()

# Video MIME types mapping for S3 uploads
VIDEO_MIME_TYPES = {
    'mp4': 'video/mp4',
    'avi': 'video/x-msvideo',
    'mov': 'video/quicktime',
    # 'wmv': 'video/x-ms-wmv',
    # 'flv': 'video/x-flv',
    # 'mkv': 'video/x-matroska',
    # 'webm': 'video/webm',
    # '3gp': 'video/3gpp',
    # 'm4v': 'video/x-m4v'
}

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin1 role required decorator
def admin1_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('role') != 's3_uploader':
            flash('Access denied. You need admin1 privileges for this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Restrict regular admin routes for admin1 users
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

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Redirect based on role
    if session.get('role') == 's3_uploader':
        return redirect(url_for('s3_dashboard'))
    
    return render_template('index.html', 
                         username=session.get('username'),
                         system_status=SYSTEM_STATUS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = ADMIN_ROLES.get(username, 'user')
            
            # Redirect based on role
            if session.get('role') == 's3_uploader':
                return redirect(url_for('s3_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
@admin_standard_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Get parameters for file organization
            upload_date = request.form.get('upload_date')
            client_id = request.form.get('client_id', 'default_client')
            camera_angle = request.form.get('camera_angle', 'left')
            video_type = request.form.get('video_type', 'entry')
            
            try:
                # Format date
                if upload_date:
                    date_obj = datetime.strptime(upload_date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d-%m-%Y')
                else:
                    formatted_date = datetime.now().strftime('%d-%m-%Y')
                
                # Create S3 path
                s3_folder_path = f"{S3_UPLOAD_FOLDER}/{formatted_date}/{client_id}/raw-videos/{camera_angle}"
                
                # Upload to S3
                success, message, uploaded_s3_key = upload_file_to_s3(
                    file,
                    S3_BUCKET,
                    s3_folder_path,
                    VIDEO_MIME_TYPES,
                    filename=filename
                )
                
                if success:
                    flash(f'File successfully uploaded to S3: {uploaded_s3_key}')
                    
                    # Update system status
                    SYSTEM_STATUS['last_upload_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    SYSTEM_STATUS['total_videos'] += 1
                else:
                    flash(f'Error uploading to S3: {message}', 'error')
                
            except Exception as e:
                logger.error(f"Error uploading file: {str(e)}")
                flash(f'Error: {str(e)}', 'error')
            
            return redirect(url_for('upload'))
        else:
            allowed_formats = ', '.join(sorted(ALLOWED_EXTENSIONS))
            flash(f'Only video files are allowed ({allowed_formats})')
            return redirect(request.url)
    
    return render_template('upload.html', 
                          username=session.get('username'),
                          system_status=SYSTEM_STATUS)

@app.route('/damage_detection', methods=['GET', 'POST'])
@login_required
@admin_standard_required
def damage_detection():
    if request.method == 'POST':
        # Handle form submission
        date = request.form.get('date')
        video = request.form.get('video')
        
        if date and video:
            # Get the actual video data from S3
            logger.info(f"Starting processing for video: {video} from date: {date}")
            flash('Video processing started')
        else:
            flash('Missing date or video selection', 'error')
        
        # Redirect back to results
        return redirect(url_for('damage_detection', date=date))
    
    # Get date parameter from URL or use today's date
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get videos for the selected date
    videos = get_videos_by_date_from_s3(selected_date)
    
    return render_template('damage_detection.html',
                         username=session.get('username'),
                         videos=videos,
                         selected_date=selected_date)

@app.route('/dashboard')
@login_required
@admin_standard_required
def dashboard():
    # Get actual damage reports from our function (currently empty)
    reports = get_damage_reports()
    
    # Refresh system status to ensure latest data
    current_status = get_system_status()
    
    # If last_upload_time was set during previous operations, preserve it
    if SYSTEM_STATUS.get("last_upload_time") is not None:
        current_status["last_upload_time"] = SYSTEM_STATUS["last_upload_time"]
    
    # Update global system status with the refreshed data
    for key in current_status:
        SYSTEM_STATUS[key] = current_status[key]
    
    # Get statistics for charts
    chart_data = {}
    
    # For now we'll create empty chart data objects
    chart_data["damage_by_date"] = []
    chart_data["damage_types"] = {
        "types": [],
        "counts": []
    }
    chart_data["damage_severity"] = {
        "levels": [],
        "counts": []
    }
    chart_data["damage_locations"] = {
        "locations": [],
        "counts": []
    }
    
    return render_template('dashboard.html', 
                          reports=reports,
                          username=session.get('username'),
                          system_status=SYSTEM_STATUS,
                          chart_data=chart_data)

@app.route('/api/videos/<date>')
@login_required
@admin_standard_required
def get_videos_by_date(date):
    videos = get_videos_by_date_from_s3(date)
    return jsonify({"videos": videos})

@app.route('/api/reports')
@login_required
@admin_standard_required
def get_reports():
    reports = get_damage_reports()
    return jsonify({"reports": reports})

@app.route('/api/download/csv')
@login_required
@admin_standard_required
def download_csv():
    # In a real application, you would generate and return a CSV file
    return jsonify({"message": "CSV download functionality would be implemented here"})

@app.route('/api/download/pdf')
@login_required
@admin_standard_required
def download_pdf():
    # In a real application, you would generate and return a PDF file
    return jsonify({"message": "PDF download functionality would be implemented here"})

@app.route('/s3_dashboard', methods=['GET', 'POST'])
@login_required
@admin1_required
def s3_dashboard():
    # Check if S3 client is properly initialized
    if s3_client is None:
        flash('S3 connection is not available. Please check AWS credentials.', 'error')
        return render_template('s3_dashboard.html', username=session.get('username'))
    
    # Handle form submission (POST request)
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'video' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('s3_dashboard'))
        
        file = request.files['video']
        
        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('s3_dashboard'))
        
        if file and allowed_file(file.filename):
            try:
                # Get form parameters
                upload_date = request.form.get('upload_date')
                client_id = request.form.get('client_id', 'client_123')  # Default to client_123 for admin1
                camera_angle = request.form.get('camera_angle', 'left')  # Default to left if not specified
                video_type = request.form.get('video_type', 'entry')     # Default to entry if not specified
                
                # Convert upload_date from yyyy-mm-dd to dd-mm-yyyy for folder name
                if upload_date:
                    try:
                        date_obj = datetime.strptime(upload_date, '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%d-%m-%Y')
                    except ValueError:
                        logger.error(f"Invalid date format: {upload_date}")
                        formatted_date = datetime.now().strftime('%d-%m-%Y')
                else:
                    # If no date provided, use current date
                    formatted_date = datetime.now().strftime('%d-%m-%Y')
                
                # Format the date for filename (ddmmyyyy)
                filename_date = date_obj.strftime('%d%m%Y')
                
                # Secure the filename
                original_filename = secure_filename(file.filename)
                
                # Create new filename format: {date}_{camera_angle}_{entry/exit}.{extension}
                extension = os.path.splitext(original_filename)[1].lower()
                new_filename = f"{filename_date}_{camera_angle}_{video_type}{extension}"
                
                # Create the structured S3 path:
                # {S3_UPLOAD_FOLDER}/{date}/{client_id}/raw-videos/{camera_angle}/{filename}
                base_folder = S3_UPLOAD_FOLDER  # Path from environment variable
                s3_folder_path = f"{base_folder}/{formatted_date}/{client_id}/raw-videos/{camera_angle}"
                s3_key = f"{s3_folder_path}/{new_filename}"
                
                logger.info(f"Uploading file to structured path: {s3_key}")
                
                # Upload the file using the utility function
                success, message, uploaded_s3_key = upload_file_to_s3(
                    file,
                    S3_BUCKET,
                    s3_folder_path,
                    VIDEO_MIME_TYPES,
                    filename=new_filename  # Pass the new filename to the upload function
                )
                
                if success:
                    # Update system status
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    SYSTEM_STATUS['last_upload_time'] = current_time
                    SYSTEM_STATUS['total_videos'] += 1
                    SYSTEM_STATUS['system_status'] = "Online"
                    
                    logger.info(f"Successfully uploaded file to S3: {message}")
                    flash(f'Video successfully uploaded to S3 path: {uploaded_s3_key}', 'success')
                else:
                    logger.error(f"Error uploading to S3: {message}")
                    flash(f'Error: {message}', 'error')
                    SYSTEM_STATUS['system_status'] = "Error"
                
            except Exception as e:
                logger.error(f"General error during upload: {str(e)}")
                flash(f'Error uploading to S3: {str(e)}', 'error')
            
            return redirect(url_for('s3_dashboard'))
        else:
            allowed_formats = ', '.join(sorted(ALLOWED_EXTENSIONS))
            flash(f'Only video files are allowed ({allowed_formats})', 'error')
            return redirect(url_for('s3_dashboard'))
    
    # Render the dashboard template for GET requests
    return render_template('s3_dashboard.html', username=session.get('username'))

@app.route('/api/test-s3-connection')
def test_s3_connection():
    """Test endpoint to check S3 connection without authentication"""
    if s3_client is None:
        return jsonify({
            "status": "error",
            "message": "S3 client not initialized",
            "bucket": S3_BUCKET,
            "region": S3_REGION
        }), 500
    
    # Create a test key in the allowed folder
    test_key = f"{S3_UPLOAD_FOLDER}/connection_test.txt"
    
    try:
        # Test if we can check file existence (uses get_object with try/except)
        file_exists = check_file_exists(S3_BUCKET, test_key)
        
        return jsonify({
            "status": "success",
            "message": f"Successfully connected to S3 bucket: {S3_BUCKET} and folder: {S3_UPLOAD_FOLDER}",
            "bucket": S3_BUCKET,
            "region": S3_REGION,
            "folder": S3_UPLOAD_FOLDER,
            "test_file_exists": file_exists
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "bucket": S3_BUCKET,
            "region": S3_REGION
        }), 500

# New route for retrieving videos from S3
@app.route('/retrieve_videos', methods=['GET', 'POST'])
@login_required
@admin_standard_required
def retrieve_videos():
    if request.method == 'POST':
        # Extract the parameters from the form
        date = request.form.get('retrieve_date')
        camera_angle = request.form.get('camera_angle')
        video_type = request.form.get('video_type')
        
        try:
            # Format date from YYYY-MM-DD to DD-MM-YYYY format used in S3
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d-%m-%Y')
            
            # Create the S3 prefix path based on the parameters
            # Structure: {S3_UPLOAD_FOLDER}/{date}/{client_id}/raw-videos/{camera_angle}/{video_name}
            base_folder = S3_UPLOAD_FOLDER  # Path from environment variable
            prefix = f"{base_folder}/{formatted_date}/"
            
            logger.info(f"Searching S3 with prefix: {prefix}")
            
            # List client_id folders within the given date path
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=prefix,
                Delimiter='/'
            )
            
            folders = []
            
            # Process common prefixes (client_id folders)
            if 'CommonPrefixes' in response:
                for i, p in enumerate(response.get('CommonPrefixes', [])):
                    client_prefix = p.get('Prefix')
                    client_id = client_prefix.split('/')[-2]  # Get the client_id from the path
                    
                    # For each client, create the path to camera angle videos
                    camera_prefix = f"{client_prefix}raw-videos/{camera_angle}/"
                    
                    # Check if this camera angle exists for the client
                    cam_response = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET,
                        Prefix=camera_prefix,
                        Delimiter='/'
                    )
                    
                    # If the camera angle exists and has videos
                    if 'Contents' in cam_response or 'CommonPrefixes' in cam_response:
                        # List all videos in this directory
                        video_response = s3_client.list_objects_v2(
                            Bucket=S3_BUCKET,
                            Prefix=camera_prefix
                        )
                        
                        videos = []
                        # Filter videos based on video type (entry/exit)
                        for obj in video_response.get('Contents', []):
                            key = obj.get('Key')
                            filename = key.split('/')[-1]
                            # Check if the filename contains the requested video type
                            if video_type.lower() in filename.lower():
                                videos.append(filename)
                        
                        if videos:  # Only add folders that have matching videos
                            folder_name = f"{date_obj.strftime('%Y%m%d')}_{client_id}_{camera_angle}"
                            folders.append({
                                "id": i + 1,
                                "name": folder_name,
                                "s3_prefix": camera_prefix,
                                "videos": videos
                            })
            
            logger.info(f"Found {len(folders)} folders matching the criteria")
            return jsonify({"success": True, "folders": folders})
            
        except Exception as e:
            logger.error(f"Error retrieving videos: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    # GET method - just render the retrieval form
    return render_template('upload.html', username=session.get('username'))

# New route for starting the video processing
@app.route('/process_videos', methods=['POST'])
@login_required
@admin_standard_required
def process_videos():
    folder_id = request.form.get('folder_id')
    folder_name = request.form.get('folder_name')
    s3_prefix = request.form.get('s3_prefix')
    selected_videos = request.form.getlist('selected_videos[]')
    
    if not folder_id or not s3_prefix or not selected_videos:
        return jsonify({"success": False, "error": "Missing required parameters"})
    
    try:
        logger.info(f"Processing videos from {s3_prefix}: {selected_videos}")
        
        processed_videos = []
        
        # Create a temporary directory to store downloaded videos
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        for video_name in selected_videos:
            # Construct the full S3 key
            s3_key = f"{s3_prefix}{video_name}"
            
            # Local path for downloaded file
            local_path = os.path.join(temp_dir, video_name)
            
            # Download the file from S3
            success, message, _ = download_file_from_s3(
                S3_BUCKET,
                s3_key,
                local_path
            )
            
            if success:
                # Apply actual processing to the downloaded video
                # This would be replaced with your actual video processing algorithm
                try:
                    # Create a status object for this video
                    video_status = {
                        "name": video_name,
                        "status": "processed",
                        "path": local_path,
                        "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "size": os.path.getsize(local_path)
                    }
                    
                    # Add to processed videos list
                    processed_videos.append(video_status)
                    
                    logger.info(f"Successfully processed {video_name} from S3")
                except Exception as video_error:
                    logger.error(f"Error processing {video_name}: {str(video_error)}")
                    processed_videos.append({
                        "name": video_name,
                        "status": "error",
                        "error": str(video_error)
                    })
            else:
                logger.error(f"Failed to download {video_name}: {message}")
                processed_videos.append({
                    "name": video_name,
                    "status": "download_failed",
                    "error": message
                })
        
        # We would typically start an asynchronous job here to process videos
        # and provide a job ID for frontend tracking
        
        # For demonstration, we'll just clean up after ourselves
        import shutil
        shutil.rmtree(temp_dir)
        
        if processed_videos:
            return jsonify({
                "success": True, 
                "message": f"Successfully processed {len(processed_videos)} videos",
                "processed_videos": processed_videos
            })
        else:
            return jsonify({
                "success": False, 
                "error": "No videos were successfully downloaded"
            })
        
    except Exception as e:
        logger.error(f"Error processing videos: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True) 