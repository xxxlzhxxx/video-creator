"""
Video Generator Module - Core video generation using Doubao-Seedance-2.0 via Volcengine Ark.
Supports text-to-video, image-to-video, and video editing modes.
"""
import os
import time
import base64
import requests
from typing import Optional, Dict, Any, List

# Try to import from volcenginesdkarkruntime, fallback to alternative
try:
    from volcenginesdkarkruntime import Ark
except ImportError:
    # Alternative import for older SDK versions
    from volcengine.ark import Ark

from config import (
    ARK_API_KEY, ARK_BASE_URL, VIDEO_ENDPOINT,
    VIDEOS_DIR, POLL_INTERVAL, MAX_POLL_TIME, 
    DEFAULT_RATIO, DEFAULT_DURATION, DEFAULT_WATERMARK
)


class VideoGenerator:
    """Client for generating videos using Doubao-Seedance-2.0."""
    
    def __init__(self):
        self.client = Ark(
            base_url=ARK_BASE_URL,
            api_key=ARK_API_KEY
        )
        self.endpoint = VIDEO_ENDPOINT
    
    def create_task(
        self,
        content: List[Dict[str, Any]],
        ratio: str = DEFAULT_RATIO,
        duration: int = DEFAULT_DURATION,
        watermark: bool = DEFAULT_WATERMARK
    ) -> str:
        """
        Create a video generation task.
        
        Args:
            content: List of content items (text, image_url, video)
            ratio: Video aspect ratio (16:9, 9:16, 1:1, etc.)
            duration: Video duration in seconds (5-12)
            watermark: Whether to add watermark
            
        Returns:
            Task ID for polling status
        """
        print(f"[VideoGen] Creating task with endpoint: {self.endpoint}", flush=True)
        print(f"[VideoGen] Parameters: ratio={ratio}, duration={duration}s", flush=True)
        
        create_result = self.client.content_generation.tasks.create(
            model=self.endpoint,
            content=content,
            ratio=ratio,
            duration=duration,
            watermark=watermark
        )
        
        task_id = create_result.id
        print(f"[VideoGen] Task created: {task_id}", flush=True)
        return task_id
    
    def poll_status(self, task_id: str, callback=None) -> Dict[str, Any]:
        """
        Poll task status until completion or failure.
        
        Args:
            task_id: The task ID to poll
            callback: Optional callback function for progress updates
            
        Returns:
            Final task result with video URL or error
        """
        print(f"[VideoGen] Polling status for task: {task_id}", flush=True)
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > MAX_POLL_TIME:
                return {
                    "status": "timeout",
                    "error": f"Task timed out after {MAX_POLL_TIME}s"
                }
            
            get_result = self.client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            
            if callback:
                callback(status, elapsed)
            
            if status == "succeeded":
                print(f"[VideoGen] Task succeeded after {elapsed:.1f}s", flush=True)
                # Debug: print full result
                print(f"[VideoGen] Raw result: {get_result}", flush=True)
                
                # Extract video URL from result
                video_url = None
                
                # The content is an object with video_url attribute directly
                if hasattr(get_result, 'content') and get_result.content:
                    content = get_result.content
                    print(f"[VideoGen] Content: {content}", flush=True)
                    
                    # Direct attribute access on content object
                    if hasattr(content, 'video_url'):
                        video_url = content.video_url
                        print(f"[VideoGen] Found video_url on content: {video_url}", flush=True)
                    elif hasattr(content, 'video'):
                        video_url = content.video
                
                # Fallback: check video_url directly on result
                if not video_url and hasattr(get_result, 'video_url'):
                    video_url = get_result.video_url
                
                print(f"[VideoGen] Final video URL: {video_url}", flush=True)
                
                return {
                    "status": "succeeded",
                    "task_id": task_id,
                    "video_url": video_url,
                    "raw_result": str(get_result)
                }
            
            elif status == "failed":
                error_msg = getattr(get_result, 'error', 'Unknown error')
                print(f"[VideoGen] Task failed: {error_msg}", flush=True)
                return {
                    "status": "failed",
                    "task_id": task_id,
                    "error": str(error_msg)
                }
            
            else:
                # Status is usually "queuing" or "running"
                print(f"[VideoGen] Status: {status} ({elapsed:.1f}s elapsed)", flush=True)
                time.sleep(POLL_INTERVAL)
    
    def download_video(self, video_url: str, output_filename: str) -> Optional[str]:
        """
        Download video from URL to local file.
        
        Args:
            video_url: URL of the video to download
            output_filename: Filename (without extension) for output
            
        Returns:
            Local file path or None if failed
        """
        try:
            print(f"[VideoGen] Downloading video from: {video_url[:80]}...", flush=True)
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Determine extension from content-type or URL
            content_type = response.headers.get('content-type', '')
            if 'mp4' in content_type or video_url.endswith('.mp4'):
                ext = '.mp4'
            elif 'webm' in content_type or video_url.endswith('.webm'):
                ext = '.webm'
            else:
                ext = '.mp4'  # Default to mp4
            
            output_path = os.path.join(VIDEOS_DIR, f"{output_filename}{ext}")
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[VideoGen] Video saved to: {output_path}", flush=True)
            return output_path
            
        except Exception as e:
            print(f"[VideoGen] Download failed: {e}", flush=True)
            return None
    
    def generate_from_text(
        self,
        text_prompt: str,
        output_filename: str = None,
        ratio: str = DEFAULT_RATIO,
        duration: int = DEFAULT_DURATION,
        callback=None
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt only.
        
        Args:
            text_prompt: Description of the video to generate
            output_filename: Optional filename for downloaded video
            ratio: Video aspect ratio
            duration: Video duration in seconds
            callback: Progress callback function
            
        Returns:
            Result dict with status, video_url, and local_path
        """
        print(f"\n{'='*60}", flush=True)
        print(f"[VideoGen] Text-to-Video Generation", flush=True)
        print(f"[VideoGen] Prompt: {text_prompt[:100]}...", flush=True)
        print(f"{'='*60}", flush=True)
        
        content = [{"type": "text", "text": text_prompt}]
        
        task_id = self.create_task(content, ratio, duration)
        result = self.poll_status(task_id, callback)
        
        # Download video if successful
        if result["status"] == "succeeded" and result.get("video_url"):
            if not output_filename:
                output_filename = f"text2video_{task_id}"
            local_path = self.download_video(result["video_url"], output_filename)
            result["local_path"] = local_path
        
        return result
    
    def generate_from_image(
        self,
        image_path: str,
        motion_prompt: str = "",
        output_filename: str = None,
        ratio: str = DEFAULT_RATIO,
        duration: int = DEFAULT_DURATION,
        callback=None
    ) -> Dict[str, Any]:
        """
        Generate video from image with optional motion prompt.
        
        Args:
            image_path: Path to the source image
            motion_prompt: Optional text describing the motion/animation
            output_filename: Optional filename for downloaded video
            ratio: Video aspect ratio
            duration: Video duration in seconds
            callback: Progress callback function
            
        Returns:
            Result dict with status, video_url, and local_path
        """
        print(f"\n{'='*60}", flush=True)
        print(f"[VideoGen] Image-to-Video Generation", flush=True)
        print(f"[VideoGen] Image: {image_path}", flush=True)
        print(f"[VideoGen] Motion: {motion_prompt[:100] if motion_prompt else 'Auto'}...", flush=True)
        print(f"{'='*60}", flush=True)
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Determine MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{encoded_image}"
        
        content = [
            {"type": "image_url", "image_url": {"url": data_url}}
        ]
        
        if motion_prompt:
            content.append({"type": "text", "text": motion_prompt})
        
        task_id = self.create_task(content, ratio, duration)
        result = self.poll_status(task_id, callback)
        
        # Download video if successful
        if result["status"] == "succeeded" and result.get("video_url"):
            if not output_filename:
                output_filename = f"img2video_{task_id}"
            local_path = self.download_video(result["video_url"], output_filename)
            result["local_path"] = local_path
        
        return result
    
    def edit_video(
        self,
        video_path: str,
        edit_prompt: str,
        output_filename: str = None,
        ratio: str = DEFAULT_RATIO,
        duration: int = DEFAULT_DURATION,
        callback=None
    ) -> Dict[str, Any]:
        """
        Edit or extend existing video based on prompt.
        
        Args:
            video_path: Path to the source video
            edit_prompt: Description of edits to make
            output_filename: Optional filename for downloaded video
            ratio: Video aspect ratio
            duration: Video duration in seconds  
            callback: Progress callback function
            
        Returns:
            Result dict with status, video_url, and local_path
        """
        print(f"\n{'='*60}", flush=True)
        print(f"[VideoGen] Video Edit Mode", flush=True)
        print(f"[VideoGen] Video: {video_path}", flush=True)
        print(f"[VideoGen] Edit: {edit_prompt[:100]}...", flush=True)
        print(f"{'='*60}", flush=True)
        
        # Read and encode video
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        ext = os.path.splitext(video_path)[1].lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mov': 'video/quicktime'
        }
        mime_type = mime_types.get(ext, 'video/mp4')
        
        encoded_video = base64.b64encode(video_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{encoded_video}"
        
        content = [
            {"type": "video_url", "video_url": {"url": data_url}},
            {"type": "text", "text": edit_prompt}
        ]
        
        task_id = self.create_task(content, ratio, duration)
        result = self.poll_status(task_id, callback)
        
        # Download video if successful
        if result["status"] == "succeeded" and result.get("video_url"):
            if not output_filename:
                output_filename = f"edit_{task_id}"
            local_path = self.download_video(result["video_url"], output_filename)
            result["local_path"] = local_path
        
        return result


def test_text_to_video():
    """Test text-to-video generation."""
    gen = VideoGenerator()
    result = gen.generate_from_text(
        "A cute cat playing with a red ball on a sunny day, realistic style, 4K quality",
        ratio="16:9",
        duration=5
    )
    print(f"\nResult: {result}")
    return result


if __name__ == "__main__":
    test_text_to_video()
