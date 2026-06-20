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
  Trash2
} from 'lucide-react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

const API_BASE = "http://localhost:8000"

const Chat = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I'm your Intelligent Academic Assistant. How can I help you study today? You can type your question or use the microphone to speak.", sender: 'ai', time: 'Just now' }
  ])
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [voiceIndicator, setVoiceIndicator] = useState(0)
  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('q')
    if (q) setInput(q)
  }, [])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMsg = { id: Date.now(), text: input, sender: 'user', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setIsTyping(true)

    try {
      const response = await axios.post(`${API_BASE}/api/qa/ask`, { question: input }, { timeout: 30000 })
      const aiMsg = {
        id: Date.now() + 1,
        text: response.data.answer,
        sender: 'ai',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.data.sources || []
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      console.error("Chat Error", err)
      const errorMsg = { id: Date.now() + 1, text: "I'm having trouble connecting to my academic database right now. Please ensure the backend is running.", sender: 'ai', time: 'Just now', isError: true }
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
      // Simulate voice pulse
      const interval = setInterval(() => {
        setVoiceIndicator(Math.random() * 100)
      }, 100)
      recognition._pulse = interval
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInput(transcript)
      // Auto-send after a short delay
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
    <div className="flex flex-col h-[calc(100vh-180px)] bg-white rounded-3xl border border-slate-100 shadow-xl overflow-hidden animate-in zoom-in-95 duration-500 relative">
      {/* Header */}
      <div className="px-8 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary shadow-sm ring-4 ring-white">
            <Bot size={22} />
          </div>
          <div>
            <h3 className="font-bold text-slate-800 leading-tight">AI Academic Scholar</h3>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-emerald-500/50 shadow-sm"></span>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">System Online</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all" title="Clear History" onClick={() => setMessages([])}>
            <Trash2 size={18} />
          </button>
          <button className="p-2 text-slate-400 hover:text-primary hover:bg-primary/5 rounded-lg transition-all">
            <Volume2 size={18} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth" id="chat-messages">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, x: msg.sender === 'user' ? 20 : -20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex flex-col max-w-[80%] ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-xs font-bold shadow-md ${msg.sender === 'user' ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500 border border-slate-200'}`}>
                    {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                  </div>
                  <div className={`p-4 rounded-2xl shadow-sm text-sm leading-relaxed ${msg.sender === 'user' ? 'bg-slate-900 text-white rounded-tr-none' : 'bg-slate-50 text-slate-800 border border-slate-200 rounded-tl-none font-medium'}`}>
                    {msg.sender === 'user' ? (
                      msg.text
                    ) : (
                      <div className="prose prose-slate prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-100 prose-pre:text-slate-900">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      </div>
                    )}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-200/50 flex flex-wrap gap-2">
                        {msg.sources.map((s, idx) => (
                          <span key={idx} className="bg-white/50 px-2 py-0.5 rounded text-[10px] text-slate-500 border border-slate-200 font-bold uppercase tracking-tighter">Ref: {s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <span className="text-[10px] text-slate-400 mt-2 font-medium px-11 uppercase">{msg.time}</span>
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
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce delay-150"></span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce delay-300"></span>
            </div>
          </motion.div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 bg-slate-50/50 backdrop-blur-sm border-t border-slate-100 mt-auto relative overflow-hidden group">
        <div className="max-w-4xl mx-auto flex items-end gap-4 relative z-10">
          <div className="relative flex-1 group">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <Sparkles size={16} className="text-primary/40 group-focus-within:text-primary group-focus-within:animate-pulse transition-colors" />
            </div>
            <textarea
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder="Ask a question about your study materials..."
              className="w-full bg-white border border-slate-200 rounded-2xl py-3.5 pl-11 pr-32 text-sm focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all resize-none shadow-sm"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
              <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all">
                <Paperclip size={18} />
              </button>
              <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all">
                <Smile size={18} />
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <motion.button
              onClick={startVoice}
              animate={isListening ? { scale: [1, 1.1, 1] } : {}}
              transition={isListening ? { repeat: Infinity, duration: 2 } : {}}
              className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all ${isListening ? 'bg-secondary text-white shadow-lg shadow-secondary/30' : 'bg-white border border-slate-200 text-slate-500 hover:bg-slate-50'}`}
            >
              {isListening ? <Mic size={20} className="animate-pulse" /> : <Mic size={20} />}
            </motion.button>

            <button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="w-12 h-12 bg-primary text-white rounded-xl flex items-center justify-center shadow-lg shadow-primary/30 hover:bg-primary-dark transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isTyping ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>

        {/* Dynamic Voice Waveform Effect */}
        {isListening && (
          <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-secondary to-transparent"
            style={{ transform: `scaleX(${voiceIndicator / 100})`, opacity: voiceIndicator / 100 }}></div>
        )}
      </div>
    </div>
  )
}

export default Chat
