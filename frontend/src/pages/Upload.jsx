import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  CloudUpload, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Plus, 
  Trash2, 
  ShieldCheck,
  Zap,
  ChevronRight,
  BookOpen,
  Layout,
  Star,
  ArrowRight,
  MessageSquare,
  MonitorPlay,
  Play
} from 'lucide-react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

const API_BASE = "http://localhost:8000"

const Upload = () => {
  const [files, setFiles] = useState([])
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [status, setStatus] = useState(null)
  const [uploadResults, setUploadResults] = useState(null)
  const [inlineAnswer, setInlineAnswer] = useState("")
  const [asking, setAsking] = useState(false)
  const [availableDocs, setAvailableDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState("")
  const [youtubeUrl, setYoutubeUrl] = useState("")
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('last_doc_intel')
    if (saved) setUploadResults(JSON.parse(saved))
    fetchDocs()
  }, [])

  const fetchDocs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/document/list`)
      setAvailableDocs(res.data.documents)
    } catch (err) {
      console.error("Failed to load document list", err)
    }
  }

  const deleteDocument = async (filename) => {
    if (!filename) return
    if (!window.confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) return

    setDeleting(true)
    try {
      await axios.delete(`${API_BASE}/api/document/delete?filename=${encodeURIComponent(filename)}`)
      setStatus({ message: `"${filename}" has been deleted successfully.`, type: "success" })
      setSelectedDoc("")
      fetchDocs()
    } catch (err) {
      console.error("Delete Error", err)
      const msg = err.response?.data?.detail || "Failed to delete the document."
      setStatus({ message: msg, type: "error" })
    } finally {
      setDeleting(false)
    }
  }

  const askInline = async (question) => {
    if (!question.trim()) return
    setAsking(true)
    setInlineAnswer("")
    try {
      const resp = await axios.post(`${API_BASE}/api/qa/ask`, { question })
      setInlineAnswer(resp.data.answer)
    } catch (err) {
      setInlineAnswer("Sorry, I couldn't process that query right now.")
    } finally {
      setAsking(false)
    }
  }

  const onDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const onDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFiles(droppedFiles)
  }, [])

  const handleFiles = (newFiles) => {
    const validFiles = newFiles.filter(f => f.type === 'application/pdf' || f.name.endsWith('.pdf'))
    if (validFiles.length < newFiles.length) {
        alert("Only PDF files are supported for now.")
    }
    setFiles(prev => [...prev, ...validFiles])
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const uploadAll = async () => {
    if (files.length === 0) return

    setUploading(true)
    setStatus({ message: "Neural Engine: Extracting semantics & generating study insights...", type: "loading" })
    setUploadResults(null)

    try {
      let lastResult = null
      
      for (const file of files) {
        const formData = new FormData()
        formData.append("file", file)
        
        const response = await axios.post(`${API_BASE}/api/document/upload`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 60000 // 60 seconds timeout
        })
        lastResult = response.data
      }
      
      setUploadResults(lastResult)
      // PERSIST: Save to local storage so it stays after navigation
      localStorage.setItem('last_doc_intel', JSON.stringify(lastResult))
      setStatus({ message: "Neural Analysis Complete! Documents are now indexed and AI insights are ready.", type: "success" })
      setFiles([])
    } catch (err) {
      console.error("Upload Error", err)
      let msg = "Neural Error: Connection timed out or server rejected the request."
      if (err.code === 'ECONNABORTED') msg = "The AI process is taking too long for this large document. Please try a smaller PDF."
      else if (err.response) msg = `Server Error (${err.response.status}): ${err.response.data?.detail || "The AI engine encountered an issue."}`
      
      setStatus({ message: msg, type: "error" })
    } finally {
      setUploading(false)
    }
  }

  const generateExistingNotes = async () => {
    if (!selectedDoc) return

    setUploading(true)
    setStatus({ message: "Neural Engine: Extracting semantics & generating study insights...", type: "loading" })
    setUploadResults(null)
    
    try {
      const response = await axios.get(`${API_BASE}/api/document/intel?filename=${encodeURIComponent(selectedDoc)}`, {
        timeout: 60000 
      })
      
      setUploadResults(response.data)
      localStorage.setItem('last_doc_intel', JSON.stringify(response.data))
      setStatus({ message: "Neural Analysis Complete! Documents are now indexed and AI insights are ready.", type: "success" })
    } catch (err) {
      console.error("Intel Error", err)
      let msg = "Neural Error: Connection timed out or server rejected the request."
      if (err.code === 'ECONNABORTED') msg = "The AI process is taking too long for this large document. Please try a smaller PDF."
      else if (err.response) msg = `Server Error (${err.response.status}): ${err.response.data?.detail || "The AI engine encountered an issue."}`
      
      setStatus({ message: msg, type: "error" })
    } finally {
      setUploading(false)
    }
  }

  const generateYoutubeNotes = async () => {
    if (!youtubeUrl.trim()) return

    setUploading(true)
    setStatus({ message: "Neural Engine: Extracting YouTube transcripts & generating intelligence...", type: "loading" })
    setUploadResults(null)
    
    try {
      const response = await axios.post(`${API_BASE}/api/document/youtube`, { url: youtubeUrl }, {
        timeout: 60000 
      })
      
      setUploadResults(response.data)
      localStorage.setItem('last_doc_intel', JSON.stringify(response.data))
      setStatus({ message: "YouTube Neural Parsing Complete!", type: "success" })
      setYoutubeUrl("")
    } catch (err) {
      console.error("YouTube Error", err)
      let msg = "Neural Error: Connection timed out or server rejected the request."
      if (err.response) msg = `Server Error (${err.response.status}): ${err.response.data?.detail || "The AI engine encountered an issue."}`
      
      setStatus({ message: msg, type: "error" })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-8 animate-in slide-in-from-right duration-500 max-w-7xl mx-auto pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-display">Document Intelligence</h1>
          <p className="text-slate-500">Upload materials to generate instant summaries and study notes.</p>
        </div>
        <div className="flex items-center gap-3 px-4 py-2 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100 font-bold text-sm shadow-sm">
            <ShieldCheck size={18} />
            Enterprise Encryption Active
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Drop Zone */}
        <div className="lg:col-span-2 space-y-6">
            {!uploadResults ? (
              <>
              <div 
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                className={`relative border-4 border-dashed rounded-[2rem] p-8 flex flex-col items-center justify-center text-center transition-all duration-300 group overflow-hidden ${isDragging ? 'border-primary bg-primary/5 scale-[1.01]' : 'border-slate-200 bg-white hover:border-primary/40 hover:bg-slate-50/50'}`}
              >
                <div className="w-full max-w-sm mb-6 flex bg-white/50 border border-slate-200 rounded-2xl p-2 items-center shadow-sm relative z-20">
                   <select 
                     value={selectedDoc}
                     onChange={(e) => setSelectedDoc(e.target.value)}
                     className="w-full bg-transparent border-none text-sm text-slate-700 font-bold focus:ring-0 outline-none"
                   >
                     <option value="">-- Choose Existing Material --</option>
                     {availableDocs.map((doc, idx) => (
                       <option key={idx} value={doc.filename}>{doc.filename}</option>
                     ))}
                   </select>
                   <button
                     onClick={generateExistingNotes}
                     disabled={!selectedDoc || uploading}
                     className="ml-2 bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 whitespace-nowrap"
                   >
                     Regenerate
                   </button>
                   <button
                     onClick={() => deleteDocument(selectedDoc)}
                     disabled={!selectedDoc || uploading || deleting}
                     className="ml-1 bg-rose-500 hover:bg-rose-600 text-white px-3 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 whitespace-nowrap flex items-center gap-1"
                     title="Delete selected PDF"
                   >
                     {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                   </button>
                </div>
              
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                
                <div className={`p-6 bg-white rounded-full shadow-xl mb-4 transition-transform duration-500 ${isDragging ? 'scale-110 rotate-6' : 'group-hover:scale-110'}`}>
                  <CloudUpload size={32} className={`transition-colors ${isDragging ? 'text-primary' : 'text-slate-300 group-hover:text-primary'}`} />
                </div>
                
                <h3 className="text-xl font-black text-slate-800 mb-1 tracking-tight">Drop Materials</h3>
                <p className="text-slate-400 max-w-xs text-xs font-medium mb-6">Drag and drop PDFs or click to browse.</p>
                
                <input 
                  type="file" 
                  multiple 
                  accept=".pdf"
                  className="hidden" 
                  id="fileInput" 
                  onChange={(e) => handleFiles(Array.from(e.target.files))}
                />
                <label 
                  htmlFor="fileInput"
                  className="gradient-btn cursor-pointer flex items-center gap-2 pr-4 z-10 py-2.5 text-xs h-10 shadow-md"
                >
                  <Plus size={16} />
                  Browse Library
                </label>
              </div>
              
              <div className="mt-6 p-8 border-4 border-dashed border-red-100 bg-white rounded-[2rem] hover:border-red-200 transition-all text-center group">
                 <div className="w-12 h-12 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                    <MonitorPlay size={24} />
                 </div>
                 <h3 className="text-xl font-black text-slate-800 mb-2 tracking-tight">YouTube Extraction</h3>
                 <p className="text-xs text-slate-400 mb-6 max-w-sm mx-auto font-medium">Instantly generate structured study notes from any educational YouTube video.</p>
                 <div className="flex gap-2 max-w-sm mx-auto shadow-sm rounded-xl">
                    <input 
                      type="text" 
                      placeholder="Paste YouTube Link here..." 
                      value={youtubeUrl}
                      onChange={(e) => setYoutubeUrl(e.target.value)}
                      className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-l-xl text-sm outline-none focus:ring-2 focus:ring-red-500/20 font-medium"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') generateYoutubeNotes()
                      }}
                    />
                    <button 
                      onClick={generateYoutubeNotes}
                      disabled={uploading || !youtubeUrl}
                      className="bg-red-500 text-white font-bold px-5 py-3 rounded-r-xl text-sm hover:bg-red-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      <Play size={16} className="fill-white" />
                      Extract
                    </button>
                 </div>
              </div>
              </>
            ) : (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-8"
              >
                {/* AI Summary Section */}
                <div className="bg-white rounded-[2.5rem] p-8 border border-slate-100 shadow-xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-8 text-primary/10 -rotate-12 group-hover:rotate-0 transition-transform duration-700">
                    <BookOpen size={120} />
                  </div>
                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="p-3 bg-primary/10 rounded-2xl text-primary">
                        <Layout size={24} />
                      </div>
                      <h3 className="text-2xl font-bold text-slate-800">Executive Summary</h3>
                    </div>
                    <div className="prose prose-slate max-w-none text-slate-600 leading-relaxed font-medium">
                      <ReactMarkdown>{uploadResults.summary}</ReactMarkdown>
                    </div>
                  </div>
                </div>

                {/* Key Points Section */}
                <div className="bg-slate-900 rounded-[2.5rem] p-8 border border-slate-800 shadow-2xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 blur-[100px] rounded-full"></div>
                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="p-3 bg-white/10 rounded-2xl text-primary shadow-lg">
                        <Star size={24} />
                      </div>
                      <h3 className="text-2xl font-bold text-white tracking-tight">Core Concept Notes</h3>
                    </div>
                    <div className="text-slate-300 leading-relaxed space-y-2">
                       <ReactMarkdown>{uploadResults.key_points}</ReactMarkdown>
                    </div>
                  </div>
                </div>

                {/* Quick Query System */}
                <div className="bg-white rounded-[2.5rem] p-8 border border-primary/20 shadow-xl">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 bg-secondary/10 rounded-2xl text-secondary">
                      <MessageSquare size={24} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-slate-800">Quick Document Query</h3>
                      <p className="text-xs text-slate-500 font-medium">Ask anything about this specific material.</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <input 
                      type="text" 
                      id="quick-query-input"
                      placeholder="e.g. What are the 3 main points mentioned here?"
                      className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') askInline(e.target.value)
                      }}
                    />
                    <button 
                      onClick={() => askInline(document.getElementById("quick-query-input").value)}
                      disabled={asking}
                      className="bg-primary text-white p-3 rounded-xl hover:bg-primary-dark transition-all shadow-lg shadow-primary/20 disabled:opacity-50"
                    >
                      {asking ? <Loader2 className="animate-spin" size={20} /> : <ArrowRight size={20} />}
                    </button>
                  </div>

                  {inlineAnswer && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-6 p-6 bg-slate-900 text-white rounded-3xl text-sm leading-relaxed relative border border-white/10"
                    >
                       <div className="absolute -top-3 left-6 px-3 py-1 bg-secondary text-[10px] font-black uppercase tracking-widest rounded-full">AI Response</div>
                       <ReactMarkdown>{inlineAnswer}</ReactMarkdown>
                    </motion.div>
                  )}
                  <p className="mt-3 text-[10px] text-slate-400 font-bold uppercase tracking-widest text-center">Powered by Neural Engine 4.0</p>
                </div>

                <button 
                  onClick={() => setUploadResults(null)}
                  className="bg-slate-100 text-slate-600 font-bold py-3 px-8 rounded-2xl hover:bg-slate-200 transition-all flex items-center justify-center gap-2 w-full max-w-xs mx-auto"
                >
                  <Plus size={18} />
                  Analyze New Document
                </button>
              </motion.div>
            )}

            {/* Status Feedback */}
            <AnimatePresence>
                {status && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className={`p-6 rounded-3xl border flex items-start gap-4 shadow-sm ${status.type === 'success' ? 'bg-emerald-50 border-emerald-100' : status.type === 'error' ? 'bg-rose-50 border-rose-100' : 'bg-primary/5 border-primary/10'}`}
                    >
                        <div className="shrink-0 mt-1">
                            {status.type === 'success' ? <CheckCircle2 className="text-emerald-500" /> : status.type === 'error' ? <XCircle className="text-rose-500" /> : <Loader2 className="animate-spin text-primary" />}
                        </div>
                        <div className="flex-1">
                            <h4 className={`font-bold text-sm uppercase tracking-widest ${status.type === 'success' ? 'text-emerald-700' : status.type === 'error' ? 'text-rose-700' : 'text-primary'}`}>
                                {status.type === 'success' ? 'Intel Complete' : status.type === 'error' ? 'Error' : 'Scanning Neural pathways'}
                            </h4>
                            <p className={`text-sm font-medium mt-1 leading-relaxed ${status.type === 'success' ? 'text-emerald-600' : status.type === 'error' ? 'text-rose-600' : 'text-slate-600'}`}>{status.message}</p>
                        </div>
                        <button onClick={() => setStatus(null)} className="text-slate-400 p-1 hover:text-slate-600 transition-colors">
                            <ChevronRight size={16} />
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>

        {/* File Queue Side Panel */}
        <div className="bg-white rounded-[2rem] p-8 border border-slate-100 shadow-sm border-b-4 border-b-primary/10 sticky top-24 h-fit">
            <h3 className="font-bold text-lg mb-6 flex items-center gap-2">
                Scan Queue 
                <span className="bg-slate-100 text-slate-500 text-[10px] py-0.5 px-2 rounded-full font-black uppercase tracking-widest">{files.length}</span>
            </h3>
            
            <div className="space-y-4 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
                {files.length === 0 ? (
                    <div className="text-center py-12 px-4 border-2 border-dashed border-slate-100 rounded-3xl opacity-50 flex flex-col items-center">
                        <FileText size={40} className="text-slate-200 mb-4" />
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Queue is currently empty</p>
                    </div>
                ) : (
                    files.map((f, i) => (
                        <motion.div 
                            key={i} 
                            initial={{ x: 20, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            className="p-4 bg-slate-50 rounded-2xl border border-slate-100 group flex items-center justify-between"
                        >
                            <div className="flex items-center gap-3">
                                <FileText className="text-primary" size={18} />
                                <div className="truncate w-32">
                                    <p className="text-xs font-bold text-slate-700 truncate">{f.name}</p>
                                    <p className="text-[10px] text-slate-400">{(f.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                            </div>
                            <button 
                                onClick={() => removeFile(i)}
                                className="p-2 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                            >
                                <Trash2 size={16} />
                            </button>
                        </motion.div>
                    ))
                )}
            </div>

            <div className="mt-12 space-y-4">
                <button 
                  onClick={uploadAll}
                  disabled={files.length === 0 || uploading}
                  className="w-full h-14 bg-slate-900 text-white rounded-2xl font-black uppercase tracking-widest text-xs flex items-center justify-center gap-3 shadow-2xl shadow-slate-900/40 hover:bg-slate-800 transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100 relative group overflow-hidden"
                >
                    <div className="absolute top-0 -left-full w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:left-full transition-all duration-1000"></div>
                    {uploading ? <Loader2 size={18} className="animate-spin" /> : <Zap size={18} className="text-primary" />}
                    Generate AI Study Notes
                </button>
                <div className="p-4 bg-primary/10 rounded-2xl border border-primary/10">
                    <p className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1 leading-tight flex items-center gap-1.5"><ShieldCheck size={10} /> Neural Precision Active</p>
                    <p className="text-[9px] text-slate-500 font-medium leading-relaxed">Our AI will automatically scan, summary, and extract key points from your PDF notes.</p>
                </div>
            </div>
        </div>
      </div>
    </div>
  )
}

export default Upload
