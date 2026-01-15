"""
Video Processing Module
=======================

Video processing capabilities:
- Video summarization
- Key frame extraction
- Video to text transcription
- Video understanding
"""

import base64
import io
import logging
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class VideoFormat(str, Enum):
    """支持的视频格式"""
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    WEBM = "webm"
    MKV = "mkv"


@dataclass
class VideoFrame:
    """视频帧"""
    timestamp: float  # 秒
    image_data: bytes
    description: str = ""
    
    def to_base64(self) -> str:
        return base64.b64encode(self.image_data).decode()


@dataclass
class VideoAnalysisResult:
    """视频分析结果"""
    summary: str = ""
    duration: float = 0.0
    frame_count: int = 0
    fps: float = 0.0
    resolution: Tuple[int, int] = (0, 0)
    key_frames: List[VideoFrame] = field(default_factory=list)
    transcript: str = ""
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "duration": self.duration,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "resolution": self.resolution,
            "key_frames_count": len(self.key_frames),
            "transcript": self.transcript,
            "scenes": self.scenes,
            "metadata": self.metadata
        }


class VideoProcessor:
    """
    视频处理器
    
    功能：
    - 视频摘要生成
    - 关键帧提取
    - 视频转文字
    - 视频理解
    """
    
    def __init__(
        self,
        workspace: str = "./workspace",
        default_model: str = "gpt-4o"
    ):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.default_model = default_model
    
    # ========================
    # 视频分析
    # ========================
    
    def analyze(
        self,
        video: Union[str, Path],
        extract_frames: int = 5,
        transcribe_audio: bool = True
    ) -> VideoAnalysisResult:
        """
        全面分析视频
        
        Args:
            video: 视频文件路径
            extract_frames: 提取的关键帧数量
            transcribe_audio: 是否转录音频
            
        Returns:
            VideoAnalysisResult: 分析结果
        """
        video_path = Path(video)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video}")
        
        result = VideoAnalysisResult()
        
        # 获取视频信息
        info = self.get_info(video_path)
        result.duration = info.get("duration", 0)
        result.frame_count = info.get("frame_count", 0)
        result.fps = info.get("fps", 0)
        result.resolution = info.get("resolution", (0, 0))
        result.metadata = info
        
        # 提取关键帧
        if extract_frames > 0:
            result.key_frames = self.extract_key_frames(video_path, extract_frames)
        
        # 转录音频
        if transcribe_audio:
            result.transcript = self.transcribe_audio(video_path)
        
        # 生成摘要
        result.summary = self._generate_summary(result)
        
        return result
    
    def get_info(self, video: Union[str, Path]) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            video: 视频文件路径
            
        Returns:
            视频信息字典
        """
        try:
            import cv2
            
            video_path = str(video)
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return {"error": "Cannot open video"}
            
            info = {
                "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "resolution": (
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                ),
                "codec": int(cap.get(cv2.CAP_PROP_FOURCC))
            }
            
            cap.release()
            return info
            
        except ImportError:
            return {"error": "OpenCV (cv2) is required for video processing"}
        except Exception as e:
            return {"error": str(e)}
    
    def extract_key_frames(
        self,
        video: Union[str, Path],
        num_frames: int = 5,
        method: str = "uniform"
    ) -> List[VideoFrame]:
        """
        提取关键帧
        
        Args:
            video: 视频文件路径
            num_frames: 提取的帧数
            method: 提取方法 ("uniform" 均匀提取, "scene" 场景变化)
            
        Returns:
            关键帧列表
        """
        try:
            import cv2
            
            video_path = str(video)
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return []
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames == 0:
                return []
            
            # 计算要提取的帧位置
            if method == "uniform":
                frame_indices = [
                    int(i * total_frames / (num_frames + 1))
                    for i in range(1, num_frames + 1)
                ]
            else:
                # 场景检测方法（简化版）
                frame_indices = self._detect_scene_changes(cap, num_frames)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置位置
            
            frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # 转换为JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    
                    frames.append(VideoFrame(
                        timestamp=idx / fps,
                        image_data=buffer.tobytes()
                    ))
            
            cap.release()
            
            # 为关键帧添加描述
            self._describe_frames(frames)
            
            return frames
            
        except ImportError:
            logger.error("OpenCV (cv2) is required for frame extraction")
            return []
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            return []
    
    def _detect_scene_changes(self, cap, num_scenes: int) -> List[int]:
        """检测场景变化点"""
        import cv2
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 简化：使用直方图差异检测场景变化
        diffs = []
        prev_hist = None
        
        # 采样检测
        sample_rate = max(1, total_frames // 100)
        
        for i in range(0, total_frames, sample_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # 计算直方图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            if prev_hist is not None:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                diffs.append((i, 1 - diff))  # 差异越大值越大
            
            prev_hist = hist
        
        # 选择差异最大的位置
        diffs.sort(key=lambda x: x[1], reverse=True)
        scene_frames = [d[0] for d in diffs[:num_scenes]]
        scene_frames.sort()
        
        return scene_frames if scene_frames else [total_frames // 2]
    
    def _describe_frames(self, frames: List[VideoFrame]):
        """为帧添加描述"""
        try:
            from .image import ImageProcessor
            
            image_processor = ImageProcessor(str(self.workspace))
            
            for frame in frames:
                try:
                    result = image_processor.analyze(
                        frame.image_data,
                        "简要描述这个视频帧的内容（20字以内）"
                    )
                    frame.description = result.description
                except Exception as e:
                    logger.warning(f"Failed to describe frame: {e}")
                    frame.description = f"帧 @{frame.timestamp:.1f}s"
                    
        except ImportError:
            for frame in frames:
                frame.description = f"帧 @{frame.timestamp:.1f}s"
    
    def transcribe_audio(self, video: Union[str, Path]) -> str:
        """
        转录视频音频
        
        Args:
            video: 视频文件路径
            
        Returns:
            音频转录文本
        """
        try:
            # 提取音频
            audio_path = self._extract_audio(video)
            
            if not audio_path:
                return ""
            
            # 使用音频处理器转录
            from .audio import AudioProcessor
            
            audio_processor = AudioProcessor(str(self.workspace))
            result = audio_processor.transcribe(audio_path)
            
            # 清理临时文件
            Path(audio_path).unlink(missing_ok=True)
            
            return result.text
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return ""
    
    def _extract_audio(self, video: Union[str, Path]) -> Optional[str]:
        """从视频提取音频"""
        try:
            from moviepy.editor import VideoFileClip
            
            video_path = str(video)
            audio_path = str(self.workspace / f"temp_audio_{datetime.now().timestamp()}.mp3")
            
            clip = VideoFileClip(video_path)
            if clip.audio is not None:
                clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
                clip.close()
                return audio_path
            
            clip.close()
            return None
            
        except ImportError:
            logger.warning("moviepy is required for audio extraction")
            return None
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None
    
    def _generate_summary(self, result: VideoAnalysisResult) -> str:
        """生成视频摘要"""
        try:
            import litellm
            
            # 构建摘要提示
            prompt_parts = [
                f"这是一个时长 {result.duration:.1f} 秒的视频。",
                f"分辨率: {result.resolution[0]}x{result.resolution[1]}"
            ]
            
            if result.key_frames:
                prompt_parts.append("\n关键帧描述:")
                for i, frame in enumerate(result.key_frames, 1):
                    prompt_parts.append(f"{i}. [{frame.timestamp:.1f}s] {frame.description}")
            
            if result.transcript:
                prompt_parts.append(f"\n音频内容:\n{result.transcript[:500]}...")
            
            prompt_parts.append("\n请根据以上信息，生成一段简洁的视频摘要（100字以内）。")
            
            response = litellm.completion(
                model=self.default_model,
                messages=[
                    {"role": "user", "content": "\n".join(prompt_parts)}
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"视频时长 {result.duration:.1f} 秒"
    
    # ========================
    # 视频编辑
    # ========================
    
    def trim(
        self,
        video: Union[str, Path],
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None
    ) -> Path:
        """
        裁剪视频
        
        Args:
            video: 视频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_path: 输出路径
            
        Returns:
            输出文件路径
        """
        try:
            from moviepy.editor import VideoFileClip
            
            video_path = str(video)
            
            if output_path is None:
                output_path = str(
                    self.workspace / f"trimmed_{datetime.now().timestamp()}.mp4"
                )
            
            clip = VideoFileClip(video_path)
            trimmed = clip.subclip(start_time, end_time)
            trimmed.write_videofile(output_path, verbose=False, logger=None)
            
            clip.close()
            trimmed.close()
            
            return Path(output_path)
            
        except ImportError:
            raise RuntimeError("moviepy is required for video trimming")
    
    def extract_frame_at(
        self,
        video: Union[str, Path],
        timestamp: float
    ) -> bytes:
        """
        提取指定时间的帧
        
        Args:
            video: 视频文件路径
            timestamp: 时间点（秒）
            
        Returns:
            帧图像数据
        """
        try:
            import cv2
            
            video_path = str(video)
            cap = cv2.VideoCapture(video_path)
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_idx = int(timestamp * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                return buffer.tobytes()
            
            return b""
            
        except ImportError:
            raise RuntimeError("OpenCV (cv2) is required for frame extraction")
    
    def create_gif(
        self,
        video: Union[str, Path],
        start_time: float = 0,
        duration: float = 5,
        fps: int = 10,
        width: int = 480,
        output_path: Optional[str] = None
    ) -> Path:
        """
        从视频创建GIF
        
        Args:
            video: 视频文件路径
            start_time: 开始时间（秒）
            duration: 时长（秒）
            fps: GIF帧率
            width: GIF宽度
            output_path: 输出路径
            
        Returns:
            GIF文件路径
        """
        try:
            from moviepy.editor import VideoFileClip
            
            video_path = str(video)
            
            if output_path is None:
                output_path = str(
                    self.workspace / f"gif_{datetime.now().timestamp()}.gif"
                )
            
            clip = VideoFileClip(video_path)
            
            # 裁剪时间段
            end_time = min(start_time + duration, clip.duration)
            subclip = clip.subclip(start_time, end_time)
            
            # 调整大小
            if width > 0:
                subclip = subclip.resize(width=width)
            
            # 写入GIF
            subclip.write_gif(output_path, fps=fps, verbose=False, logger=None)
            
            clip.close()
            subclip.close()
            
            return Path(output_path)
            
        except ImportError:
            raise RuntimeError("moviepy is required for GIF creation")
    
    # ========================
    # 视频理解
    # ========================
    
    def answer_question(
        self,
        video: Union[str, Path],
        question: str,
        num_frames: int = 5
    ) -> str:
        """
        回答关于视频的问题
        
        Args:
            video: 视频文件路径
            question: 问题
            num_frames: 用于分析的帧数
            
        Returns:
            回答
        """
        try:
            import litellm
            
            # 提取关键帧
            frames = self.extract_key_frames(video, num_frames)
            
            if not frames:
                return "无法提取视频帧"
            
            # 获取音频转录
            transcript = self.transcribe_audio(video)
            
            # 构建消息
            content = [
                {"type": "text", "text": f"这是一个视频的关键帧。问题: {question}"}
            ]
            
            # 添加帧图像
            for frame in frames[:4]:  # 最多4帧
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame.to_base64()}"
                    }
                })
            
            if transcript:
                content.append({
                    "type": "text",
                    "text": f"\n视频音频内容: {transcript[:500]}"
                })
            
            response = litellm.completion(
                model=self.default_model,
                messages=[
                    {"role": "user", "content": content}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Video QA failed: {e}")
            return f"回答失败: {str(e)}"

