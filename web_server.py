"""
Video Creator Web API Server
Flask-based API for video generation and editing.
"""
import os
import uuid
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from video_generator import VideoGenerator
from llm_client import LLMClient
from config import OUTPUT_DIR, UPLOADS_DIR, VIDEOS_DIR

app = Flask(__name__, static_folder='static')
CORS(app)

# History file path
HISTORY_FILE = os.path.join(OUTPUT_DIR, 'history.json')

# Store task status (in-memory, synced to file for persistence)
tasks = {}

# Load history from file on startup
def load_history():
    global tasks
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            print(f"[History] Loaded {len(tasks)} tasks from history", flush=True)
        except Exception as e:
            print(f"[History] Failed to load history: {e}", flush=True)
            tasks = {}

def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[History] Failed to save history: {e}", flush=True)

# Load history on module load
load_history()

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}


def allowed_file(filename, file_type='image'):
    if file_type == 'image':
        allowed = ALLOWED_IMAGE_EXTENSIONS
    else:
        allowed = ALLOWED_VIDEO_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def generate_video_task(
    task_id: str,
    mode: str,
    text: str = None,
    image_path: str = None,
    video_path: str = None,
    ratio: str = "16:9",
    duration: int = 5,
    enhance_prompt: bool = True
):
    """Background task to generate video."""
    try:
        print(f"\n{'='*60}", flush=True)
        print(f"[Task {task_id}] Starting video generation", flush=True)
        print(f"[Task {task_id}] Mode: {mode}", flush=True)
        print(f"{'='*60}", flush=True)
        
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['progress'] = 'Initializing...'
        
        gen = VideoGenerator()
        
        # Enhance prompt if requested and text is provided
        if enhance_prompt and text:
            tasks[task_id]['progress'] = 'Enhancing prompt with AI...'
            try:
                llm = LLMClient()
                enhanced_text = llm.enhance_video_prompt(text)
                print(f"[Task {task_id}] Enhanced prompt: {enhanced_text[:100]}...", flush=True)
                text = enhanced_text
                tasks[task_id]['enhanced_prompt'] = enhanced_text
            except Exception as e:
                print(f"[Task {task_id}] Prompt enhancement failed: {e}, using original", flush=True)
        
        def progress_callback(status, elapsed):
            tasks[task_id]['progress'] = f'Status: {status} ({elapsed:.0f}s)'
            tasks[task_id]['elapsed'] = elapsed
        
        result = None
        
        if mode == 'text2video':
            tasks[task_id]['progress'] = 'Generating video from text...'
            result = gen.generate_from_text(
                text,
                output_filename=f"video_{task_id}",
                ratio=ratio,
                duration=duration,
                callback=progress_callback
            )
        
        elif mode == 'image2video':
            tasks[task_id]['progress'] = 'Generating video from image...'
            result = gen.generate_from_image(
                image_path,
                motion_prompt=text or "",
                output_filename=f"video_{task_id}",
                ratio=ratio,
                duration=duration,
                callback=progress_callback
            )
        
        elif mode == 'edit':
            tasks[task_id]['progress'] = 'Editing video...'
            # Can use either image or video as source
            source_path = video_path or image_path
            result = gen.edit_video(
                source_path,
                text,
                output_filename=f"video_{task_id}",
                ratio=ratio,
                duration=duration,
                callback=progress_callback
            )
        
        if result and result.get('status') == 'succeeded':
            print(f"\n{'='*60}", flush=True)
            print(f"[Task {task_id}] Video generation completed!", flush=True)
            print(f"{'='*60}\n", flush=True)
            
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 'Done!'
            tasks[task_id]['completed_at'] = datetime.now().isoformat()
            tasks[task_id]['result'] = {
                'video_url': result.get('video_url'),
                'local_path': result.get('local_path'),
                'video_filename': os.path.basename(result.get('local_path', '')) if result.get('local_path') else None
            }
            save_history()  # Persist to file
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result'
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = str(error_msg)
            save_history()  # Persist to file
            
    except Exception as e:
        print(f"[Task {task_id}] Error: {e}", flush=True)
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        save_history()  # Persist to file


@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload image or video file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    file_type = request.form.get('type', 'image')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, file_type):
        return jsonify({'error': f'Invalid file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS if file_type == "image" else ALLOWED_VIDEO_EXTENSIONS}'}), 400
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOADS_DIR, unique_filename)
    
    file.save(filepath)
    
    return jsonify({
        'file_id': unique_filename,
        'file_path': filepath,
        'file_type': file_type
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    """Start video generation task."""
    data = request.json
    mode = data.get('mode', 'text2video')
    text = data.get('text', '')
    image_id = data.get('image_id')
    video_id = data.get('video_id')
    ratio = data.get('ratio', '16:9')
    duration = data.get('duration', 5)
    enhance_prompt = data.get('enhance_prompt', True)
    
    # Validate input
    if mode == 'text2video' and not text.strip():
        return jsonify({'error': 'Text prompt is required for text-to-video mode'}), 400
    
    if mode == 'image2video' and not image_id:
        return jsonify({'error': 'Image is required for image-to-video mode'}), 400
    
    if mode == 'edit' and not (image_id or video_id):
        return jsonify({'error': 'Image or video is required for edit mode'}), 400
    
    # Resolve file paths
    image_path = os.path.join(UPLOADS_DIR, image_id) if image_id else None
    video_path = os.path.join(UPLOADS_DIR, video_id) if video_id else None
    
    # Validate files exist
    if image_path and not os.path.exists(image_path):
        return jsonify({'error': 'Upload image not found'}), 400
    if video_path and not os.path.exists(video_path):
        return jsonify({'error': 'Uploaded video not found'}), 400
    
    # Create task
    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {
        'id': task_id,
        'status': 'pending',
        'progress': 'Starting...',
        'created_at': datetime.now().isoformat(),
        'params': {
            'mode': mode,
            'prompt': text,  # Store full prompt for history
            'ratio': ratio,
            'duration': duration
        }
    }
    
    # Start background task
    thread = threading.Thread(
        target=generate_video_task,
        args=(task_id, mode, text, image_path, video_path, ratio, duration, enhance_prompt)
    )
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'pending'})


@app.route('/api/status/<task_id>')
def get_status(task_id):
    """Get task status."""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(tasks[task_id])


@app.route('/api/download/<task_id>')
def download(task_id):
    """Download generated video."""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': 'Video not ready yet'}), 400
    
    local_path = task['result'].get('local_path')
    if not local_path or not os.path.exists(local_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        local_path,
        as_attachment=True,
        download_name=task['result'].get('video_filename', f'video_{task_id}.mp4')
    )


@app.route('/api/preview/<task_id>')
def preview(task_id):
    """Stream video for preview."""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': 'Video not ready yet'}), 400
    
    local_path = task['result'].get('local_path')
    if not local_path or not os.path.exists(local_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(local_path, mimetype='video/mp4')


@app.route('/api/tasks')
def list_tasks():
    """List all tasks."""
    return jsonify(list(tasks.values()))


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    print("\n" + "="*60)
    print("Video Creator Server Starting...")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Uploads directory: {UPLOADS_DIR}")
    print(f"Videos directory: {VIDEOS_DIR}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=True)
