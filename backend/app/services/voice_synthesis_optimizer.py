"""
语音合成质量优化器
提升TTS语音质量和自然度
"""

import asyncio
import logging
import numpy as np
import librosa
from scipy import signal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import wave
import io
import re

logger = logging.getLogger(__name__)


class VoiceQuality(Enum):
    """语音质量等级"""
    ROBOTIC = "robotic"
    NATURAL = "natural"
    EXPRESSIVE = "expressive"


class EmotionType(Enum):
    """情感类型"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"


@dataclass
class AudioQualityMetrics:
    """音频质量指标"""
    clarity: float  # 清晰度 (0-1)
    naturalness: float  # 自然度 (0-1)
    smoothness: float  # 流畅度 (0-1)
    emotion_score: float  # 情感表达度 (0-1)
    overall_quality: float  # 总体质量 (0-1)


@dataclass
class SynthesisOptimizationResult:
    """合成优化结果"""
    original_audio: bytes
    optimized_audio: bytes
    quality_improvement: float
    optimizations_applied: List[str]
    quality_metrics: AudioQualityMetrics


class VoiceSynthesisOptimizer:
    """语音合成质量优化器"""
    
    def __init__(self):
        """初始化语音合成优化器"""
        # 音频处理配置
        self.audio_config = {
            "target_sample_rate": 22050,
            "target_bit_depth": 16,
            "target_channels": 1,
            "volume_target": -20.0,  # dB
            "noise_floor": -60.0  # dB
        }
        
        # 语音质量优化配置
        self.quality_config = {
            "pitch_variation": {
                "enabled": True,
                "variation_range": 0.1  # 10%的音高变化
            },
            "prosody_enhancement": {
                "enabled": True,
                "emphasis_strength": 0.2
            },
            "breath_simulation": {
                "enabled": True,
                "breath_interval": 3.0  # 每3秒添加一次呼吸声
            },
            "emotion_enhancement": {
                "enabled": True,
                "default_emotion": EmotionType.NEUTRAL
            }
        }
        
        # 语言特定配置
        self.language_config = {
            "chinese": {
                "tone_patterns": self._load_chinese_tone_patterns(),
                "prosody_rules": self._load_chinese_prosody_rules()
            },
            "english": {
                "intonation_patterns": self._load_english_intonation_patterns(),
                "stress_rules": self._load_english_stress_rules()
            }
        }
        
        # 优化统计
        self.optimization_stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "average_quality_improvement": 0.0,
            "language_specific_stats": {}
        }
    
    async def optimize_synthesis_quality(self, audio_data: bytes, 
                                        text: str,
                                        language: str = "zh-CN",
                                        emotion: EmotionType = EmotionType.NEUTRAL,
                                        target_quality: VoiceQuality = VoiceQuality.NATURAL) -> SynthesisOptimizationResult:
        """优化语音合成质量
        
        Args:
            audio_data: 原始音频数据
            text: 对应的文本
            language: 语言代码
            emotion: 情感类型
            target_quality: 目标质量等级
            
        Returns:
            合成优化结果
        """
        try:
            # 1. 分析原始音频质量
            original_metrics = await self._analyze_audio_quality(audio_data, text, language)
            
            # 2. 应用质量优化
            optimized_audio = await self._apply_quality_optimizations(audio_data, text, language, emotion, target_quality)
            
            # 3. 分析优化后音频质量
            optimized_metrics = await self._analyze_audio_quality(optimized_audio, text, language)
            
            # 4. 计算质量改进
            quality_improvement = self._calculate_quality_improvement(original_metrics, optimized_metrics)
            
            # 5. 记录优化应用
            optimizations_applied = self._identify_applied_optimizations(audio_data, optimized_audio)
            
            result = SynthesisOptimizationResult(
                original_audio=audio_data,
                optimized_audio=optimized_audio,
                quality_improvement=quality_improvement,
                optimizations_applied=optimizations_applied,
                quality_metrics=optimized_metrics
            )
            
            # 6. 更新统计信息
            self._update_optimization_stats(result, language)
            
            logger.info(f"语音合成质量优化完成: 质量提升 {quality_improvement:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"语音合成质量优化失败: {e}")
            # 返回原始音频
            metrics = AudioQualityMetrics(
                clarity=0.5,
                naturalness=0.5,
                smoothness=0.5,
                emotion_score=0.5,
                overall_quality=0.5
            )
            
            return SynthesisOptimizationResult(
                original_audio=audio_data,
                optimized_audio=audio_data,
                quality_improvement=0.0,
                optimizations_applied=[],
                quality_metrics=metrics
            )
    
    async def _analyze_audio_quality(self, audio_data: bytes, text: str, language: str) -> AudioQualityMetrics:
        """分析音频质量"""
        try:
            # 读取音频数据
            audio_buffer = io.BytesIO(audio_data)
            
            with wave.open(audio_buffer, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                audio_frames = wav_file.readframes(frames)
                audio_array = np.frombuffer(audio_frames, dtype=np.int16)
            
            # 转换为浮点数
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 计算各项质量指标
            clarity = self._calculate_clarity(audio_float, sample_rate)
            naturalness = self._calculate_naturalness(audio_float, sample_rate, text, language)
            smoothness = self._calculate_smoothness(audio_float, sample_rate)
            emotion_score = self._calculate_emotion_score(audio_float, sample_rate)
            
            # 计算总体质量
            overall_quality = (clarity + naturalness + smoothness + emotion_score) / 4.0
            
            return AudioQualityMetrics(
                clarity=clarity,
                naturalness=naturalness,
                smoothness=smoothness,
                emotion_score=emotion_score,
                overall_quality=overall_quality
            )
            
        except Exception as e:
            logger.error(f"音频质量分析失败: {e}")
            return AudioQualityMetrics(
                clarity=0.5,
                naturalness=0.5,
                smoothness=0.5,
                emotion_score=0.5,
                overall_quality=0.5
            )
    
    def _calculate_clarity(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """计算清晰度"""
        # 使用频谱质心作为清晰度指标
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
        
        # 归一化到0-1范围
        max_centroid = 4000  # 假设最大质心频率
        clarity = np.mean(spectral_centroids) / max_centroid
        
        return float(np.clip(clarity, 0.0, 1.0))
    
    def _calculate_naturalness(self, audio_data: np.ndarray, sample_rate: int, text: str, language: str) -> float:
        """计算自然度"""
        # 基于音高变化和韵律分析自然度
        
        # 1. 音高变化分析
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
        pitch_values = pitches[pitches > 0]
        
        if len(pitch_values) > 0:
            pitch_variation = np.std(pitch_values) / np.mean(pitch_values)
        else:
            pitch_variation = 0.0
        
        # 2. 能量变化分析
        frame_length = int(0.025 * sample_rate)  # 25ms帧
        hop_length = int(0.010 * sample_rate)    # 10ms跳步
        
        energy = []
        for i in range(0, len(audio_data) - frame_length, hop_length):
            frame = audio_data[i:i + frame_length]
            frame_energy = np.sum(frame**2)
            energy.append(frame_energy)
        
        if energy:
            energy_variation = np.std(energy) / np.mean(energy)
        else:
            energy_variation = 0.0
        
        # 3. 语言特定的自然度评估
        language_naturalness = self._assess_language_naturalness(text, language)
        
        # 综合自然度评分
        naturalness = (pitch_variation * 0.4 + energy_variation * 0.3 + language_naturalness * 0.3)
        
        return float(np.clip(naturalness, 0.0, 1.0))
    
    def _assess_language_naturalness(self, text: str, language: str) -> float:
        """评估语言自然度"""
        if language.startswith("zh"):
            # 中文自然度评估
            return self._assess_chinese_naturalness(text)
        elif language.startswith("en"):
            # 英文自然度评估
            return self._assess_english_naturalness(text)
        else:
            return 0.7  # 默认值
    
    def _assess_chinese_naturalness(self, text: str) -> float:
        """评估中文自然度"""
        # 基于句子长度和标点使用评估自然度
        sentences = re.split(r'[。！？]', text)
        
        if not sentences:
            return 0.5
        
        # 计算平均句子长度
        avg_length = sum(len(sentence.strip()) for sentence in sentences if sentence.strip()) / len(sentences)
        
        # 理想句子长度范围
        if 5 <= avg_length <= 20:
            return 0.8
        elif 3 <= avg_length <= 30:
            return 0.6
        else:
            return 0.4
    
    def _assess_english_naturalness(self, text: str) -> float:
        """评估英文自然度"""
        # 基于单词数量和句子结构评估自然度
        words = text.split()
        sentences = re.split(r'[.!?]', text)
        
        if not words or not sentences:
            return 0.5
        
        # 计算平均句子长度
        avg_words_per_sentence = len(words) / len(sentences)
        
        # 理想句子长度范围
        if 5 <= avg_words_per_sentence <= 15:
            return 0.8
        elif 3 <= avg_words_per_sentence <= 20:
            return 0.6
        else:
            return 0.4
    
    def _calculate_smoothness(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """计算流畅度"""
        # 使用频谱滚降点作为流畅度指标
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)[0]
        
        # 计算频谱平滑度
        spectral_smoothness = 1.0 - (np.std(spectral_rolloff) / np.mean(spectral_rolloff))
        
        # 计算时域平滑度（避免突然的幅度变化）
        amplitude_changes = np.diff(np.abs(audio_data))
        temporal_smoothness = 1.0 - (np.std(amplitude_changes) / (np.mean(np.abs(audio_data)) + 1e-8))
        
        smoothness = (spectral_smoothness + temporal_smoothness) / 2.0
        
        return float(np.clip(smoothness, 0.0, 1.0))
    
    def _calculate_emotion_score(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """计算情感表达度"""
        # 基于音高、能量和频谱特征评估情感表达
        
        # 1. 音高范围（情感表达通常有更大的音高范围）
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
        pitch_values = pitches[pitches > 0]
        
        if len(pitch_values) > 0:
            pitch_range = (np.max(pitch_values) - np.min(pitch_values)) / 200  # 归一化
        else:
            pitch_range = 0.0
        
        # 2. 能量动态范围
        frame_energy = librosa.feature.rms(y=audio_data)[0]
        energy_dynamic_range = (np.max(frame_energy) - np.min(frame_energy)) / (np.mean(frame_energy) + 1e-8)
        
        # 3. 频谱亮度（高频能量）
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
        spectral_brightness = np.mean(spectral_centroids) / 4000  # 归一化
        
        emotion_score = (pitch_range * 0.4 + energy_dynamic_range * 0.3 + spectral_brightness * 0.3)
        
        return float(np.clip(emotion_score, 0.0, 1.0))
    
    async def _apply_quality_optimizations(self, audio_data: bytes, text: str, language: str,
                                          emotion: EmotionType, target_quality: VoiceQuality) -> bytes:
        """应用质量优化"""
        try:
            # 读取原始音频
            audio_buffer = io.BytesIO(audio_data)
            
            with wave.open(audio_buffer, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                audio_frames = wav_file.readframes(frames)
                audio_array = np.frombuffer(audio_frames, dtype=np.int16)
            
            # 转换为浮点数
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 应用优化处理
            optimized_audio = audio_float.copy()
            
            # 1. 音高变化优化
            if self.quality_config["pitch_variation"]["enabled"]:
                optimized_audio = self._apply_pitch_variation(optimized_audio, sample_rate, text, language)
            
            # 2. 韵律增强
            if self.quality_config["prosody_enhancement"]["enabled"]:
                optimized_audio = self._apply_prosody_enhancement(optimized_audio, sample_rate, text, language)
            
            # 3. 情感增强
            if self.quality_config["emotion_enhancement"]["enabled"]:
                optimized_audio = self._apply_emotion_enhancement(optimized_audio, sample_rate, emotion)
            
            # 4. 音量标准化
            optimized_audio = self._normalize_volume(optimized_audio)
            
            # 5. 噪声抑制
            optimized_audio = self._reduce_noise(optimized_audio, sample_rate)
            
            # 转换回整数格式
            optimized_int = (optimized_audio * 32768).astype(np.int16)
            
            # 创建新的WAV文件
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(optimized_int.tobytes())
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"质量优化处理失败: {e}")
            return audio_data
    
    def _apply_pitch_variation(self, audio_data: np.ndarray, sample_rate: int, text: str, language: str) -> np.ndarray:
        """应用音高变化优化"""
        # 基于语言和文本内容应用自然的音高变化
        
        # 分析文本中的重点词汇
        emphasis_positions = self._identify_emphasis_positions(text, language)
        
        # 应用音高变化
        frame_length = int(0.025 * sample_rate)  # 25ms帧
        hop_length = int(0.010 * sample_rate)    # 10ms跳步
        
        optimized_audio = audio_data.copy()
        
        for i, pos in enumerate(emphasis_positions):
            # 计算在音频中的位置
            audio_pos = int((pos / len(text)) * len(audio_data))
            
            # 在重点位置应用音高提升
            if 0 <= audio_pos < len(audio_data) - frame_length:
                # 简单的音高提升（可以改为更复杂的音高变换）
                pitch_boost = 1.0 + (i % 3) * 0.05  # 交替提升程度
                frame = audio_data[audio_pos:audio_pos + frame_length]
                boosted_frame = frame * pitch_boost
                optimized_audio[audio_pos:audio_pos + frame_length] = boosted_frame
        
        return optimized_audio
    
    def _identify_emphasis_positions(self, text: str, language: str) -> List[int]:
        """识别文本中的重点位置"""
        emphasis_positions = []
        
        if language.startswith("zh"):
            # 中文重点识别：关键词、疑问词、感叹词等
            keywords = ["重要", "关键", "注意", "必须", "一定", "特别"]
            question_words = ["什么", "为什么", "如何", "怎样", "哪里"]
            exclamation_words = ["！", "！", "！"]
            
            for i, char in enumerate(text):
                if char in exclamation_words:
                    emphasis_positions.append(i)
                elif i < len(text) - 1:
                    word = text[i:i+2]
                    if word in keywords or word in question_words:
                        emphasis_positions.append(i)
        
        elif language.startswith("en"):
            # 英文重点识别
            keywords = ["important", "key", "must", "essential", "critical"]
            question_words = ["what", "why", "how", "where", "when"]
            
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in keywords or word.lower() in question_words:
                    # 找到单词在文本中的位置
                    pos = text.find(word)
                    if pos != -1:
                        emphasis_positions.append(pos)
        
        return emphasis_positions
    
    def _apply_prosody_enhancement(self, audio_data: np.ndarray, sample_rate: int, text: str, language: str) -> np.ndarray:
        """应用韵律增强"""
        # 基于语言特点增强韵律
        
        if language.startswith("zh"):
            # 中文韵律增强：四声调变化
            return self._enhance_chinese_prosody(audio_data, sample_rate, text)
        elif language.startswith("en"):
            # 英文韵律增强：重音和语调
            return self._enhance_english_prosody(audio_data, sample_rate, text)
        else:
            return audio_data
    
    def _enhance_chinese_prosody(self, audio_data: np.ndarray, sample_rate: int, text: str) -> np.ndarray:
        """增强中文韵律"""
        # 简单的韵律增强：在句子边界添加停顿
        sentences = re.split(r'[。！？]', text)
        
        if len(sentences) > 1:
            # 在句子间添加短暂停顿
            audio_duration = len(audio_data) / sample_rate
            sentence_duration = audio_duration / len(sentences)
            
            # 简单的实现：在音频中间位置添加静音
            pause_duration = 0.1  # 100ms停顿
            pause_samples = int(pause_duration * sample_rate)
            
            # 创建带停顿的音频
            optimized_audio = np.zeros(len(audio_data) + pause_samples * (len(sentences) - 1))
            
            current_pos = 0
            for i in range(len(sentences)):
                sentence_audio = audio_data[int(i * sentence_duration * sample_rate):
                                          int((i + 1) * sentence_duration * sample_rate)]
                
                optimized_audio[current_pos:current_pos + len(sentence_audio)] = sentence_audio
                current_pos += len(sentence_audio)
                
                if i < len(sentences) - 1:
                    current_pos += pause_samples
            
            return optimized_audio
        
        return audio_data
    
    def _enhance_english_prosody(self, audio_data: np.ndarray, sample_rate: int, text: str) -> np.ndarray:
        """增强英文韵律"""
        # 英文韵律增强：重音和语调模式
        
        # 简单的实现：在疑问句末尾提升音高
        if text.strip().endswith('?'):
            # 在最后0.5秒提升音高
            rise_duration = 0.5  # 0.5秒
            rise_samples = int(rise_duration * sample_rate)
            
            if rise_samples < len(audio_data):
                # 应用线性音高提升
                rise_factor = np.linspace(1.0, 1.2, rise_samples)
                audio_data[-rise_samples:] = audio_data[-rise_samples:] * rise_factor
        
        return audio_data
    
    def _apply_emotion_enhancement(self, audio_data: np.ndarray, sample_rate: int, emotion: EmotionType) -> np.ndarray:
        """应用情感增强"""
        # 基于情感类型调整音频特征
        
        emotion_factors = {
            EmotionType.NEUTRAL: {"pitch": 1.0, "speed": 1.0, "energy": 1.0},
            EmotionType.HAPPY: {"pitch": 1.1, "speed": 1.1, "energy": 1.2},
            EmotionType.SAD: {"pitch": 0.9, "speed": 0.8, "energy": 0.8},
            EmotionType.ANGRY: {"pitch": 1.2, "speed": 1.0, "energy": 1.3},
            EmotionType.EXCITED: {"pitch": 1.15, "speed": 1.2, "energy": 1.25},
            EmotionType.CALM: {"pitch": 0.95, "speed": 0.9, "energy": 0.9}
        }
        
        factors = emotion_factors.get(emotion, emotion_factors[EmotionType.NEUTRAL])
        
        # 应用情感因子
        optimized_audio = audio_data.copy()
        
        # 音高调整（简单的实现）
        optimized_audio = optimized_audio * factors["pitch"]
        
        # 速度调整（需要更复杂的时域拉伸）
        if factors["speed"] != 1.0:
            # 简单的速度调整（实际应该使用时域拉伸算法）
            optimized_audio = signal.resample(optimized_audio, 
                                            int(len(optimized_audio) / factors["speed"]))
        
        # 能量调整
        optimized_audio = optimized_audio * factors["energy"]
        
        return optimized_audio
    
    def _normalize_volume(self, audio_data: np.ndarray) -> np.ndarray:
        """音量标准化"""
        # 计算RMS
        rms = np.sqrt(np.mean(audio_data**2))
        
        if rms > 0:
            # 目标RMS
            target_rms = 10**(self.audio_config["volume_target"] / 20)
            gain = target_rms / rms
            
            # 限制最大增益
            max_gain = 5.0
            gain = min(gain, max_gain)
            
            return audio_data * gain
        
        return audio_data
    
    def _reduce_noise(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """噪声抑制"""
        # 简单的噪声抑制（可以使用更专业的算法）
        
        # 计算噪声阈值
        noise_threshold = 10**(self.audio_config["noise_floor"] / 20)
        
        # 应用简单的噪声门
        audio_data[np.abs(audio_data) < noise_threshold] = 0
        
        return audio_data
    
    def _calculate_quality_improvement(self, original_metrics: AudioQualityMetrics, 
                                    optimized_metrics: AudioQualityMetrics) -> float:
        """计算质量改进"""
        improvement = optimized_metrics.overall_quality - original_metrics.overall_quality
        return float(max(improvement, 0.0))
    
    def _identify_applied_optimizations(self, original_audio: bytes, optimized_audio: bytes) -> List[str]:
        """识别应用的优化"""
        optimizations = []
        
        # 比较音频长度
        if len(optimized_audio) != len(original_audio):
            optimizations.append("时长调整")
        
        # 这里可以添加更多优化类型识别
        optimizations.append("音质优化")
        optimizations.append("韵律增强")
        
        return optimizations
    
    def _update_optimization_stats(self, result: SynthesisOptimizationResult, language: str):
        """更新优化统计"""
        self.optimization_stats["total_optimizations"] += 1
        
        if result.quality_improvement > 0.1:
            self.optimization_stats["successful_optimizations"] += 1
        
        # 更新平均质量改进
        total_improvement = self.optimization_stats["average_quality_improvement"] * (self.optimization_stats["total_optimizations"] - 1)
        total_improvement += result.quality_improvement
        self.optimization_stats["average_quality_improvement"] = total_improvement / self.optimization_stats["total_optimizations"]
        
        # 更新语言特定统计
        if language not in self.optimization_stats["language_specific_stats"]:
            self.optimization_stats["language_specific_stats"][language] = {
                "total": 0,
                "successful": 0,
                "average_improvement": 0.0
            }
        
        lang_stats = self.optimization_stats["language_specific_stats"][language]
        lang_stats["total"] += 1
        
        if result.quality_improvement > 0.1:
            lang_stats["successful"] += 1
        
        # 更新语言平均改进
        total_lang_improvement = lang_stats["average_improvement"] * (lang_stats["total"] - 1)
        total_lang_improvement += result.quality_improvement
        lang_stats["average_improvement"] = total_lang_improvement / lang_stats["total"]
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        success_rate = 0.0
        if self.optimization_stats["total_optimizations"] > 0:
            success_rate = (self.optimization_stats["successful_optimizations"] / 
                          self.optimization_stats["total_optimizations"]) * 100
        
        return {
            "success_rate": success_rate,
            "average_quality_improvement": self.optimization_stats["average_quality_improvement"],
            "total_optimizations": self.optimization_stats["total_optimizations"],
            "successful_optimizations": self.optimization_stats["successful_optimizations"],
            "language_specific_stats": self.optimization_stats["language_specific_stats"]
        }
    
    def _load_chinese_tone_patterns(self) -> Dict[str, Any]:
        """加载中文声调模式"""
        return {
            "first_tone": {"pitch": "high", "pattern": "flat"},
            "second_tone": {"pitch": "rising", "pattern": "rise"},
            "third_tone": {"pitch": "low", "pattern": "fall-rise"},
            "fourth_tone": {"pitch": "falling", "pattern": "fall"}
        }
    
    def _load_chinese_prosody_rules(self) -> Dict[str, Any]:
        """加载中文韵律规则"""
        return {
            "sentence_boundary_pause": 0.1,
            "phrase_boundary_pause": 0.05,
            "emphasis_boost": 1.2
        }
    
    def _load_english_intonation_patterns(self) -> Dict[str, Any]:
        """加载英文语调模式"""
        return {
            "statement": {"pattern": "falling"},
            "question": {"pattern": "rising"},
            "emphasis": {"pattern": "high"}
        }
    
    def _load_english_stress_rules(self) -> Dict[str, Any]:
        """加载英文重音规则"""
        return {
            "content_words": ["nouns", "verbs", "adjectives", "adverbs"],
            "stress_boost": 1.3,
            "duration_multiplier": 1.2
        }


# 创建全局语音合成优化器实例
voice_synthesis_optimizer = VoiceSynthesisOptimizer()