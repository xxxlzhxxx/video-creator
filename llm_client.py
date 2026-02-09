"""
LLM Client Module - Handles prompt enhancement for video generation.
Uses Seed 2.0 via OpenAI-compatible API for Volcengine Ark.
"""
from typing import Optional
from openai import OpenAI
from config import ARK_API_KEY, ARK_BASE_URL, LLM_ENDPOINT


class LLMClient:
    """Client for enhancing video generation prompts using Seed 2.0."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=ARK_API_KEY,
            base_url=ARK_BASE_URL
        )
        self.endpoint = LLM_ENDPOINT
    
    def enhance_video_prompt(
        self,
        user_input: str,
        style: str = "cinematic",
        language: str = "English"
    ) -> str:
        """
        Convert simple user description to detailed video generation prompt.
        
        Args:
            user_input: Simple description from user
            style: Video style (cinematic, anime, realistic, etc.)
            language: Output language for the prompt
            
        Returns:
            Enhanced prompt optimized for video generation
        """
        system_prompt = f"""You are an expert at crafting prompts for AI video generation models.
Your task is to transform simple user descriptions into detailed, effective video generation prompts.

Guidelines for creating video prompts:
1. Be specific about camera movements (pan, zoom, tracking, static)
2. Describe lighting conditions (golden hour, dramatic shadows, soft diffused)
3. Include motion descriptions (how subjects move, speed, direction)
4. Specify visual style ({style} style)
5. Add quality keywords (4K, high resolution, cinematic)
6. Keep prompts concise but descriptive (50-100 words ideal)

Output only the enhanced prompt in {language}, nothing else."""

        user_prompt = f"""Transform this into a video generation prompt:

"{user_input}"

Remember: Focus on visual details, camera work, and motion. Output only the enhanced prompt."""

        completion = self.client.chat.completions.create(
            model=self.endpoint,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        request_id = completion.id
        print(f"[LLM] Request ID: {request_id}", flush=True)
        
        enhanced_prompt = completion.choices[0].message.content.strip()
        
        # Remove quotes if present
        if enhanced_prompt.startswith('"') and enhanced_prompt.endswith('"'):
            enhanced_prompt = enhanced_prompt[1:-1]
        
        return enhanced_prompt
    
    def generate_motion_prompt(
        self,
        image_description: str = None,
        motion_type: str = "natural"
    ) -> str:
        """
        Generate motion prompt for image-to-video generation.
        
        Args:
            image_description: Optional description of the image content
            motion_type: Type of motion (natural, dramatic, subtle, dynamic)
            
        Returns:
            Motion prompt for animating the image
        """
        system_prompt = """You are an expert at creating motion prompts for image-to-video AI models.
Your task is to describe how elements in an image should move to create a natural-looking video.

Guidelines:
1. Describe subtle, realistic movements
2. Consider physics and natural motion
3. Include camera movement if appropriate
4. Keep descriptions concise (20-50 words)
5. Focus on bringing the scene to life naturally

Output only the motion prompt, nothing else."""

        if image_description:
            user_prompt = f"""Create a {motion_type} motion prompt for this image:

"{image_description}"

Describe how elements should move and any camera motion."""
        else:
            user_prompt = f"""Create a {motion_type} motion prompt for animating a static image.
Describe general, natural movements that would work for most images."""

        completion = self.client.chat.completions.create(
            model=self.endpoint,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        return completion.choices[0].message.content.strip()


def test_llm_client():
    """Test LLM client functionality."""
    client = LLMClient()
    
    # Test prompt enhancement
    simple_prompt = "猫咪在花园里玩耍"
    enhanced = client.enhance_video_prompt(simple_prompt, style="realistic")
    print(f"Original: {simple_prompt}")
    print(f"Enhanced: {enhanced}")
    
    # Test motion prompt
    motion = client.generate_motion_prompt("A serene lake with mountains")
    print(f"\nMotion prompt: {motion}")
    
    return enhanced, motion


if __name__ == "__main__":
    test_llm_client()
