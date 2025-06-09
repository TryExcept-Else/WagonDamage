import cv2
import os
from ultralytics import YOLO
import collections
import logging
import torch
import torch.nn as nn
from ultralytics.nn.tasks import DetectionModel, SegmentationModel
from ultralytics.nn.modules import Conv, C2f, Concat
from ultralytics.nn.modules.block import Bottleneck

# Configure logging
logger = logging.getLogger(__name__)

# --- FIX for PyTorch Model Loading ---
try:
    torch.serialization.add_safe_globals([
        DetectionModel,
        SegmentationModel,
        Conv,
        C2f,
        Concat,
        Bottleneck,
        nn.Sequential,
        nn.Conv2d,
        nn.BatchNorm2d,
        nn.SiLU,
        nn.Upsample,
        nn.ModuleList
    ])
except AttributeError:
    logger.warning("Could not set safe globals for torch.serialization.")


def extract_and_annotate_wagons(video_path, output_video_path, model, task=None):
    """
    Processes a video to detect wagons using a pre-loaded YOLO model,
    returns annotated frames, and creates an annotated video, while updating
    Celery task progress.

    Args:
        video_path (str): Path to the input video file.
        output_video_path (str): Path to save the annotated output video.
        model (YOLO): The pre-loaded YOLO model instance.
        task (celery.Task, optional): Celery task instance for progress updates.
    """
    # --- Configuration ---
    CONFIDENCE_THRESHOLD = 0.6
    WAGON_CLASS_ID = 1
    CAPTURE_DELAY = 5
    FRAME_BUFFER_SIZE = CAPTURE_DELAY + 1

    if model is None:
        logger.error("YOLO model is not loaded. Aborting extraction.")
        if task:
            task.update_state(state='FAILURE', meta={'status': 'Model not loaded.'})
        return 0, []

    try:
        output_video_dir = os.path.dirname(output_video_path)
        os.makedirs(output_video_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating output video directory: {e}")
        return 0, []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Error: Could not open video file {video_path}")
        return 0, []

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    frame_buffer = collections.deque(maxlen=FRAME_BUFFER_SIZE)
    current_capture_state = "SEARCHING_FOR_WAGON"
    potential_capture_frame_img = None
    saved_frame_count = 0
    saved_frames = []
    frame_idx = 0

    logger.info(f"Processing video: {video_path}...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        
        if task and total_frames > 0 and frame_idx % 20 == 0:
            progress = 10 + int((frame_idx / total_frames) * 80)
            task.update_state(state='PROGRESS', meta={'status': f'Processing frame {frame_idx}/{total_frames}', 'progress': progress})

        original_frame_for_buffer = frame.copy()
        annotated_frame_for_video = frame.copy()

        results = model(original_frame_for_buffer, verbose=False, conf=CONFIDENCE_THRESHOLD)

        current_detected_wagon_boxes_coords = []
        if results and results[0].boxes:
            for box_obj in results[0].boxes:
                conf = box_obj.conf.item()
                cls_id = int(box_obj.cls.item())

                if cls_id == WAGON_CLASS_ID and conf >= CONFIDENCE_THRESHOLD:
                    current_detected_wagon_boxes_coords.append(box_obj.xyxy.cpu().numpy().flatten().tolist())

        video_writer.write(annotated_frame_for_video)
        frame_buffer.append((original_frame_for_buffer, current_detected_wagon_boxes_coords))

        if len(frame_buffer) == FRAME_BUFFER_SIZE:
            num_current_wagon_boxes = len(current_detected_wagon_boxes_coords)
            oldest_frame_img_in_buf, oldest_wagon_boxes_in_buf_coords = frame_buffer[0]
            num_oldest_wagon_boxes_in_buf = len(oldest_wagon_boxes_in_buf_coords)

            if current_capture_state == "SEARCHING_FOR_WAGON":
                if num_current_wagon_boxes == 1:
                    current_capture_state = "SINGLE_WAGON_PASSING"
                    potential_capture_frame_img = None
            elif current_capture_state == "SINGLE_WAGON_PASSING":
                if num_current_wagon_boxes == 1:
                    if num_oldest_wagon_boxes_in_buf == 1:
                        potential_capture_frame_img = oldest_frame_img_in_buf.copy()
                else:
                    if potential_capture_frame_img is not None:
                        saved_frames.append(potential_capture_frame_img)
                        saved_frame_count += 1
                    potential_capture_frame_img = None
                    current_capture_state = "SEARCHING_FOR_WAGON"

    if current_capture_state == "SINGLE_WAGON_PASSING" and potential_capture_frame_img is not None:
        saved_frames.append(potential_capture_frame_img)
        saved_frame_count += 1

    cap.release()
    video_writer.release()
    logger.info(f"Processing complete. Extracted {saved_frame_count} individual wagon frames.")
    return saved_frame_count, saved_frames
