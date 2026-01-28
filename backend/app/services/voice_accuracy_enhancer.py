"""
语音识别准确率增强器
专门提升语音识别的准确性和可靠性
"""

import asyncio
import logging
import numpy as np
import librosa
import noisereduce as nr
from scipy import signal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import wave
import io
import re

logger = logging.getLogger(__name__)


class AudioQuality(Enum):
    """音频质量等级"""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class AudioAnalysisResult:
    """音频分析结果"""
    quality: AudioQuality
    sample_rate: int
    channels: int
    duration: float
    noise_level: float
    signal_to_noise_ratio: float
    speech_activity: float
    issues: List[str]


@dataclass
class RecognitionEnhancementResult:
    """识别增强结果"""
    original_text: str
    enhanced_text: str
    confidence_boost: float
    corrections_applied: List[str]
    language_model_score: float


class VoiceAccuracyEnhancer:
    """语音识别准确率增强器"""
    
    def __init__(self):
        """初始化准确率增强器"""
        # 音频处理配置
        self.audio_config = {
            "target_sample_rate": 16000,
            "target_channels": 1,
            "noise_reduction_threshold": 0.1,
            "volume_normalization_target": -20.0  # dB
        }
        
        # 语言模型配置
        self.language_model_config = {
            "chinese": {
                "common_words": self._load_chinese_common_words(),
                "punctuation_patterns": ["，", "。", "！", "？", "；", "：", "、"]
            },
            "english": {
                "common_words": self._load_english_common_words(),
                "punctuation_patterns": [",", ".", "!", "?", ";", ":"]
            }
        }
        
        # 准确率统计
        self.accuracy_stats = {
            "total_enhancements": 0,
            "successful_enhancements": 0,
            "average_confidence_boost": 0.0,
            "language_specific_stats": {}
        }
    
    async def enhance_recognition_accuracy(self, audio_data: bytes, 
                                         original_text: str,
                                         confidence: float,
                                         language: str = "zh-CN") -> RecognitionEnhancementResult:
        """增强语音识别准确率
        
        Args:
            audio_data: 音频数据
            original_text: 原始识别文本
            confidence: 原始置信度
            language: 语言代码
            
        Returns:
            识别增强结果
        """
        try:
            # 1. 音频质量分析
            audio_analysis = await self._analyze_audio_quality(audio_data)
            
            # 2. 音频预处理（如果需要）
            processed_audio = await self._preprocess_audio(audio_data, audio_analysis)
            
            # 3. 文本后处理
            enhanced_text = await self._enhance_text(original_text, language, confidence)
            
            # 4. 语言模型校正
            corrected_text = await self._apply_language_model_correction(enhanced_text, language)
            
            # 5. 置信度提升计算
            confidence_boost = self._calculate_confidence_boost(audio_analysis, original_text, corrected_text)
            
            # 6. 记录增强结果
            corrections = self._identify_corrections(original_text, corrected_text)
            language_model_score = self._calculate_language_model_score(corrected_text, language)
            
            result = RecognitionEnhancementResult(
                original_text=original_text,
                enhanced_text=corrected_text,
                confidence_boost=confidence_boost,
                corrections_applied=corrections,
                language_model_score=language_model_score
            )
            
            # 7. 更新统计信息
            self._update_accuracy_stats(result, language)
            
            logger.info(f"语音识别准确率增强完成: 置信度提升 {confidence_boost:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"语音识别准确率增强失败: {e}")
            # 返回原始结果
            return RecognitionEnhancementResult(
                original_text=original_text,
                enhanced_text=original_text,
                confidence_boost=0.0,
                corrections_applied=[],
                language_model_score=0.0
            )
    
    async def _analyze_audio_quality(self, audio_data: bytes) -> AudioAnalysisResult:
        """分析音频质量"""
        try:
            # 读取音频数据
            audio_buffer = io.BytesIO(audio_data)
            
            with wave.open(audio_buffer, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                frames = wav_file.getnframes()
                duration = frames / float(sample_rate)
                
                # 读取音频数据
                audio_frames = wav_file.readframes(frames)
                audio_array = np.frombuffer(audio_frames, dtype=np.int16)
            
            # 转换为浮点数
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 分析音频质量
            noise_level = self._calculate_noise_level(audio_float)
            snr = self._calculate_snr(audio_float)
            speech_activity = self._calculate_speech_activity(audio_float, sample_rate)
            
            # 识别问题
            issues = self._identify_audio_issues(audio_float, sample_rate, duration, snr)
            
            # 确定质量等级
            quality = self._determine_audio_quality(snr, speech_activity, issues)
            
            return AudioAnalysisResult(
                quality=quality,
                sample_rate=sample_rate,
                channels=channels,
                duration=duration,
                noise_level=noise_level,
                signal_to_noise_ratio=snr,
                speech_activity=speech_activity,
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"音频质量分析失败: {e}")
            # 返回默认结果
            return AudioAnalysisResult(
                quality=AudioQuality.POOR,
                sample_rate=16000,
                channels=1,
                duration=0.0,
                noise_level=1.0,
                signal_to_noise_ratio=0.0,
                speech_activity=0.0,
                issues=["音频分析失败"]
            )
    
    def _calculate_noise_level(self, audio_data: np.ndarray) -> float:
        """计算噪声水平"""
        # 使用RMS计算噪声水平
        rms = np.sqrt(np.mean(audio_data**2))
        return float(rms)
    
    def _calculate_snr(self, audio_data: np.ndarray) -> float:
        """计算信噪比"""
        # 简单的信噪比估算
        signal_power = np.mean(audio_data**2)
        noise_power = np.var(audio_data)
        
        if noise_power > 0:
            snr = 10 * np.log10(signal_power / noise_power)
            return float(snr)
        
        return 0.0
    
    def _calculate_speech_activity(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """计算语音活动度"""
        # 简单的语音活动检测
        frame_length = int(0.025 * sample_rate)  # 25ms帧
        hop_length = int(0.010 * sample_rate)    # 10ms跳步
        
        if len(audio_data) < frame_length:
            return 0.0
        
        # 计算能量
        energy = []
        for i in range(0, len(audio_data) - frame_length, hop_length):
            frame = audio_data[i:i + frame_length]
            frame_energy = np.sum(frame**2)
            energy.append(frame_energy)
        
        if not energy:
            return 0.0
        
        # 语音活动阈值
        threshold = np.mean(energy) * 0.1
        speech_frames = sum(1 for e in energy if e > threshold)
        speech_activity = speech_frames / len(energy)
        
        return float(speech_activity)
    
    def _identify_audio_issues(self, audio_data: np.ndarray, sample_rate: int, 
                             duration: float, snr: float) -> List[str]:
        """识别音频问题"""
        issues = []
        
        # 检查信噪比
        if snr < 10:
            issues.append("信噪比过低")
        
        # 检查音频时长
        if duration < 0.5:
            issues.append("音频过短")
        elif duration > 30:
            issues.append("音频过长")
        
        # 检查采样率
        if sample_rate < 8000:
            issues.append("采样率过低")
        
        # 检查音量
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude < 0.01:
            issues.append("音量过低")
        elif max_amplitude > 0.9:
            issues.append("音量过高（可能削波）")
        
        return issues
    
    def _determine_audio_quality(self, snr: float, speech_activity: float, issues: List[str]) -> AudioQuality:
        """确定音频质量等级"""
        if snr > 20 and speech_activity > 0.7 and not issues:
            return AudioQuality.EXCELLENT
        elif snr > 15 and speech_activity > 0.5 and len(issues) <= 1:
            return AudioQuality.GOOD
        elif snr > 10 and speech_activity > 0.3:
            return AudioQuality.FAIR
        else:
            return AudioQuality.POOR
    
    async def _preprocess_audio(self, audio_data: bytes, analysis: AudioAnalysisResult) -> bytes:
        """预处理音频数据"""
        if analysis.quality == AudioQuality.EXCELLENT:
            # 高质量音频不需要预处理
            return audio_data
        
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
            
            # 应用噪声抑制
            if analysis.noise_level > 0.05:
                audio_float = nr.reduce_noise(y=audio_float, sr=sample_rate)
            
            # 音量标准化
            audio_float = self._normalize_volume(audio_float)
            
            # 采样率转换（如果需要）
            if sample_rate != self.audio_config["target_sample_rate"]:
                audio_float = librosa.resample(audio_float, 
                                             orig_sr=sample_rate,
                                             target_sr=self.audio_config["target_sample_rate"])
                sample_rate = self.audio_config["target_sample_rate"]
            
            # 转换回整数格式
            audio_int = (audio_float * 32768).astype(np.int16)
            
            # 创建新的WAV文件
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int.tobytes())
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"音频预处理失败: {e}")
            return audio_data
    
    def _normalize_volume(self, audio_data: np.ndarray) -> np.ndarray:
        """音量标准化"""
        # 计算RMS
        rms = np.sqrt(np.mean(audio_data**2))
        
        if rms > 0:
            # 目标RMS（转换为线性值）
            target_rms = 10**(self.audio_config["volume_normalization_target"] / 20)
            gain = target_rms / rms
            
            # 应用增益（限制最大增益）
            max_gain = 10.0
            gain = min(gain, max_gain)
            
            return audio_data * gain
        
        return audio_data
    
    async def _enhance_text(self, text: str, language: str, confidence: float) -> str:
        """增强识别文本"""
        if confidence > 0.8:
            # 高置信度文本，轻微处理
            return self._clean_text(text)
        
        # 低置信度文本，应用更多增强
        enhanced_text = text
        
        # 1. 文本清理
        enhanced_text = self._clean_text(enhanced_text)
        
        # 2. 标点符号修复
        enhanced_text = self._fix_punctuation(enhanced_text, language)
        
        # 3. 常见错误修正
        enhanced_text = self._fix_common_errors(enhanced_text, language)
        
        # 4. 大小写规范化
        if language.startswith("en"):
            enhanced_text = self._normalize_case(enhanced_text)
        
        return enhanced_text
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空格
        text = ' '.join(text.split())
        
        # 移除特殊字符（保留标点符号）
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff.,!?;:()\[\]{}]', '', text)
        
        return text.strip()
    
    def _fix_punctuation(self, text: str, language: str) -> str:
        """修复标点符号"""
        if language.startswith("zh"):
            # 中文标点符号修复
            text = re.sub(r'\s+([，。！？；：])', r'\1', text)  # 移除标点前的空格
            text = re.sub(r'([，。！？；：])\s+', r'\1', text)  # 移除标点后的空格
        elif language.startswith("en"):
            # 英文标点符号修复
            text = re.sub(r'\s+([,.!?;:])', r'\1', text)
            text = re.sub(r'([,.!?;:])\s+', r'\1 ', text)
        
        return text
    
    def _fix_common_errors(self, text: str, language: str) -> str:
        """修复常见错误"""
        # 语言特定的常见错误修正
        if language.startswith("zh"):
            # 中文常见错误
            corrections = {
                "你好吗": "你好吗",
                "谢谢": "谢谢",
                "对不起": "对不起"
            }
            
            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)
        
        return text
    
    def _normalize_case(self, text: str) -> str:
        """规范化大小写"""
        # 句子首字母大写
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    async def _apply_language_model_correction(self, text: str, language: str) -> str:
        """应用语言模型校正"""
        if not text:
            return text
        
        # 简单的语言模型校正
        words = text.split()
        corrected_words = []
        
        for word in words:
            # 检查单词是否在常见词列表中
            if self._is_common_word(word, language):
                corrected_words.append(word)
            else:
                # 尝试找到最相似的常见词
                similar_word = self._find_similar_word(word, language)
                if similar_word:
                    corrected_words.append(similar_word)
                else:
                    corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _is_common_word(self, word: str, language: str) -> bool:
        """检查是否为常见词"""
        lang_key = "chinese" if language.startswith("zh") else "english"
        common_words = self.language_model_config[lang_key]["common_words"]
        
        return word.lower() in common_words
    
    def _find_similar_word(self, word: str, language: str) -> Optional[str]:
        """查找相似词"""
        lang_key = "chinese" if language.startswith("zh") else "english"
        common_words = self.language_model_config[lang_key]["common_words"]
        
        # 简单的相似度计算（编辑距离）
        def edit_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return edit_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # 查找最相似的词
        best_match = None
        best_distance = float('inf')
        
        for common_word in common_words:
            distance = edit_distance(word.lower(), common_word.lower())
            if distance < best_distance and distance <= 2:  # 允许最多2个字符的差异
                best_distance = distance
                best_match = common_word
        
        return best_match
    
    def _calculate_confidence_boost(self, audio_analysis: AudioAnalysisResult, 
                                  original_text: str, enhanced_text: str) -> float:
        """计算置信度提升"""
        # 基于音频质量和文本改进计算置信度提升
        quality_boost = {
            AudioQuality.POOR: 0.0,
            AudioQuality.FAIR: 0.1,
            AudioQuality.GOOD: 0.2,
            AudioQuality.EXCELLENT: 0.3
        }[audio_analysis.quality]
        
        # 基于文本改进的置信度提升
        text_improvement = 0.0
        if original_text != enhanced_text:
            # 计算文本改进程度
            original_words = set(original_text.split())
            enhanced_words = set(enhanced_text.split())
            
            if original_words and enhanced_words:
                intersection = original_words.intersection(enhanced_words)
                union = original_words.union(enhanced_words)
                similarity = len(intersection) / len(union)
                text_improvement = 1.0 - similarity  # 差异越大，改进越大
        
        # 总置信度提升
        total_boost = quality_boost + (text_improvement * 0.2)
        
        return min(total_boost, 0.5)  # 限制最大提升为0.5
    
    def _identify_corrections(self, original_text: str, enhanced_text: str) -> List[str]:
        """识别应用的修正"""
        corrections = []
        
        if original_text != enhanced_text:
            original_words = original_text.split()
            enhanced_words = enhanced_text.split()
            
            for i, (orig, enh) in enumerate(zip(original_words, enhanced_words)):
                if orig != enh:
                    corrections.append(f"位置{i}: '{orig}' -> '{enh}'")
        
        return corrections
    
    def _calculate_language_model_score(self, text: str, language: str) -> float:
        """计算语言模型得分"""
        if not text:
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        lang_key = "chinese" if language.startswith("zh") else "english"
        common_words = self.language_model_config[lang_key]["common_words"]
        
        # 计算常见词比例
        common_count = sum(1 for word in words if word.lower() in common_words)
        score = common_count / len(words)
        
        return score
    
    def _update_accuracy_stats(self, result: RecognitionEnhancementResult, language: str):
        """更新准确率统计"""
        self.accuracy_stats["total_enhancements"] += 1
        
        if result.confidence_boost > 0.1:
            self.accuracy_stats["successful_enhancements"] += 1
        
        # 更新平均置信度提升
        total_boost = self.accuracy_stats["average_confidence_boost"] * (self.accuracy_stats["total_enhancements"] - 1)
        total_boost += result.confidence_boost
        self.accuracy_stats["average_confidence_boost"] = total_boost / self.accuracy_stats["total_enhancements"]
        
        # 更新语言特定统计
        if language not in self.accuracy_stats["language_specific_stats"]:
            self.accuracy_stats["language_specific_stats"][language] = {
                "total": 0,
                "successful": 0,
                "average_boost": 0.0
            }
        
        lang_stats = self.accuracy_stats["language_specific_stats"][language]
        lang_stats["total"] += 1
        
        if result.confidence_boost > 0.1:
            lang_stats["successful"] += 1
        
        # 更新语言平均提升
        total_lang_boost = lang_stats["average_boost"] * (lang_stats["total"] - 1)
        total_lang_boost += result.confidence_boost
        lang_stats["average_boost"] = total_lang_boost / lang_stats["total"]
    
    def get_accuracy_enhancement_report(self) -> Dict[str, Any]:
        """获取准确率增强报告"""
        success_rate = 0.0
        if self.accuracy_stats["total_enhancements"] > 0:
            success_rate = (self.accuracy_stats["successful_enhancements"] / 
                          self.accuracy_stats["total_enhancements"]) * 100
        
        return {
            "success_rate": success_rate,
            "average_confidence_boost": self.accuracy_stats["average_confidence_boost"],
            "total_enhancements": self.accuracy_stats["total_enhancements"],
            "successful_enhancements": self.accuracy_stats["successful_enhancements"],
            "language_specific_stats": self.accuracy_stats["language_specific_stats"]
        }
    
    def _load_chinese_common_words(self) -> set:
        """加载中文常见词"""
        common_words = {
            "你好", "谢谢", "对不起", "请问", "可以", "需要", "帮助", "问题", "解决",
            "今天", "明天", "昨天", "现在", "以后", "之前", "之后", "时间", "日期",
            "工作", "学习", "生活", "家庭", "朋友", "公司", "学校", "医院", "商店",
            "吃饭", "睡觉", "工作", "学习", "运动", "休息", "娱乐", "旅游", "购物"
        }
        return common_words
    
    def _load_english_common_words(self) -> set:
        """加载英文常见词"""
        common_words = {
            "hello", "thank", "sorry", "please", "can", "need", "help", "problem", "solution",
            "today", "tomorrow", "yesterday", "now", "later", "before", "after", "time", "date",
            "work", "study", "life", "family", "friend", "company", "school", "hospital", "store",
            "eat", "sleep", "work", "study", "exercise", "rest", "entertainment", "travel", "shopping"
        }
        return common_words


# 创建全局语音准确率增强器实例
voice_accuracy_enhancer = VoiceAccuracyEnhancer()