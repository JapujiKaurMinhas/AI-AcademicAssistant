import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Layers,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Loader2,
  Zap,
  Shuffle,
  BookOpen,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  Star,
  Trophy,
  ArrowRight
} from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://localhost:8000"

const difficultyColors = {
  easy: { bg: 'bg-emerald-50', text: 'text-emerald-600', border: 'border-emerald-200', dot: 'bg-emerald-400' },
  medium: { bg: 'bg-amber-50', text: 'text-amber-600', border: 'border-amber-200', dot: 'bg-amber-400' },
  hard: { bg: 'bg-rose-50', text: 'text-rose-600', border: 'border-rose-200', dot: 'bg-rose-400' },
}

const Flashcards = () => {
  const [flashcards, setFlashcards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [loading, setLoading] = useState(false)
  const [availableDocs, setAvailableDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState("")
  const [cardCount, setCardCount] = useState(10)
  const [knownCards, setKnownCards] = useState(new Set())
  const [reviewCards, setReviewCards] = useState(new Set())
  const [studyMode, setStudyMode] = useState(false)
  const [source, setSource] = useState("")

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/document/list`)
        setAvailableDocs(res.data.documents)
      } catch (err) {
        console.error("Failed to load document list", err)
      }
    }
    fetchDocs()
  }, [])

  const generateFlashcards = async () => {
    setLoading(true)
    setFlashcards([])
    setCurrentIndex(0)
    setIsFlipped(false)
    setKnownCards(new Set())
    setReviewCards(new Set())
    setStudyMode(false)

    try {
      const params = new URLSearchParams({ count: cardCount })
      if (selectedDoc) params.append("filename", selectedDoc)

      const res = await axios.get(`${API_BASE}/api/flashcards/generate?${params}`, {
        timeout: 60000,
      })
      setFlashcards(res.data.flashcards)
      setSource(res.data.source)
    } catch (err) {
      console.error("Flashcard Error", err)
      alert(err.response?.data?.detail || "Failed to generate flashcards. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const nextCard = () => {
    setIsFlipped(false)
    setTimeout(() => {
      setCurrentIndex((prev) => (prev + 1) % flashcards.length)
    }, 150)
  }

  const prevCard = () => {
    setIsFlipped(false)
    setTimeout(() => {
      setCurrentIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length)
    }, 150)
  }

  const shuffleCards = () => {
    const shuffled = [...flashcards].sort(() => Math.random() - 0.5)
    setFlashcards(shuffled)
    setCurrentIndex(0)
    setIsFlipped(false)
  }

  const markKnown = () => {
    setKnownCards((prev) => new Set([...prev, currentIndex]))
    setReviewCards((prev) => { const n = new Set(prev); n.delete(currentIndex); return n })
    nextCard()
  }

  const markReview = () => {
    setReviewCards((prev) => new Set([...prev, currentIndex]))
    setKnownCards((prev) => { const n = new Set(prev); n.delete(currentIndex); return n })
    nextCard()
  }

  const startStudyMode = () => {
    if (reviewCards.size > 0) {
      const reviewIndices = Array.from(reviewCards)
      const reviewFlashcards = reviewIndices.map(i => flashcards[i])
      setFlashcards(reviewFlashcards)
      setCurrentIndex(0)
      setIsFlipped(false)
      setKnownCards(new Set())
      setReviewCards(new Set())
      setStudyMode(true)
    }
  }

  const currentCard = flashcards[currentIndex]
  const difficulty = currentCard ? difficultyColors[currentCard.difficulty] || difficultyColors.medium : null
  const progress = flashcards.length > 0 ? ((knownCards.size / flashcards.length) * 100) : 0

  // ───────── NO FLASHCARDS: Generator View ─────────
  if (flashcards.length === 0) {
    return (
      <div className="space-y-8 animate-in slide-in-from-right duration-500 max-w-7xl mx-auto pb-20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 font-display">Flashcard Generator</h1>
            <p className="text-slate-500">Create AI-powered flashcards from your study materials.</p>
          </div>
          <div className="flex items-center gap-3 px-4 py-2 bg-violet-50 text-violet-600 rounded-xl border border-violet-100 font-bold text-sm shadow-sm">
            <Layers size={18} />
            Smart Recall Engine
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Main Generator Card */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 text-violet-500/10 -rotate-12 group-hover:rotate-0 transition-transform duration-700">
                <Layers size={140} />
              </div>

              <div className="relative z-10 space-y-8">
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl text-white shadow-lg shadow-violet-500/30">
                    <Zap size={28} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-slate-800 tracking-tight">Generate Flashcards</h2>
                    <p className="text-sm text-slate-400 font-medium">AI extracts key concepts from your PDFs</p>
                  </div>
                </div>

                {/* Document Selector */}
                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Source Material</label>
                  <select
                    value={selectedDoc}
                    onChange={(e) => setSelectedDoc(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-5 py-4 text-sm text-slate-700 font-bold outline-none focus:ring-2 focus:ring-violet-500/20 transition-all"
                  >
                    <option value="">Latest uploaded document</option>
                    {availableDocs.map((doc, idx) => (
                      <option key={idx} value={doc.filename}>{doc.filename}</option>
                    ))}
                  </select>
                </div>

                {/* Card Count */}
                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Number of Cards</label>
                  <div className="flex items-center gap-3">
                    {[5, 10, 15, 20].map((n) => (
                      <button
                        key={n}
                        onClick={() => setCardCount(n)}
                        className={`flex-1 py-3 rounded-xl text-sm font-bold transition-all ${
                          cardCount === n
                            ? 'bg-violet-500 text-white shadow-lg shadow-violet-500/30 scale-105'
                            : 'bg-slate-50 text-slate-500 border border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Generate Button */}
                <button
                  onClick={generateFlashcards}
                  disabled={loading}
                  className="w-full h-16 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-2xl font-black uppercase tracking-widest text-sm flex items-center justify-center gap-3 shadow-2xl shadow-violet-600/40 hover:shadow-violet-600/60 transition-all active:scale-[0.98] disabled:opacity-50 relative group overflow-hidden"
                >
                  <div className="absolute top-0 -left-full w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:left-full transition-all duration-1000"></div>
                  {loading ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      Generating Flashcards...
                    </>
                  ) : (
                    <>
                      <Zap size={20} />
                      Generate Flashcards
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Side Info Panel */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[2rem] p-8 text-white relative overflow-hidden">
              <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-violet-500/20 rounded-full blur-3xl"></div>
              <div className="relative z-10">
                <BookOpen className="text-violet-400 mb-4" size={32} />
                <h3 className="text-xl font-bold mb-3">How It Works</h3>
                <div className="space-y-4 text-sm text-slate-300">
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 bg-violet-500/30 rounded-full flex items-center justify-center text-[10px] font-bold text-violet-300 shrink-0 mt-0.5">1</span>
                    <p>Select a PDF from your uploaded materials or use the latest one.</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 bg-violet-500/30 rounded-full flex items-center justify-center text-[10px] font-bold text-violet-300 shrink-0 mt-0.5">2</span>
                    <p>Our AI extracts key concepts, definitions, and facts.</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 bg-violet-500/30 rounded-full flex items-center justify-center text-[10px] font-bold text-violet-300 shrink-0 mt-0.5">3</span>
                    <p>Flip through cards, mark what you know, and focus on what needs review.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-[2rem] p-8 border border-slate-100 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <Star className="text-amber-400" size={20} />
                <h3 className="font-bold text-slate-800">Pro Tips</h3>
              </div>
              <ul className="space-y-3 text-xs text-slate-500 font-medium leading-relaxed">
                <li className="flex items-start gap-2"><span className="text-violet-500 mt-0.5">•</span> Use the shuffle feature to test recall in random order</li>
                <li className="flex items-start gap-2"><span className="text-violet-500 mt-0.5">•</span> Mark cards as "Review" to create a focused study deck</li>
                <li className="flex items-start gap-2"><span className="text-violet-500 mt-0.5">•</span> Try to answer before flipping for better retention</li>
                <li className="flex items-start gap-2"><span className="text-violet-500 mt-0.5">•</span> Generate new sets from different documents to broaden coverage</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ───────── FLASHCARD STUDY VIEW ─────────
  return (
    <div className="space-y-8 animate-in slide-in-from-right duration-500 max-w-7xl mx-auto pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-display">Flashcard Study</h1>
          <p className="text-slate-500 text-sm">
            Source: <span className="font-bold text-violet-600">{source}</span> • {flashcards.length} cards
            {studyMode && <span className="ml-2 text-amber-500 font-bold">(Review Mode)</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={shuffleCards}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-200 transition-all"
          >
            <Shuffle size={14} /> Shuffle
          </button>
          <button
            onClick={() => { setFlashcards([]); setSource(""); }}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-200 transition-all"
          >
            <RotateCcw size={14} /> New Deck
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4 text-xs font-bold">
            <span className="flex items-center gap-1.5 text-emerald-600"><CheckCircle2 size={14} /> Known: {knownCards.size}</span>
            <span className="flex items-center gap-1.5 text-amber-600"><Eye size={14} /> Review: {reviewCards.size}</span>
            <span className="flex items-center gap-1.5 text-slate-400"><EyeOff size={14} /> Unseen: {flashcards.length - knownCards.size - reviewCards.size}</span>
          </div>
          <span className="text-xs font-black text-violet-600 uppercase tracking-widest">{Math.round(progress)}% Mastered</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Card Area */}
        <div className="lg:col-span-3 space-y-6">
          {/* The Flashcard */}
          <div
            className="relative cursor-pointer"
            style={{ perspective: '1200px' }}
            onClick={() => setIsFlipped(!isFlipped)}
          >
            <motion.div
              className="relative w-full"
              style={{ transformStyle: 'preserve-3d' }}
              animate={{ rotateY: isFlipped ? 180 : 0 }}
              transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
            >
              {/* Front */}
              <div
                className="w-full min-h-[320px] bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl flex flex-col justify-between relative overflow-hidden"
                style={{ backfaceVisibility: 'hidden' }}
              >
                <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-violet-500 via-purple-500 to-pink-500"></div>
                <div className="absolute bottom-0 right-0 w-48 h-48 bg-violet-500/5 rounded-full blur-3xl"></div>

                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-8">
                    <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${difficulty?.bg} ${difficulty?.text} ${difficulty?.border} border`}>
                      {currentCard?.difficulty}
                    </div>
                    <span className={`px-3 py-1 bg-slate-50 text-slate-500 rounded-full text-[10px] font-bold border border-slate-100`}>
                      {currentCard?.category}
                    </span>
                  </div>
                  <h2 className="text-2xl font-black text-slate-800 leading-relaxed tracking-tight">
                    {currentCard?.front}
                  </h2>
                </div>

                <div className="flex items-center justify-center mt-8">
                  <span className="text-[10px] text-slate-300 font-bold uppercase tracking-widest flex items-center gap-2">
                    <RotateCcw size={12} /> Click to reveal answer
                  </span>
                </div>
              </div>

              {/* Back */}
              <div
                className="w-full min-h-[320px] bg-gradient-to-br from-slate-900 to-slate-800 rounded-[2.5rem] p-10 border border-slate-700 shadow-2xl flex flex-col justify-between absolute top-0 left-0 overflow-hidden"
                style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
              >
                <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-emerald-400 via-cyan-400 to-violet-400"></div>
                <div className="absolute bottom-0 right-0 w-48 h-48 bg-violet-500/10 rounded-full blur-3xl"></div>

                <div className="relative z-10">
                  <div className="flex items-center gap-2 mb-8">
                    <div className="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-[10px] font-black uppercase tracking-widest border border-emerald-500/30">
                      Answer
                    </div>
                  </div>
                  <p className="text-lg text-slate-200 leading-relaxed font-medium">
                    {currentCard?.back}
                  </p>
                </div>

                <div className="flex items-center justify-center mt-8">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest flex items-center gap-2">
                    <RotateCcw size={12} /> Click to see question
                  </span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Navigation & Actions */}
          <div className="flex items-center justify-between">
            <button
              onClick={prevCard}
              className="p-4 bg-white border border-slate-200 rounded-2xl text-slate-600 hover:bg-slate-50 transition-all shadow-sm hover:shadow-md active:scale-95"
            >
              <ChevronLeft size={24} />
            </button>

            <div className="flex items-center gap-3">
              <button
                onClick={markReview}
                className="flex items-center gap-2 px-6 py-3 bg-amber-50 text-amber-600 rounded-2xl text-sm font-bold border border-amber-200 hover:bg-amber-100 transition-all active:scale-95"
              >
                <XCircle size={18} /> Review Again
              </button>
              <button
                onClick={markKnown}
                className="flex items-center gap-2 px-6 py-3 bg-emerald-50 text-emerald-600 rounded-2xl text-sm font-bold border border-emerald-200 hover:bg-emerald-100 transition-all active:scale-95"
              >
                <CheckCircle2 size={18} /> Got It!
              </button>
            </div>

            <button
              onClick={nextCard}
              className="p-4 bg-white border border-slate-200 rounded-2xl text-slate-600 hover:bg-slate-50 transition-all shadow-sm hover:shadow-md active:scale-95"
            >
              <ChevronRight size={24} />
            </button>
          </div>

          {/* Card counter */}
          <div className="text-center">
            <span className="text-xs font-black text-slate-400 uppercase tracking-widest">
              Card {currentIndex + 1} of {flashcards.length}
            </span>
          </div>
        </div>

        {/* Right Panel: Card List */}
        <div className="bg-white rounded-[2rem] p-6 border border-slate-100 shadow-sm h-fit sticky top-24">
          <h3 className="font-bold text-sm mb-4 text-slate-800 flex items-center gap-2">
            <Layers size={16} className="text-violet-500" /> Card Overview
          </h3>
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
            {flashcards.map((card, idx) => (
              <button
                key={idx}
                onClick={() => { setCurrentIndex(idx); setIsFlipped(false) }}
                className={`w-full text-left p-3 rounded-xl text-xs font-medium transition-all border ${
                  idx === currentIndex
                    ? 'bg-violet-50 border-violet-200 text-violet-700 shadow-sm'
                    : knownCards.has(idx)
                    ? 'bg-emerald-50 border-emerald-100 text-emerald-600'
                    : reviewCards.has(idx)
                    ? 'bg-amber-50 border-amber-100 text-amber-600'
                    : 'bg-slate-50 border-slate-100 text-slate-500 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${
                    knownCards.has(idx) ? 'bg-emerald-400' : reviewCards.has(idx) ? 'bg-amber-400' : 'bg-slate-300'
                  }`}></span>
                  <span className="truncate">{card.front}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Study Review Button */}
          {reviewCards.size > 0 && (
            <button
              onClick={startStudyMode}
              className="w-full mt-4 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-2xl text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-amber-500/30 hover:shadow-amber-500/50 transition-all active:scale-95"
            >
              <Trophy size={16} /> Study {reviewCards.size} Review Cards
            </button>
          )}

          {/* Completion Celebration */}
          {knownCards.size === flashcards.length && flashcards.length > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-4 p-4 bg-gradient-to-br from-emerald-50 to-cyan-50 rounded-2xl border border-emerald-200 text-center"
            >
              <Trophy className="text-emerald-500 mx-auto mb-2" size={28} />
              <p className="text-sm font-bold text-emerald-700">All Cards Mastered!</p>
              <p className="text-[10px] text-emerald-500 font-medium mt-1">Outstanding work! 🎉</p>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Flashcards
