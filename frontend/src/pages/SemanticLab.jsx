import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Dna, 
  ArrowRightLeft, 
  CheckCircle2, 
  AlertCircle, 
  XCircle,
  Zap,
  BookOpen,
  ClipboardCheck,
  Loader2,
  Trash2,
  ShieldAlert,
  UserCheck,
  RefreshCw,
  FileText
} from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://localhost:8000"

const SemanticLab = () => {
  const [text1, setText1] = useState("")
  const [text2, setText2] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const [activeTab, setActiveTab] = useState("similarity") // "similarity" or "plagiarism"
  const [singleText, setSingleText] = useState("")
  const [plagLoading, setPlagLoading] = useState(false)
  const [plagResult, setPlagResult] = useState(null)
  const [humanizing, setHumanizing] = useState(false)

  const checkPlagiarism = async () => {
    if (!singleText.trim()) return
    setPlagLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/api/analysis/detect-plagiarism`, { text: singleText })
      setPlagResult(response.data) // { score, analysis }
    } catch (err) {
      console.error(err)
      setPlagResult({ score: 0, analysis: "Error connecting to AI detection service." })
    } finally {
      setPlagLoading(false)
    }
  }

  const humanizeText = async () => {
    if (!singleText.trim()) return
    setHumanizing(true)
    try {
      const response = await axios.post(`${API_BASE}/api/analysis/humanize`, { text: singleText })
      setSingleText(response.data.humanized_text)
      setPlagResult(null) // Clear result since text has changed
    } catch (err) {
      console.error(err)
    } finally {
      setHumanizing(false)
    }
  }

  const checkSimilarity = async () => {
    if (!text1.trim() || !text2.trim()) return

    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/api/analysis/similarity`, { 
        paragraph1: text1, 
        paragraph2: text2 
      })
      const score = Math.round(response.data * 100)
      
      let status = 'medium'
      let message = "These paragraphs share partial themes but differ in core information."
      let icon = <AlertCircle size={20} className="text-orange-500" />
      
      if (score > 80) {
        status = 'high'
        message = "High Semantic Match: These texts express essentially the same concept with high degree of overlap."
        icon = <CheckCircle2 size={20} className="text-emerald-500" />
      } else if (score < 40) {
        status = 'low'
        message = "Low Semantic Match: These texts appear to discuss different subject matters or viewpoints."
        icon = <XCircle size={20} className="text-rose-500" />
      }

      setResult({ score, message, status, icon })
    } catch (err) {
      console.error("Similarity Error", err)
      setResult({ score: 0, message: "Error connecting to AI analysis engine.", status: 'low', icon: <XCircle size={20} className="text-rose-500" /> })
    } finally {
      setLoading(false)
    }
  }

  const clear = () => {
    setText1("")
    setText2("")
    setResult(null)
    setSingleText("")
    setPlagResult(null)
  }

  return (
    <div className="space-y-8 animate-in slide-in-from-left duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-display">Semantic Lab</h1>
          <p className="text-slate-500">Analyze the conceptual similarity between academic passages.</p>
        </div>
        <button 
          onClick={clear}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-600 font-semibold px-4 py-2 rounded-xl transition-all"
        >
          <Trash2 size={18} />
          Clear Workspace
        </button>
      </div>

      <div className="flex bg-slate-100 p-1 rounded-2xl w-fit mx-auto mb-4">
        <button 
          onClick={() => setActiveTab("similarity")}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${activeTab === 'similarity' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
          <ArrowRightLeft size={18} />
          Similarity Matcher
        </button>
        <button 
          onClick={() => setActiveTab("plagiarism")}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${activeTab === 'plagiarism' ? 'bg-white text-rose-500 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
          <ShieldAlert size={18} />
          Plagiarism & AI Checker
        </button>
      </div>

      {activeTab === "similarity" && (
        <div className="space-y-8 animate-in fade-in duration-500">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 relative">
        {/* Connector Icon */}
        <div className="hidden lg:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-white rounded-full shadow-lg border border-slate-100 z-10 items-center justify-center text-primary group transition-all">
           <ArrowRightLeft className="group-hover:rotate-180 transition-transform duration-500" size={24} />
        </div>

        {/* Input A */}
        <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm transition-all focus-within:ring-4 focus-within:ring-primary/10">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <BookOpen size={18} className="text-primary" />
              Source Material A
            </div>
          </div>
          <textarea 
            value={text1}
            onChange={(e) => setText1(e.target.value)}
            className="w-full h-80 outline-none resize-none text-slate-600 bg-slate-50/50 p-6 rounded-2xl border border-dashed border-slate-300 focus:border-primary/50 focus:bg-white transition-all text-sm leading-relaxed"
            placeholder="Paste first paragraph here..."
          />
        </div>

        {/* Input B */}
        <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm transition-all focus-within:ring-4 focus-within:ring-primary/10">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <ClipboardCheck size={18} className="text-secondary" />
              Source Material B
            </div>
          </div>
          <textarea 
            value={text2}
            onChange={(e) => setText2(e.target.value)}
            className="w-full h-80 outline-none resize-none text-slate-600 bg-slate-50/50 p-6 rounded-2xl border border-dashed border-slate-300 focus:border-secondary/50 focus:bg-white transition-all text-sm leading-relaxed"
            placeholder="Paste second paragraph here..."
          />
        </div>
      </div>

      <div className="flex flex-col items-center justify-center p-8">
        <button 
          onClick={checkSimilarity}
          disabled={loading || !text1 || !text2}
          className="gradient-btn flex items-center gap-3 relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
          {loading ? <Loader2 size={24} className="animate-spin" /> : <Zap size={24} />}
          <span className="text-lg font-bold">Execute Semantic Matching</span>
        </button>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-white rounded-[2rem] p-10 border border-slate-100 shadow-2xl overflow-hidden relative"
          >
            {/* Background Blob decoration */}
            <div className={`absolute -right-20 -top-20 w-64 h-64 blur-3xl rounded-full opacity-10 ${result.status === 'high' ? 'bg-emerald-500' : result.status === 'medium' ? 'bg-orange-500' : 'bg-rose-500'}`}></div>

            <div className="flex flex-col md:flex-row items-center gap-10 relative z-10">
              {/* Circular Progress */}
              <div className="relative w-40 h-40 flex items-center justify-center shrink-0">
                <svg className="w-full h-full -rotate-90">
                    <circle cx="80" cy="80" r="70" className="stroke-slate-100 fill-none" strokeWidth="12" />
                    <motion.circle 
                        cx="80" cy="80" r="70" 
                        className={`fill-none ${result.status === 'high' ? 'stroke-emerald-500' : result.status === 'medium' ? 'stroke-orange-500' : 'stroke-rose-500'}`} 
                        strokeWidth="12" 
                        strokeLinecap="round"
                        initial={{ strokeDasharray: "0 440" }}
                        animate={{ strokeDasharray: `${(result.score / 100) * 440} 440` }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                    />
                </svg>
                <div className="absolute flex flex-col items-center">
                    <span className="text-4xl font-black text-slate-800 tracking-tighter">{result.score}%</span>
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Confidence</span>
                </div>
              </div>

              {/* Text Result */}
              <div className="flex-1 space-y-4">
                <div className={`flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-bold w-fit shadow-sm ${result.status === 'high' ? 'bg-emerald-50 text-emerald-600' : result.status === 'medium' ? 'bg-orange-50 text-orange-600' : 'bg-rose-50 text-rose-600'}`}>
                    {result.icon}
                    {result.status === 'high' ? 'High Similarity' : result.status === 'medium' ? 'Moderate Similarity' : 'Low Similarity'}
                </div>
                <h2 className="text-2xl font-bold text-slate-800 leading-snug">{result.message}</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                    <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                        <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-1">Concept Overlap</p>
                        <div className="flex items-baseline gap-1">
                            <span className="text-xl font-bold">{Math.min(100, result.score + 5)}%</span>
                            <span className="text-[10px] text-emerald-500 font-bold tracking-tighter">Positive</span>
                        </div>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                        <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-1">Inference Level</p>
                        <div className="flex items-baseline gap-1">
                            <span className="text-xl font-bold">Neural</span>
                            <span className="text-[10px] text-primary font-bold tracking-tighter">DeepEngine</span>
                        </div>
                    </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
        </div>
      )}

      {activeTab === "plagiarism" && (
        <div className="space-y-8 animate-in fade-in duration-500">
           <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm transition-all focus-within:ring-4 focus-within:ring-rose-500/10">
             <div className="flex items-center justify-between mb-4">
               <div className="flex items-center gap-2 font-bold text-slate-800">
                 <FileText size={18} className="text-rose-500" />
                 Text to Analyze
               </div>
               <button 
                 onClick={humanizeText}
                 disabled={humanizing || !singleText}
                 className="flex items-center gap-2 text-emerald-600 hover:text-emerald-700 font-bold px-4 py-2 bg-emerald-50 rounded-xl transition-all disabled:opacity-50"
               >
                 {humanizing ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                 Humanize / Remove AI
               </button>
             </div>
             <textarea 
               value={singleText}
               onChange={(e) => setSingleText(e.target.value)}
               className="w-full h-80 outline-none resize-none text-slate-600 bg-slate-50/50 p-6 rounded-2xl border border-dashed border-slate-300 focus:border-rose-500/50 focus:bg-white transition-all text-sm leading-relaxed"
               placeholder="Paste document text here to check for AI generation and plagiarism..."
             />
           </div>

           <div className="flex flex-col items-center justify-center p-8">
             <button 
               onClick={checkPlagiarism}
               disabled={plagLoading || !singleText}
               className="bg-gradient-to-r from-rose-500 to-orange-500 text-white rounded-2xl px-8 py-4 flex items-center gap-3 relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-rose-500/25 transition-all"
             >
               {plagLoading ? <Loader2 size={24} className="animate-spin" /> : <ShieldAlert size={24} />}
               <span className="text-lg font-bold">Check Plagiarism & AI</span>
             </button>
           </div>

           <AnimatePresence>
             {plagResult && (
               <motion.div 
                 initial={{ opacity: 0, y: 30 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0, scale: 0.9 }}
                 className="bg-white rounded-[2rem] p-10 border border-slate-100 shadow-2xl overflow-hidden relative"
               >
                 <div className={`absolute -right-20 -top-20 w-64 h-64 blur-3xl rounded-full opacity-10 ${plagResult.score > 50 ? 'bg-rose-500' : 'bg-emerald-500'}`}></div>
                 
                 <div className="flex flex-col md:flex-row items-center gap-10 relative z-10">
                   <div className="relative w-40 h-40 flex items-center justify-center shrink-0">
                     <svg className="w-full h-full -rotate-90">
                         <circle cx="80" cy="80" r="70" className="stroke-slate-100 fill-none" strokeWidth="12" />
                         <motion.circle 
                             cx="80" cy="80" r="70" 
                             className={`fill-none ${plagResult.score > 50 ? 'stroke-rose-500' : 'stroke-emerald-500'}`} 
                             strokeWidth="12" 
                             strokeLinecap="round"
                             initial={{ strokeDasharray: "0 440" }}
                             animate={{ strokeDasharray: `${(plagResult.score / 100) * 440} 440` }}
                             transition={{ duration: 1.5, ease: "easeOut" }}
                         />
                     </svg>
                     <div className="absolute flex flex-col items-center">
                         <span className="text-4xl font-black text-slate-800 tracking-tighter">{plagResult.score}%</span>
                         <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">AI / Plagiarism</span>
                     </div>
                   </div>

                   <div className="flex-1 space-y-4">
                     <div className={`flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-bold w-fit shadow-sm ${plagResult.score > 50 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
                         {plagResult.score > 50 ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
                         {plagResult.score > 50 ? 'High AI Generation/Plagiarism Detected' : 'Text Appears Human & Original'}
                     </div>
                     <p className="text-slate-600 text-lg leading-relaxed">{plagResult.analysis}</p>
                   </div>
                 </div>
               </motion.div>
             )}
           </AnimatePresence>
        </div>
      )}
    </div>
  )
}

export default SemanticLab
