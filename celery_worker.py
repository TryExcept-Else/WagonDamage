import os
from celery import Celery, Task
import logging
import time
import base64
import cv2
from frame_extractor import extract_and_annotate_wagons
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Celery Configuration ---
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery = Celery(
    'tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# --- Global Model Loading for Celery Worker ---
# The model is loaded once per worker process. This is the most efficient approach.
YOLO_MODEL_PATH = 'models/best_weights.pt'
yolo_model = None

try:
    if os.path.exists(YOLO_MODEL_PATH):
        yolo_model = YOLO(YOLO_MODEL_PATH)
        logger.info(f"YOLO model loaded successfully in Celery worker from {YOLO_MODEL_PATH}")
    else:
        logger.error(f"YOLO model file not found at {YOLO_MODEL_PATH}")
except Exception as e:
    logger.error(f"Error loading YOLO model in Celery worker: {e}", exc_info=True)


# --- Celery Task Definition ---
@celery.task(bind=True)
def process_video_task(self: Task, video_path: str, model_path: str):
    """
    Celery task to process a video for frame extraction and wagon annotation.
    It uses the globally pre-loaded YOLO model for efficiency.
    """
    global yolo_model
    if yolo_model is None:
        # This is a fallback in case the initial loading failed.
        try:
            logger.warning("YOLO model not pre-loaded. Attempting to load within the task.")
            yolo_model = YOLO(model_path)
            logger.info("YOLO model reloaded successfully within the task.")
        except Exception as e:
            logger.error(f"Failed to reload YOLO model within task: {e}")
            self.update_state(state='FAILURE', meta={'status': 'Model could not be loaded.'})
            return # Exit the task if model loading fails

    try:
        logger.info(f"Starting video processing task for: {video_path}")
        self.update_state(state='PROGRESS', meta={'status': 'Processing started...', 'progress': 5})

        output_dir = os.path.join('static/extracted_frames', time.strftime("%Y%m%d-%H%M%S"))
        output_video_path = os.path.join(output_dir, 'annotated_video.mp4')
        os.makedirs(output_dir, exist_ok=True)
        
        # The `extract_and_annotate_wagons` function now uses the pre-loaded model.
        saved_count, frame_images = extract_and_annotate_wagons(
            video_path=video_path,
            output_video_path=output_video_path,
            model=yolo_model, # Pass the loaded model object
            task=self
        )

        logger.info(f"Frame extraction complete. Found {saved_count} frames.")
        self.update_state(state='PROGRESS', meta={'status': 'Encoding frames...', 'progress': 95})

        encoded_frames = []
        for frame in frame_images:
            _, buffer = cv2.imencode('.jpg', frame)
            encoded_frame = base64.b64encode(buffer).decode('utf-8')
            encoded_frames.append(f"data:image/jpeg;base64,{encoded_frame}")

        logger.info("Task finished successfully.")
        return {'status': 'Completed', 'result': encoded_frames, 'count': saved_count}

    except Exception as e:
        logger.error(f"Error during video processing task: {str(e)}", exc_info=True)
        self.update_state(state='FAILURE', meta={'status': 'Task failed', 'error': str(e)})
        raise

