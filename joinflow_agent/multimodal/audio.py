"""
Audio Processing Module
=======================

Audio processing capabilities:
- Speech-to-Text (Whisper)
- Text-to-Speech (TTS)
- Audio analysis
- Real-time voice interaction
"""

import base64
import io
import logging
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AudioFormat(str, Enum):
    """支持的音频格式"""
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    OGG = "ogg"
    FLAC = "flac"
    WEBM = "webm"


class TTSVoice(str, Enum):
    """TTS语音选项"""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


@dataclass
class TranscriptionResult:
    """语音转文字结果"""
    text: str = ""
    language: str = ""
    duration: float = 0.0
    segments: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "duration": self.duration,
            "segments": self.segments,
            "confidence": self.confidence
        }


@dataclass
class SpeechResult:
    """文字转语音结果"""
    audio_data: bytes = b""
    format: str = "mp3"
    duration: float = 0.0
    voice: str = "alloy"
    
    def save(self, path: str):
        """保存音频到文件"""
        Path(path).write_bytes(self.audio_data)
    
    def to_base64(self) -> str:
        """转换为base64"""
        return base64.b64encode(self.audio_data).decode()


class AudioProcessor:
    """
    音频处理器
    
    功能：
    - 语音转文字 (Speech-to-Text)
    - 文字转语音 (Text-to-Speech)
    - 音频分析
    - 实时语音交互
    """
    
    def __init__(
        self,
        workspace: str = "./workspace",
        default_stt_model: str = "whisper-1",
        default_tts_model: str = "tts-1"
    ):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.default_stt_model = default_stt_model
        self.default_tts_model = default_tts_model
    
    # ========================
    # 语音转文字 (STT)
    # ========================
    
    def transcribe(
        self,
        audio: Union[str, bytes, Path],
        language: Optional[str] = None,
        model: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> TranscriptionResult:
        """
        语音转文字
        
        Args:
            audio: 音频文件路径或字节数据
            language: 语言代码（如 "zh", "en"）
            model: 使用的模型
            prompt: 提示词（帮助识别特定词汇）
            
        Returns:
            TranscriptionResult: 转录结果
        """
        try:
            import litellm
            
            # 准备音频文件
            audio_path = self._prepare_audio(audio)
            
            # 调用API
            with open(audio_path, "rb") as audio_file:
                response = litellm.transcription(
                    model=model or self.default_stt_model,
                    file=audio_file,
                    language=language,
                    prompt=prompt
                )
            
            return TranscriptionResult(
                text=response.text,
                language=language or "auto",
                confidence=0.95
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return TranscriptionResult(
                text=f"转录失败: {str(e)}",
                confidence=0.0
            )
    
    def transcribe_with_timestamps(
        self,
        audio: Union[str, bytes, Path],
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        带时间戳的语音转文字
        
        Args:
            audio: 音频数据
            language: 语言代码
            
        Returns:
            包含时间戳的转录结果
        """
        try:
            import litellm
            
            audio_path = self._prepare_audio(audio)
            
            with open(audio_path, "rb") as audio_file:
                response = litellm.transcription(
                    model=self.default_stt_model,
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            segments = []
            if hasattr(response, 'segments'):
                for seg in response.segments:
                    segments.append({
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "")
                    })
            
            return TranscriptionResult(
                text=response.text,
                language=response.language if hasattr(response, 'language') else "",
                duration=response.duration if hasattr(response, 'duration') else 0,
                segments=segments,
                confidence=0.95
            )
            
        except Exception as e:
            logger.error(f"Transcription with timestamps failed: {e}")
            return TranscriptionResult(
                text=f"转录失败: {str(e)}",
                confidence=0.0
            )
    
    # ========================
    # 文字转语音 (TTS)
    # ========================
    
    def synthesize(
        self,
        text: str,
        voice: Union[str, TTSVoice] = TTSVoice.ALLOY,
        model: Optional[str] = None,
        speed: float = 1.0
    ) -> SpeechResult:
        """
        文字转语音
        
        Args:
            text: 要转换的文字
            voice: 语音选项
            model: 使用的模型
            speed: 语速 (0.25 - 4.0)
            
        Returns:
            SpeechResult: 语音结果
        """
        try:
            import litellm
            
            if isinstance(voice, TTSVoice):
                voice = voice.value
            
            response = litellm.speech(
                model=model or self.default_tts_model,
                input=text,
                voice=voice,
                speed=speed
            )
            
            # 获取音频数据
            audio_data = response.content if hasattr(response, 'content') else response
            
            return SpeechResult(
                audio_data=audio_data,
                format="mp3",
                voice=voice
            )
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: Union[str, TTSVoice] = TTSVoice.ALLOY,
        speed: float = 1.0
    ) -> Path:
        """
        文字转语音并保存到文件
        
        Args:
            text: 要转换的文字
            output_path: 输出文件路径
            voice: 语音选项
            speed: 语速
            
        Returns:
            保存的文件路径
        """
        result = self.synthesize(text, voice, speed=speed)
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        result.save(str(path))
        
        return path
    
    # ========================
    # 音频分析
    # ========================
    
    def get_duration(self, audio: Union[str, bytes, Path]) -> float:
        """
        获取音频时长
        
        Args:
            audio: 音频数据
            
        Returns:
            时长（秒）
        """
        try:
            from pydub import AudioSegment
            
            audio_path = self._prepare_audio(audio)
            audio_segment = AudioSegment.from_file(audio_path)
            
            return len(audio_segment) / 1000.0  # 转换为秒
            
        except ImportError:
            logger.warning("pydub not installed, cannot get duration")
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 0.0
    
    def get_info(self, audio: Union[str, bytes, Path]) -> Dict[str, Any]:
        """
        获取音频信息
        
        Args:
            audio: 音频数据
            
        Returns:
            音频信息字典
        """
        try:
            from pydub import AudioSegment
            
            audio_path = self._prepare_audio(audio)
            audio_segment = AudioSegment.from_file(audio_path)
            
            return {
                "duration": len(audio_segment) / 1000.0,
                "channels": audio_segment.channels,
                "sample_width": audio_segment.sample_width,
                "frame_rate": audio_segment.frame_rate,
                "frame_width": audio_segment.frame_width
            }
            
        except ImportError:
            return {"error": "pydub not installed"}
        except Exception as e:
            return {"error": str(e)}
    
    # ========================
    # 音频转换
    # ========================
    
    def convert_format(
        self,
        audio: Union[str, bytes, Path],
        target_format: AudioFormat
    ) -> bytes:
        """
        转换音频格式
        
        Args:
            audio: 音频数据
            target_format: 目标格式
            
        Returns:
            转换后的音频字节数据
        """
        try:
            from pydub import AudioSegment
            
            audio_path = self._prepare_audio(audio)
            audio_segment = AudioSegment.from_file(audio_path)
            
            buffer = io.BytesIO()
            audio_segment.export(buffer, format=target_format.value)
            return buffer.getvalue()
            
        except ImportError:
            raise RuntimeError("pydub is required for audio conversion")
    
    def trim(
        self,
        audio: Union[str, bytes, Path],
        start_ms: int = 0,
        end_ms: Optional[int] = None
    ) -> bytes:
        """
        裁剪音频
        
        Args:
            audio: 音频数据
            start_ms: 开始时间（毫秒）
            end_ms: 结束时间（毫秒），None表示到结尾
            
        Returns:
            裁剪后的音频字节数据
        """
        try:
            from pydub import AudioSegment
            
            audio_path = self._prepare_audio(audio)
            audio_segment = AudioSegment.from_file(audio_path)
            
            if end_ms is None:
                trimmed = audio_segment[start_ms:]
            else:
                trimmed = audio_segment[start_ms:end_ms]
            
            buffer = io.BytesIO()
            trimmed.export(buffer, format="mp3")
            return buffer.getvalue()
            
        except ImportError:
            raise RuntimeError("pydub is required for audio trimming")
    
    def merge(
        self,
        audio_files: List[Union[str, bytes, Path]],
        crossfade_ms: int = 0
    ) -> bytes:
        """
        合并多个音频文件
        
        Args:
            audio_files: 音频文件列表
            crossfade_ms: 交叉淡入淡出时长（毫秒）
            
        Returns:
            合并后的音频字节数据
        """
        try:
            from pydub import AudioSegment
            
            if not audio_files:
                return b""
            
            # 加载第一个音频
            first_path = self._prepare_audio(audio_files[0])
            combined = AudioSegment.from_file(first_path)
            
            # 合并其余音频
            for audio in audio_files[1:]:
                audio_path = self._prepare_audio(audio)
                segment = AudioSegment.from_file(audio_path)
                
                if crossfade_ms > 0:
                    combined = combined.append(segment, crossfade=crossfade_ms)
                else:
                    combined += segment
            
            buffer = io.BytesIO()
            combined.export(buffer, format="mp3")
            return buffer.getvalue()
            
        except ImportError:
            raise RuntimeError("pydub is required for audio merging")
    
    # ========================
    # 实时语音交互
    # ========================
    
    def create_realtime_session(self) -> "RealtimeAudioSession":
        """
        创建实时语音会话
        
        Returns:
            RealtimeAudioSession: 实时会话对象
        """
        return RealtimeAudioSession(self)
    
    # ========================
    # 辅助方法
    # ========================
    
    def _prepare_audio(self, audio: Union[str, bytes, Path]) -> str:
        """
        准备音频文件
        
        Returns:
            音频文件路径
        """
        if isinstance(audio, (str, Path)):
            path = Path(audio)
            if path.exists():
                return str(path)
            # 可能是base64
            if isinstance(audio, str):
                data = base64.b64decode(audio)
                return self._save_temp_audio(data)
        elif isinstance(audio, bytes):
            return self._save_temp_audio(audio)
        
        raise ValueError(f"Unsupported audio type: {type(audio)}")
    
    def _save_temp_audio(self, data: bytes) -> str:
        """保存临时音频文件"""
        # 检测格式
        if data[:4] == b'RIFF':
            ext = '.wav'
        elif data[:3] == b'ID3' or data[:2] == b'\xff\xfb':
            ext = '.mp3'
        elif data[:4] == b'fLaC':
            ext = '.flac'
        else:
            ext = '.mp3'
        
        temp_file = tempfile.NamedTemporaryFile(
            suffix=ext,
            delete=False,
            dir=str(self.workspace)
        )
        temp_file.write(data)
        temp_file.close()
        
        return temp_file.name
    
    def save_audio(
        self,
        data: Union[str, bytes],
        filename: str
    ) -> Path:
        """
        保存音频到工作区
        
        Args:
            data: 音频数据（base64或字节）
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        if isinstance(data, str):
            data = base64.b64decode(data)
        
        path = self.workspace / filename
        path.write_bytes(data)
        return path


class RealtimeAudioSession:
    """
    实时音频会话
    
    支持：
    - 流式语音输入
    - 实时转录
    - 语音对话
    """
    
    def __init__(self, processor: AudioProcessor):
        self.processor = processor
        self.is_active = False
        self._buffer: List[bytes] = []
        self._transcription_callback = None
    
    def start(self, on_transcription=None):
        """开始会话"""
        self.is_active = True
        self._transcription_callback = on_transcription
        logger.info("Realtime audio session started")
    
    def stop(self):
        """停止会话"""
        self.is_active = False
        self._buffer.clear()
        logger.info("Realtime audio session stopped")
    
    def add_audio_chunk(self, chunk: bytes):
        """添加音频块"""
        if not self.is_active:
            return
        
        self._buffer.append(chunk)
        
        # 当缓冲区足够大时进行转录
        if len(self._buffer) >= 10:  # 约1秒的音频
            self._process_buffer()
    
    def _process_buffer(self):
        """处理缓冲区"""
        if not self._buffer:
            return
        
        # 合并音频块
        audio_data = b''.join(self._buffer)
        self._buffer.clear()
        
        # 转录
        try:
            result = self.processor.transcribe(audio_data)
            if self._transcription_callback and result.text:
                self._transcription_callback(result.text)
        except Exception as e:
            logger.error(f"Realtime transcription error: {e}")
    
    def get_response(self, text: str) -> SpeechResult:
        """
        获取语音响应
        
        Args:
            text: 要转换为语音的文字
            
        Returns:
            SpeechResult: 语音结果
        """
        return self.processor.synthesize(text)

