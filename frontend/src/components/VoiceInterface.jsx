import React, { useState, useRef, useEffect } from 'react';
import './VoiceInterface.css';

const VoiceInterface = () => {
  // 状态管理
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [recognitionConfidence, setRecognitionConfidence] = useState(0);
  const [voiceSettings, setVoiceSettings] = useState({
    voiceType: 'female',
    speed: 1.0,
    pitch: 1.0,
    language: 'zh-CN',
    emotion: 'neutral'
  });
  const [audioHistory, setAudioHistory] = useState([]);
  const [recognitionStats, setRecognitionStats] = useState({
    totalRequests: 0,
    successRate: 0,
    averageConfidence: 0
  });

  // 引用
  const audioRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const recognitionRef = useRef(null);

  // 初始化语音识别
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = voiceSettings.language;

      recognitionRef.current.onstart = () => {
        setIsListening(true);
        startAudioAnalysis();
      };

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        let confidence = 0;

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            confidence = event.results[i][0].confidence;
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(finalTranscript || interimTranscript);
        setRecognitionConfidence(confidence * 100);
        
        // 更新统计信息
        updateRecognitionStats(confidence);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('语音识别错误:', event.error);
        setIsListening(false);
        stopAudioAnalysis();
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        stopAudioAnalysis();
      };
    }
  }, [voiceSettings.language]);

  // 开始语音识别
  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
      } catch (error) {
        console.error('开始语音识别失败:', error);
      }
    }
  };

  // 停止语音识别
  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  // 开始音频分析（用于显示音频级别）
  const startAudioAnalysis = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      
      const analyzeAudio = () => {
        if (!isListening) return;
        
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average);
        
        requestAnimationFrame(analyzeAudio);
      };
      
      analyzeAudio();
    } catch (error) {
      console.error('音频分析失败:', error);
    }
  };

  // 停止音频分析
  const stopAudioAnalysis = () => {
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setAudioLevel(0);
  };

  // 文本转语音
  const speakText = async (text = transcript) => {
    if (!text.trim()) return;

    try {
      setIsSpeaking(true);
      
      // 使用Web Speech API
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = voiceSettings.language;
      utterance.rate = voiceSettings.speed;
      utterance.pitch = voiceSettings.pitch;

      // 设置语音类型
      const voices = window.speechSynthesis.getVoices();
      const selectedVoice = voices.find(voice => 
        voice.lang.includes(voiceSettings.language) && 
        voice.name.toLowerCase().includes(voiceSettings.voiceType)
      );
      
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }

      utterance.onend = () => {
        setIsSpeaking(false);
        // 保存到历史记录
        addToAudioHistory(text, 'synthesis');
      };

      utterance.onerror = (error) => {
        console.error('语音合成错误:', error);
        setIsSpeaking(false);
      };

      window.speechSynthesis.speak(utterance);
    } catch (error) {
      console.error('语音合成失败:', error);
      setIsSpeaking(false);
    }
  };

  // 停止语音合成
  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  // 添加到音频历史记录
  const addToAudioHistory = (text, type) => {
    const newEntry = {
      id: Date.now(),
      text,
      type,
      timestamp: new Date().toLocaleString(),
      settings: { ...voiceSettings }
    };
    
    setAudioHistory(prev => [newEntry, ...prev.slice(0, 49)]); // 保留最近50条
  };

  // 更新识别统计
  const updateRecognitionStats = (confidence) => {
    setRecognitionStats(prev => ({
      totalRequests: prev.totalRequests + 1,
      successRate: ((prev.successRate * prev.totalRequests + (confidence > 0.7 ? 1 : 0)) / (prev.totalRequests + 1)) * 100,
      averageConfidence: ((prev.averageConfidence * prev.totalRequests + confidence * 100) / (prev.totalRequests + 1))
    }));
  };

  // 清除转录文本
  const clearTranscript = () => {
    setTranscript('');
    setRecognitionConfidence(0);
  };

  // 下载音频
  const downloadAudio = async (text) => {
    try {
      // 这里应该调用后端API生成音频文件
      // 暂时使用模拟下载
      const blob = new Blob([text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `voice_${Date.now()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载音频失败:', error);
    }
  };

  // 语音设置变更
  const handleVoiceSettingChange = (setting, value) => {
    setVoiceSettings(prev => ({
      ...prev,
      [setting]: value
    }));
  };

  return (
    <div className="voice-interface">
      {/* 语音识别控制区域 */}
      <div className="recognition-section">
        <div className="recognition-controls">
          <button 
            className={`listen-btn ${isListening ? 'active' : ''}`}
            onClick={isListening ? stopListening : startListening}
            disabled={isSpeaking}
          >
            {isListening ? (
              <>
                <div className="pulse-animation"></div>
                🎤 停止录音
              </>
            ) : (
              '🎤 开始录音'
            )}
          </button>
          
          <div className="audio-level">
            <div 
              className="level-bar" 
              style={{ width: `${audioLevel}%` }}
            ></div>
          </div>
          
          <div className="confidence-indicator">
            <span>置信度: {recognitionConfidence.toFixed(1)}%</span>
          </div>
        </div>
        
        <div className="transcript-area">
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="语音识别结果将显示在这里..."
            className="transcript-input"
            rows="4"
          />
          <div className="transcript-actions">
            <button onClick={clearTranscript} className="clear-btn">
              🗑️ 清除
            </button>
            <button onClick={() => speakText()} className="speak-btn" disabled={isSpeaking || !transcript.trim()}>
              {isSpeaking ? '🔊 播放中...' : '🔊 朗读'}
            </button>
          </div>
        </div>
      </div>

      {/* 语音合成控制区域 */}
      <div className="synthesis-section">
        <div className="voice-settings">
          <h3>语音设置</h3>
          
          <div className="setting-group">
            <label>语音类型</label>
            <select 
              value={voiceSettings.voiceType}
              onChange={(e) => handleVoiceSettingChange('voiceType', e.target.value)}
            >
              <option value="female">女声</option>
              <option value="male">男声</option>
              <option value="child">童声</option>
            </select>
          </div>
          
          <div className="setting-group">
            <label>语速: {voiceSettings.speed.toFixed(1)}x</label>
            <input 
              type="range" 
              min="0.5" 
              max="2" 
              step="0.1" 
              value={voiceSettings.speed}
              onChange={(e) => handleVoiceSettingChange('speed', parseFloat(e.target.value))}
            />
          </div>
          
          <div className="setting-group">
            <label>语调: {voiceSettings.pitch.toFixed(1)}x</label>
            <input 
              type="range" 
              min="0.5" 
              max="2" 
              step="0.1" 
              value={voiceSettings.pitch}
              onChange={(e) => handleVoiceSettingChange('pitch', parseFloat(e.target.value))}
            />
          </div>
          
          <div className="setting-group">
            <label>语言</label>
            <select 
              value={voiceSettings.language}
              onChange={(e) => handleVoiceSettingChange('language', e.target.value)}
            >
              <option value="zh-CN">中文</option>
              <option value="en-US">English</option>
              <option value="ja-JP">日本語</option>
            </select>
          </div>
          
          <div className="setting-group">
            <label>情感</label>
            <select 
              value={voiceSettings.emotion}
              onChange={(e) => handleVoiceSettingChange('emotion', e.target.value)}
            >
              <option value="neutral">中性</option>
              <option value="happy">高兴</option>
              <option value="sad">悲伤</option>
              <option value="excited">兴奋</option>
            </select>
          </div>
        </div>
        
        <div className="quick-actions">
          <h3>快捷操作</h3>
          <div className="action-buttons">
            <button onClick={() => speakText('你好，有什么可以帮助你的吗？')} disabled={isSpeaking}>
              👋 问候语
            </button>
            <button onClick={() => speakText('谢谢您的使用，再见！')} disabled={isSpeaking}>
              👋 告别语
            </button>
            <button onClick={stopSpeaking} disabled={!isSpeaking}>
              ⏹️ 停止播放
            </button>
          </div>
        </div>
      </div>

      {/* 历史记录区域 */}
      <div className="history-section">
        <h3>历史记录</h3>
        <div className="history-list">
          {audioHistory.length === 0 ? (
            <p className="no-history">暂无历史记录</p>
          ) : (
            audioHistory.map(item => (
              <div key={item.id} className="history-item">
                <div className="item-header">
                  <span className="item-type">{item.type === 'synthesis' ? '🔊' : '🎤'}</span>
                  <span className="item-time">{item.timestamp}</span>
                </div>
                <p className="item-text">{item.text}</p>
                <div className="item-actions">
                  <button onClick={() => speakText(item.text)}>播放</button>
                  <button onClick={() => downloadAudio(item.text)}>下载</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 统计信息区域 */}
      <div className="stats-section">
        <h3>识别统计</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-value">{recognitionStats.totalRequests}</span>
            <span className="stat-label">总请求数</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{recognitionStats.successRate.toFixed(1)}%</span>
            <span className="stat-label">成功率</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{recognitionStats.averageConfidence.toFixed(1)}%</span>
            <span className="stat-label">平均置信度</span>
          </div>
        </div>
      </div>

      {/* 音频播放器 */}
      <audio ref={audioRef} className="audio-player" />
    </div>
  );
};

export default VoiceInterface;