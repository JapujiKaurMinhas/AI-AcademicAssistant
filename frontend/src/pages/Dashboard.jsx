import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  FileText, 
  MessageSquare, 
  Mic, 
  Activity, 
  TrendingUp, 
  MoreVertical,
  ChevronRight,
  Clock,
  Sparkles,
  Trash2
} from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://localhost:8000" // FastAPI Port

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_uploads: 0,
    total_questions: 0,
    voice_commands: 12, // Mocked for now
    semantic_accuracy: 98.4
  })
  const [recentFiles, setRecentFiles] = useState([])

  const fetchFiles = async () => {
    try {
      const filesRes = await axios.get(`${API_BASE}/api/document/list`)
      setRecentFiles(filesRes.data.documents)
    } catch (err) {
      console.error("Failed to fetch files", err)
    }
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsRes = await axios.get(`${API_BASE}/api/analytics/`)
        setStats(prev => ({ ...prev, ...statsRes.data }))
      } catch (err) {
        console.error("Dashboard Fetch Failed", err)
      }
    }
    fetchData()
    fetchFiles()
  }, [])

  const deleteDocument = async (filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) return
    try {
      await axios.delete(`${API_BASE}/api/document/delete?filename=${encodeURIComponent(filename)}`)
      fetchFiles()
    } catch (err) {
      console.error("Delete Error", err)
      alert(err.response?.data?.detail || "Failed to delete the document.")
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slides-in-from-bottom duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-500 font-display">
            Analytics Overview
          </h1>
          <p className="text-slate-500">Monitor your academic productivity and insights.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500 bg-white px-4 py-2 rounded-xl border border-slate-100 shadow-sm self-start">
          <Clock size={16} />
          <span>Live Academic Cloud</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={<FileText className="text-indigo-600" />} 
          value={stats.total_uploads} 
          label="Total Uploads" 
          trend="+12% vs last week"
          color="bg-indigo-50"
        />
        <StatCard 
          icon={<MessageSquare className="text-pink-600" />} 
          value={stats.total_questions} 
          label="AI Questions" 
          trend="+24% engagement"
          color="bg-pink-50"
        />
        <StatCard 
          icon={<Mic className="text-orange-600" />} 
          value={stats.voice_commands} 
          label="Voice Commands" 
          trend="Increasing activity"
          color="bg-orange-50"
        />
        <StatCard 
          icon={<Activity className="text-emerald-600" />} 
          value={`${stats.semantic_accuracy}%`} 
          label="Semantic Match" 
          trend="Optimized confidence"
          color="bg-emerald-50"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart Section */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-8 border border-slate-100 shadow-sm border-b-4 border-b-primary/10 transition-transform duration-300 hover:scale-[1.01]">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <TrendingUp className="text-primary" size={20} />
              <h3 className="font-bold text-lg">Study Trends</h3>
            </div>
            <select className="bg-slate-50 border-none rounded-lg text-xs py-1.5 px-3 outline-none focus:ring-1 focus:ring-primary/20">
              <option>Last 7 Days</option>
              <option>Last Month</option>
            </select>
          </div>
          
          <div className="flex items-end justify-between h-48 gap-4 mt-12 pb-2">
            {[40, 60, 45, 90, 75, 85, 95].map((h, i) => (
              <motion.div 
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${h}%` }}
                transition={{ duration: 0.8, delay: i * 0.1, ease: "easeOut" }}
                className="flex-1 bg-gradient-to-t from-primary/52 to-primary rounded-t-lg relative group"
              >
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {h}% Growth
                </div>
              </motion.div>
            ))}
          </div>
          <div className="flex justify-between mt-4 text-[10px] text-slate-400 font-medium px-1 uppercase tracking-tight">
            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
          </div>
        </div>

        {/* Right Sidebar List */}
        <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm border-b-4 border-b-secondary/10">
          <div className="flex items-center justify-between mb-8">
            <h3 className="font-bold text-lg">Recent Files</h3>
            <button className="text-xs text-primary font-semibold hover:underline flex items-center gap-1">
              View All <ChevronRight size={12} />
            </button>
          </div>
          <div className="space-y-6 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
            {recentFiles.length > 0 ? (
              recentFiles.map((file, idx) => (
                <RecentFile key={idx} name={file.filename} time={file.upload_date} size={file.size} onDelete={deleteDocument} />
              ))
            ) : (
              <p className="text-slate-400 text-sm italic py-4">No documents uploaded yet.</p>
            )}
          </div>

          <div className="mt-12 bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-6 text-white overflow-hidden relative group">
             <div className="relative z-10">
               <Sparkles className="text-yellow-400 mb-4" size={24} />
               <p className="font-bold text-lg mb-2 leading-tight">Unlock AI Memory</p>
               <p className="text-slate-400 text-xs mb-4">Chat with thousands of documents simultaneously.</p>
               <button 
                  onClick={() => alert("Enterprise Tier: Please contact support for pricing.")}
                  className="w-full bg-primary text-white text-sm font-bold py-2.5 rounded-xl hover:bg-primary-dark transition-colors shadow-lg shadow-primary/20"
                >
                 Upgrade Pro
               </button>
             </div>
             <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-primary/20 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
          </div>
        </div>
      </div>
    </div>
  )
}

const StatCard = ({ icon, value, label, trend, color }) => (
  <div className="stat-card">
    <div className="flex items-center justify-between mb-4">
      <div className={`p-3 rounded-2xl ${color} shadow-sm group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <button className="text-slate-400 p-1 hover:bg-slate-50 rounded-lg transition-colors">
        <MoreVertical size={16} />
      </button>
    </div>
    <div className="text-3xl font-black text-slate-800 mb-1">{value}</div>
    <div className="text-slate-500 text-sm font-medium mb-2">{label}</div>
    <div className="text-[10px] text-emerald-500 font-bold uppercase tracking-wider">{trend}</div>
  </div>
)

const RecentFile = ({ name, time, size, onDelete }) => (
  <div 
    className="flex items-center justify-between group cursor-pointer"
  >
    <div className="flex items-center gap-4" onClick={() => alert("This file is indexed and ready for Chat. Use the AI Assistant to query it specifically.")}>
      <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center text-slate-400 group-hover:bg-primary/10 group-hover:text-primary transition-all">
        <FileText size={18} />
      </div>
      <div>
        <p className="text-sm font-bold text-slate-700 truncate w-32">{name}</p>
        <p className="text-[10px] text-slate-400 font-medium">{time} • {size}</p>
      </div>
    </div>
    <button 
      onClick={(e) => { e.stopPropagation(); onDelete(name); }}
      className="p-1.5 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
      title="Delete this PDF"
    >
      <Trash2 size={14} />
    </button>
  </div>
)

export default Dashboard
