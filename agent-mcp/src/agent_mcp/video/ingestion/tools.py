import base64
import subprocess
from io import BytesIO
from pathlib import Path


import av
import loguru 
from moviepy import VideoFileCLip
from PIL import Image

logger = loguru.logger.bind(name = "VideoTools")

def extract_video_clip(video_path:str , start_time: float, end_time: float,output_path: str = None) -> VideoFileCLip:
    if start_time>=end_time:
        raise ValueError("start_time must be less than end_time")

    command = [
        "ffmpeg",
        "-ss",
        str(start_time),
        "-to",
        str(end_time),
        "-i",
        video_path,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "copy",
        "-y",
        output_path,
    ]

    try:
        process = subprocess.Popen(command,stdout = subprocess.PIPE,stderr = subprocess.PIPE)
        stdout , _ = process.communicate()
        logger.debug(f"FFMpeg output: {stdout.decode('utf-8',erros = 'ignore')}")
        return VideoFileCLip(output_path)
    except subprocess.CalledProcessError as e:
        raise IOError(f"Failed to extract video clip: {str(e)}")

def encode_image(image: str | Image.Image) -> str:
    """Encode an image to base64 string"""
    try:
        if isinstance(image,str):
            with open(image,"rb") as image_file:
                image_str = image_file.read()
        else:
            if not image.format:
                image_format = "JPEG"
            else:
                image_format = image.format
            buffered = BytesIO()
            image.save(buffered,format = image_format)
            image_str = buffered.getvalue()
        return base64.b64encode(image_str).decode("utf-8")
    except (FileNotFoundError,IOError) as e:
        raise IOError(f"Failed to process image: {str(e)}")
    
def decode_image(base64_string: str)->Image.Image:
    """Decode a base64 string back into a PIL Image object"""

    try:
        image_bytes = base64.b64decode(base64_string)
        image_buffer = BytesIO(image_bytes)

        return Image.open(image_buffer)
    except (ValueError,IOError) as e:
        raise IOError(f"Failed to decode image: {str(e)}")
    
def re_encode_video(video_path: str)-> str:
    """RE-Encode a video file to ensure compatibility with PyAV"""
    if not Path(video_path).exists():
        logger.error(f"Error: Video file not found at {video_path}")
        return False
    
    try:
        with av.open(video_path) as _ :
            logger.info(f"Video {video_path} successfully opened by pyAv")
            return str(video_path)
    except Exception as e:
        logger.error(f"An Unexpected error occured while trying to open video {video_path}: {e}")
    finally:
        o_dir , o_fname = Path(video_path).parent , Path(video_path).name
        reencoded_filename = f"re_{o_fname}.mp4"
        reencoded_video_path = Path(o_dir) / reencoded_filename

        command = ["ffmpeg", "-i", video_path, "-c:v", "libx264", "-c:a", "copy", str(reencoded_video_path)]

        logger.info(f"Attempting to re-encode video using FFmpeg: {' '.join(command) }")

        try:
            result = subprocess.run(command,capture_output= True, text = True, check = True)
            logger.info(f"FFMpeg re-encoding successful for {video_path} to {reencoded_video_path}")
            logger.debug(f"FFMpeg stdout : {result.stdout}")
            logger.debug(f"FFmpeg stderr: {result.stderr}")

            try:
                with av.open(reencoded_video_path) as _ :
                    logger.info(f"RE encoded video {reencoded_video_path} successsfully opened by PyAV")
                    return str(reencoded_video_path)
            except Exception as e:
                logger.error(f"An unexpected error occured while trying to open re-encoded video {reencoded_video_path}: {e}")
                return None

        except Exception as e:
            logger.error(f"An Unexpected error occured during FFMpeg re-encoding : {e}")
            return None    