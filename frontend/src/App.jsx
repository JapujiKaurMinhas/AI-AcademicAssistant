import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LayoutDashboard, 
  MessageSquare, 
  Dna, 
  CloudUpload, 
  Bell, 
  Search, 
  Menu, 
  X,
  User,
  Zap,
  GraduationCap,
  Layers
} from 'lucide-react'

// Components
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import SemanticLab from './pages/SemanticLab'
import Upload from './pages/Upload'
import Quiz from './pages/Quiz'
import Flashcards from './pages/Flashcards'

const App = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const location = useLocation()

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar Overlay for Mobile */}
      {!isSidebarOpen && (
        <button 
          onClick={() => setIsSidebarOpen(true)}
          className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md lg:hidden"
        >
          <Menu size={20} />
        </button>
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-slate-900 text-slate-300 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex flex-col h-full p-6">
          <div className="flex items-center justify-between mb-12">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary rounded-xl">
                <Zap className="text-white" size={24} />
              </div>
              <span className="text-xl font-bold text-white tracking-tight">EduAI Pro</span>
            </div>
            <button className="lg:hidden" onClick={() => setIsSidebarOpen(false)}>
              <X size={20} />
            </button>
          </div>

          <nav className="flex-1 space-y-2">
            <NavItem to="/" icon={<LayoutDashboard size={20} />} label="Dashboard" />
            <NavItem to="/chat" icon={<MessageSquare size={20} />} label="AI Assistant" />
            <NavItem to="/semantic" icon={<Dna size={20} />} label="Semantic Lab" />
            <NavItem to="/upload" icon={<CloudUpload size={20} />} label="Upload Notes" />
            <NavItem to="/quiz" icon={<GraduationCap size={20} />} label="Knowledge Quiz" />
            <NavItem to="/flashcards" icon={<Layers size={20} />} label="Flashcards" />
          </nav>

          <div className="mt-auto p-4 bg-white/5 rounded-2xl flex items-center gap-3 border border-white/10">
            <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center font-bold text-white shadow-lg">
              JS
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Junior Scholar</p>
              <p className="text-xs text-slate-400">Basic Tier</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-h-screen pb-12 overflow-x-hidden">
        {/* Top Navbar */}
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 py-4 flex items-center justify-between">
          <div className="relative w-96 max-w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Search academic insights..."
              className="w-full bg-slate-100 border-none rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-primary/20 transition-all outline-none"
            />
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-slate-500 hover:bg-slate-100 rounded-xl transition-colors relative">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-secondary rounded-full border-2 border-white"></span>
            </button>
            <button 
              onClick={() => alert("Enterprise Tier: Unlock batch processing, 100k+ token context, and higher rate limits. Contact our academic sales team for institution licensing.")}
              className="hidden sm:block bg-gradient-to-r from-primary to-primary-dark text-white px-5 py-2 rounded-xl text-sm font-semibold shadow-lg shadow-primary/25 hover:scale-105 active:scale-95 transition-all"
            >
              Go Enterprise
            </button>
          </div>
        </header>

        {/* Dynamic Route Content */}
        <div className="p-8 max-w-7xl mx-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/semantic" element={<SemanticLab />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/quiz" element={<Quiz />} />
                <Route path="/flashcards" element={<Flashcards />} />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}

const NavItem = ({ to, icon, label }) => (
  <NavLink 
    to={to} 
    className={({ isActive }) => 
      `flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 group ${
        isActive 
          ? 'bg-primary text-white shadow-lg shadow-primary/30 font-semibold' 
          : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
      }`
    }
  >
    <span className="shrink-0 transition-transform duration-300 group-hover:scale-110">{icon}</span>
    <span className="text-sm tracking-wide">{label}</span>
  </NavLink>
)

export default App
