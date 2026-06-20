import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  BrainCircuit, 
  PlayCircle,
  FileQuestion,
  CheckCircle2,
  XCircle,
  Trophy,
  Loader2,
  RefreshCw,
  History
} from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://localhost:8000"

const Quiz = () => {
  const [activeTab, setActiveTab] = useState("take") // "take" or "history"
  const [loading, setLoading] = useState(false)
  const [availableDocs, setAvailableDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState("")
  
  // Quiz state
  const [questions, setQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState({}) // { questionIndex: "answer string" }
  const [quizFinished, setQuizFinished] = useState(false)
  const [score, setScore] = useState(0)
  
  // History state
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const generateQuiz = async () => {
    setLoading(true)
    setError("")
    try {
      const url = selectedDoc ? `${API_BASE}/api/quiz/generate?filename=${encodeURIComponent(selectedDoc)}` : `${API_BASE}/api/quiz/generate`
      const response = await axios.get(url)
      setQuestions(response.data.questions)
      setCurrentQuestionIndex(0)
      setSelectedAnswers({})
      setQuizFinished(false)
      setScore(0)
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || "Error generating quiz. Did you upload a PDF?")
    } finally {
      setLoading(false)
    }
  }

  const [error, setError] = useState("")

  const handleSelectAnswer = (option) => {
    if (quizFinished) return
    setSelectedAnswers({
      ...selectedAnswers,
      [currentQuestionIndex]: option
    })
  }

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }

  const submitQuiz = async () => {
    let finalScore = 0
    questions.forEach((q, idx) => {
      if (selectedAnswers[idx] === q.answer) {
        finalScore += 1
      }
    })
    setScore(finalScore)
    setQuizFinished(true)

    // Save to backend
    try {
      await axios.post(`${API_BASE}/api/quiz/submit`, {
        score: finalScore,
        total_questions: questions.length
      })
    } catch (err) {
      console.error("Failed to save score", err)
    }
  }

  const fetchHistory = async () => {
    setHistoryLoading(true)
    try {
      const response = await axios.get(`${API_BASE}/api/quiz/history`)
      setHistory(response.data.history)
    } catch (err) {
      console.error(err)
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === "history") {
      fetchHistory()
    }
  }, [activeTab])

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/document/list`)
        setAvailableDocs(res.data.documents)
        if (res.data.documents.length > 0) {
          setSelectedDoc(res.data.documents[0].filename)
        }
      } catch (err) {
        console.error("Failed to load document list", err)
      }
    }
    fetchDocs()
  }, [])

  return (
    <div className="space-y-8 animate-in slide-in-from-left duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-display">Knowledge Quiz</h1>
          <p className="text-slate-500">Test your understanding of the uploaded study material.</p>
        </div>
      </div>

      <div className="flex bg-slate-100 p-1 rounded-2xl w-fit mb-4">
        <button 
          onClick={() => setActiveTab("take")}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${activeTab === 'take' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
          <FileQuestion size={18} />
          Take Quiz
        </button>
        <button 
          onClick={() => setActiveTab("history")}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${activeTab === 'history' ? 'bg-white text-emerald-500 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
          <History size={18} />
          My Scores
        </button>
      </div>

      {activeTab === "take" && (
        <div className="space-y-6">
          {error && (
            <div className="bg-rose-50 text-rose-600 p-4 rounded-xl flex items-center gap-2 border border-rose-100">
              <XCircle size={20} />
              <span className="font-semibold">{error}</span>
            </div>
          )}

          {questions.length === 0 && !loading && (
            <div className="bg-white rounded-3xl p-12 border border-slate-100 shadow-sm text-center flex flex-col items-center justify-center">
              <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mb-6">
                <BrainCircuit size={40} className="text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-slate-800 mb-2">Ready to test your knowledge?</h2>
              <p className="text-slate-500 max-w-md mx-auto mb-6">
                We'll generate a custom multiple-choice quiz based on the PDF you select below.
              </p>
              
              {availableDocs.length > 0 ? (
                <div className="mb-8 w-full max-w-sm mx-auto">
                    <label className="block text-left text-sm font-bold text-slate-700 mb-2">Select Study Material</label>
                    <select 
                      value={selectedDoc}
                      onChange={(e) => setSelectedDoc(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-primary/20 outline-none"
                    >
                      {availableDocs.map((doc, idx) => (
                        <option key={idx} value={doc.filename}>{doc.filename}</option>
                      ))}
                    </select>
                </div>
              ) : (
                 <div className="mb-8 p-4 bg-orange-50 text-orange-600 rounded-xl border border-orange-100 text-sm font-medium">
                   No uploaded PDFs found. Please go to "Upload Notes" first.
                 </div>
              )}

              <button 
                onClick={generateQuiz}
                disabled={loading || availableDocs.length === 0}
                className="gradient-btn flex items-center gap-3 disabled:opacity-50"
              >
                <PlayCircle size={20} />
                Generate Quiz Now
              </button>
            </div>
          )}

          {loading && (
            <div className="bg-white rounded-3xl p-12 border border-slate-100 shadow-sm text-center flex flex-col items-center justify-center min-h-[400px]">
              <Loader2 size={48} className="animate-spin text-primary mb-4" />
              <h3 className="text-xl font-bold text-slate-800">Analyzing Document...</h3>
              <p className="text-slate-500">Crafting insightful questions based on your material.</p>
            </div>
          )}

          {questions.length > 0 && !quizFinished && !loading && (
            <div className="bg-white rounded-3xl p-8 lg:p-12 border border-slate-100 shadow-sm transition-all relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-slate-100">
                <motion.div 
                  className="h-full bg-primary"
                  initial={{ width: 0 }}
                  animate={{ width: `${((currentQuestionIndex) / questions.length) * 100}%` }}
                />
              </div>

              <div className="flex items-center justify-between mb-8">
                <span className="text-sm font-bold text-slate-400 uppercase tracking-wider">
                  Question {currentQuestionIndex + 1} of {questions.length}
                </span>
              </div>

              <h2 className="text-2xl font-bold text-slate-800 mb-8 leading-relaxed">
                {questions[currentQuestionIndex].question}
              </h2>

              <div className="space-y-4 mb-10">
                {questions[currentQuestionIndex].options.map((opt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectAnswer(opt)}
                    className={`w-full text-left p-5 rounded-2xl border-2 transition-all font-medium ${
                      selectedAnswers[currentQuestionIndex] === opt 
                        ? 'border-primary bg-primary/5 text-primary' 
                        : 'border-slate-100 hover:border-primary/30 hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-6">
                <button 
                  onClick={handlePrevious}
                  disabled={currentQuestionIndex === 0}
                  className="px-6 py-3 rounded-xl font-bold text-slate-500 hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                
                {currentQuestionIndex === questions.length - 1 ? (
                  <button 
                    onClick={submitQuiz}
                    disabled={!selectedAnswers[currentQuestionIndex]}
                    className="gradient-btn flex items-center gap-2 disabled:opacity-50"
                  >
                    <CheckCircle2 size={18} />
                    Submit Quiz
                  </button>
                ) : (
                  <button 
                    onClick={handleNext}
                    disabled={!selectedAnswers[currentQuestionIndex]}
                    className="bg-slate-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next Question
                  </button>
                )}
              </div>
            </div>
          )}

          {quizFinished && (
            <div className="space-y-8 animate-in fade-in zoom-in-95 duration-500">
              <div className="bg-white rounded-3xl p-10 border border-slate-100 shadow-xl overflow-hidden relative text-center">
                <div className="absolute -right-20 -top-20 w-64 h-64 blur-3xl rounded-full opacity-10 bg-primary"></div>
                
                <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6 text-primary">
                  <Trophy size={48} />
                </div>
                <h2 className="text-4xl font-black text-slate-900 mb-2 tracking-tight">Quiz Complete!</h2>
                <p className="text-slate-500 mb-8">You scored {score} out of {questions.length}</p>

                <div className="inline-flex items-center gap-4 px-6 py-3 bg-slate-50 rounded-2xl border border-slate-100 font-bold mb-8">
                  <span className="text-2xl text-slate-800">{Math.round((score / questions.length) * 100)}%</span>
                  <span className="text-slate-400">Accuracy</span>
                </div>

                <div className="flex justify-center">
                   <button onClick={generateQuiz} className="flex items-center gap-2 text-primary font-bold hover:underline">
                      <RefreshCw size={18} /> Create New Quiz
                   </button>
                </div>
              </div>

              <div className="space-y-6">
                <h3 className="text-2xl font-bold text-slate-800">Review Answers</h3>
                {questions.map((q, idx) => {
                  const isCorrect = selectedAnswers[idx] === q.answer
                  return (
                    <div key={idx} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                      <div className="flex items-start gap-4">
                        <div className="shrink-0 mt-1">
                          {isCorrect ? <CheckCircle2 className="text-emerald-500" size={24} /> : <XCircle className="text-rose-500" size={24} />}
                        </div>
                        <div>
                          <h4 className="font-bold text-lg text-slate-800 mb-4">{q.question}</h4>
                          <div className="space-y-2 mb-4">
                            {q.options.map((opt, optIdx) => {
                              let optionClass = "p-3 rounded-xl border text-sm "
                              if (opt === q.answer) {
                                optionClass += "border-emerald-500 bg-emerald-50 text-emerald-700 font-bold"
                              } else if (opt === selectedAnswers[idx] && !isCorrect) {
                                optionClass += "border-rose-300 bg-rose-50 text-rose-700"
                              } else {
                                optionClass += "border-slate-100 text-slate-500 bg-slate-50"
                              }
                              return (
                                <div key={optIdx} className={optionClass}>
                                  {opt}
                                </div>
                              )
                            })}
                          </div>
                          {!isCorrect && (
                             <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100 text-sm text-blue-800">
                               <span className="font-bold block mb-1">Explanation:</span>
                               {q.explanation}
                             </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "history" && (
        <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm animate-in fade-in duration-500">
           <h2 className="text-2xl font-bold text-slate-800 mb-6">Past Scores</h2>
           {historyLoading ? (
             <div className="flex justify-center p-10"><Loader2 className="animate-spin text-slate-400" size={32} /></div>
           ) : history.length === 0 ? (
             <div className="text-center p-10 text-slate-500">No quizzes taken yet.</div>
           ) : (
             <div className="space-y-4">
               {history.map((attempt) => (
                 <div key={attempt.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-5 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-colors">
                   <div className="flex items-center gap-4 mb-4 sm:mb-0">
                     <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-lg">
                       {Math.round((attempt.score / attempt.total_questions) * 100)}%
                     </div>
                     <div>
                       <p className="font-bold text-slate-800">Quiz Attempt #{attempt.id}</p>
                       <p className="text-xs text-slate-400">{new Date(attempt.created_at).toLocaleString()}</p>
                     </div>
                   </div>
                   <div className="text-sm font-semibold text-slate-600 bg-white px-4 py-2 rounded-lg border border-slate-100 shadow-sm">
                     {attempt.score} / {attempt.total_questions} Correct
                   </div>
                 </div>
               ))}
             </div>
           )}
        </div>
      )}
    </div>
  )
}

export default Quiz
