import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  Mic,
  MicOff,
  Bot,
  User,
  Sparkles,
  Volume2,
  Paperclip,
  Smile,
  Loader2,
  Trash2,
  Sliders,
  CheckCircle2,
  Cpu,
  Layers,
  FileText
} from 'lucide-react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

const API_BASE = "http://localhost:8000"

const Chat = () => {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: "Hello! I'm your Optimization-Driven Academic Scholar. Ask me any question from your uploaded academic literature or benchmark notes. You can toggle between **Default** and **Optimized** retrieval modes to see how metaheuristic parameters alter context retrieval.", 
      sender: 'ai', 
      time: 'Just now' 
    }
  ])
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [voiceIndicator, setVoiceIndicator] = useState(0)
  const [retrievalMode, setRetrievalMode] = useState("optimized") // "default" or "optimized"
  const [activeConfig, setActiveConfig] = useState(null)
  const [availableDocs, setAvailableDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState("")
  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  useEffect(() => {
    fetchActiveConfig()
    fetchDocs()
    const q = new URLSearchParams(window.location.search).get('q')
    if (q) setInput(q)
  }, [])

  const fetchActiveConfig = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/optimization/active-config`)
      setActiveConfig(res.data)
      if (res.data.mode) {
        setRetrievalMode(res.data.mode)
      }
    } catch (err) {
      console.warn("Could not fetch active retrieval config", err)
    }
  }

  const fetchDocs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/document/list`)
      if (res.data && res.data.documents) {
        setAvailableDocs(res.data.documents)
      }
    } catch (err) {
      console.warn("Could not load documents", err)
    }
  }

  const toggleRetrievalMode = async (mode) => {
    setRetrievalMode(mode)
    if (mode === "default") {
      try {
        await axios.post(`${API_BASE}/api/optimization/active-config/reset`)
        fetchActiveConfig()
      } catch (err) {
        console.warn("Could not reset config", err)
      }
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMsg = { 
      id: Date.now(), 
      text: input, 
      sender: 'user', 
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    }
    setMessages(prev => [...prev, userMsg])
    const questionText = input
    setInput("")
    setIsTyping(true)

    try {
      const payload = {
        question: questionText,
        retrieval_mode: retrievalMode,
        document_filename: selectedDoc || undefined
      }
      const response = await axios.post(`${API_BASE}/api/qa/ask`, payload, { timeout: 45000 })
      
      const aiMsg = {
        id: Date.now() + 1,
        text: response.data.answer,
        sender: 'ai',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.data.sources || [],
        retrievalMode: response.data.retrieval_mode,
        retrievalConfig: response.data.retrieval_config
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      console.error("Chat Error", err)
      const errorMsg = { 
        id: Date.now() + 1, 
        text: "I'm having trouble retrieving passages or connecting to the AI backend. Please ensure the backend is running.", 
        sender: 'ai', 
        time: 'Just now', 
        isError: true 
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsTyping(false)
    }
  }

  const startVoice = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Speech recognition is not supported in this browser.")
      return
    }

    const recognition = new window.webkitSpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      setIsListening(true)
      const interval = setInterval(() => {
        setVoiceIndicator(Math.random() * 100)
      }, 100)
      recognition._pulse = interval
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInput(transcript)
      setTimeout(() => handleSend(), 500)
    }

    recognition.onend = () => {
      setIsListening(false)
      clearInterval(recognition._pulse)
      setVoiceIndicator(0)
    }

    recognition.start()
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] bg-white rounded-3xl border border-slate-200/80 shadow-xl overflow-hidden animate-in zoom-in-95 duration-500 relative">
      {/* Header */}
      <div className="px-8 py-3.5 bg-slate-50 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary shadow-sm ring-4 ring-white">
            <Bot size={22} />
          </div>
          <div>
            <h3 className="font-bold text-slate-800 leading-tight flex items-center gap-2">
              AI Academic Scholar
              <span className="text-[10px] bg-emerald-50 text-emerald-600 font-extrabold uppercase px-2 py-0.5 rounded border border-emerald-200">
                RAG v2
              </span>
            </h3>
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <span>Optimization-Driven Retrieval Active</span>
            </div>
          </div>
        </div>

        {/* Retrieval Mode Toggle & Active Config Badges */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Document Target Selector */}
          {availableDocs.length > 0 && (
            <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-xl px-2.5 py-1 text-xs">
              <FileText size={13} className="text-slate-400" />
              <select
                value={selectedDoc}
                onChange={(e) => setSelectedDoc(e.target.value)}
                className="bg-transparent text-slate-700 font-medium outline-none text-xs cursor-pointer max-w-[140px] truncate"
              >
                <option value="">Latest Upload</option>
                {availableDocs.map((d, i) => (
                  <option key={i} value={d.filename}>{d.filename}</option>
                ))}
              </select>
            </div>
          )}

          {/* Mode Pill Switch */}
          <div className="flex bg-slate-200/80 p-1 rounded-xl text-xs font-bold">
            <button
              onClick={() => toggleRetrievalMode("default")}
              className={`px-3 py-1 rounded-lg transition-all ${
                retrievalMode === "default"
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Default
            </button>
            <button
              onClick={() => toggleRetrievalMode("optimized")}
              className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                retrievalMode === "optimized"
                  ? "bg-primary text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Sparkles size={12} />
              Optimized
            </button>
          </div>

          <div className="flex items-center gap-1">
            <button 
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all" 
              title="Clear History" 
              onClick={() => setMessages([])}
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Current Retrieval Configuration Banner */}
      <div className="bg-slate-900 text-slate-200 px-8 py-2 text-xs flex flex-wrap items-center justify-between gap-3 border-b border-slate-800">
        <div className="flex items-center gap-2 font-mono">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Current Pipeline:</span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
            retrievalMode === "optimized" ? "bg-emerald-950 text-emerald-300 border border-emerald-700" : "bg-slate-800 text-slate-300"
          }`}>
            {retrievalMode === "optimized" ? `Optimized (${activeConfig?.algorithm_source || 'Metaheuristic'})` : 'Default Baseline'}
          </span>
        </div>
        {activeConfig && (
          <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-300">
            <span>Chunk: <strong className="text-white">{retrievalMode === "optimized" ? activeConfig.chunk_size : 800}</strong></span>
            <span>Overlap: <strong className="text-white">{retrievalMode === "optimized" ? activeConfig.chunk_overlap : 100}</strong></span>
            <span>Top-K: <strong className="text-white">{retrievalMode === "optimized" ? activeConfig.top_k : 3}</strong></span>
            <span>Cutoff: <strong className="text-white">{retrievalMode === "optimized" ? activeConfig.similarity_threshold : 0.20}</strong></span>
            <span>Budget: <strong className="text-white">{retrievalMode === "optimized" ? activeConfig.context_token_budget : 3000} tok</strong></span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6 scroll-smooth" id="chat-messages">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, x: msg.sender === 'user' ? 20 : -20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex flex-col max-w-[85%] ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-xs font-bold shadow-md ${
                    msg.sender === 'user' ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500 border border-slate-200'
                  }`}>
                    {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                  </div>
                  <div className={`p-4 rounded-2xl shadow-sm text-sm leading-relaxed ${
                    msg.sender === 'user' 
                      ? 'bg-slate-900 text-white rounded-tr-none' 
                      : 'bg-slate-50 text-slate-800 border border-slate-200 rounded-tl-none font-medium'
                  }`}>
                    {msg.sender === 'user' ? (
                      msg.text
                    ) : (
                      <div className="prose prose-slate prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-100 prose-pre:text-slate-900">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      </div>
                    )}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-200/60 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                          <Layers size={12} />
                          <span>Retrieved Evidence ({msg.retrievalMode || 'dynamic'} mode):</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.sources.map((s, idx) => (
                            <span 
                              key={idx} 
                              className="bg-white px-2 py-1 rounded text-[10px] text-slate-600 border border-slate-200 font-mono shadow-xs block"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <span className="text-[10px] text-slate-400 mt-1.5 font-medium px-11 uppercase">{msg.time}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400 border border-slate-200">
              <Bot size={14} />
            </div>
            <div className="flex gap-1.5 p-3 bg-slate-50 rounded-2xl border border-slate-100">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-150"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-300"></span>
            </div>
          </motion.div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-5 bg-slate-50/70 backdrop-blur-sm border-t border-slate-200/80 mt-auto relative overflow-hidden group">
        <div className="max-w-4xl mx-auto flex items-end gap-3 relative z-10">
          <div className="relative flex-1 group">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <Sparkles size={16} className="text-primary/50 group-focus-within:text-primary group-focus-within:animate-pulse transition-colors" />
            </div>
            <textarea
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder={`Ask a question with ${retrievalMode} retrieval parameters...`}
              className="w-full bg-white border border-slate-200 rounded-2xl py-3 pl-11 pr-24 text-sm focus:ring-3 focus:ring-primary/10 focus:border-primary outline-none transition-all resize-none shadow-sm"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <button 
                type="button"
                onClick={() => setInput("What are the key concepts and optimization objectives discussed in the document?")}
                className="text-[10px] font-bold text-primary bg-primary/5 hover:bg-primary/10 px-2 py-1 rounded transition-colors"
                title="Use sample academic prompt"
              >
                Sample
              </button>
            </div>
          </div>

          <div className="flex gap-2">
            <motion.button
              onClick={startVoice}
              animate={isListening ? { scale: [1, 1.1, 1] } : {}}
              transition={isListening ? { repeat: Infinity, duration: 2 } : {}}
              className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all ${
                isListening 
                  ? 'bg-secondary text-white shadow-lg shadow-secondary/30' 
                  : 'bg-white border border-slate-200 text-slate-500 hover:bg-slate-50'
              }`}
              title="Voice Input"
            >
              {isListening ? <Mic size={18} className="animate-pulse" /> : <Mic size={18} />}
            </motion.button>

            <button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="w-11 h-11 bg-primary text-white rounded-xl flex items-center justify-center shadow-lg shadow-primary/25 hover:bg-primary-dark transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title="Send Query"
            >
              {isTyping ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
        </div>

        {/* Dynamic Voice Waveform Effect */}
        {isListening && (
          <div 
            className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-secondary to-transparent"
            style={{ transform: `scaleX(${voiceIndicator / 100})`, opacity: voiceIndicator / 100 }}
          />
        )}
      </div>
    </div>
  )
}

export default Chat
