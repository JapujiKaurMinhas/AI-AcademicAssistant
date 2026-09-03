import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Zap, 
  Cpu, 
  Database, 
  AlertTriangle, 
  Gauge, 
  TrendingUp, 
  Play, 
  Layers, 
  Activity, 
  HelpCircle,
  FileText,
  DollarSign,
  CheckCircle2,
  Sliders,
  Download,
  Trash2,
  RefreshCw,
  Sparkles,
  ArrowRight,
  BarChart2,
  GitBranch,
  ShieldCheck,
  Compass,
  Award
} from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://localhost:8000"

const OptimizationDashboard = () => {
  const [activeTab, setActiveTab] = useState("runner") // "problem", "runner", "comparison", "pareto", "sensitivity", "history", "system"
  
  // Search Space & Specification
  const [searchSpace, setSearchSpace] = useState(null)
  const [algorithms, setAlgorithms] = useState([])
  const [availableDocs, setAvailableDocs] = useState([])
  const [activeConfig, setActiveConfig] = useState(null)

  // Runner Configuration State
  const [selectedAlgo, setSelectedAlgo] = useState("ga")
  const [selectedDoc, setSelectedDoc] = useState("")
  const [popSize, setPopSize] = useState(12)
  const [iterations, setIterations] = useState(8)
  const [randomSeed, setRandomSeed] = useState(42)
  const [numRuns, setNumRuns] = useState(3)
  const [isMultiRun, setIsMultiRun] = useState(false)

  // Algorithm Tunable Parameters
  const [crossoverProb, setCrossoverProb] = useState(0.85)
  const [mutationProb, setMutationProb] = useState(0.20)
  const [inertiaMax, setInertiaMax] = useState(0.90)
  const [inertiaMin, setInertiaMin] = useState(0.40)
  const [cognitiveCoeff, setCognitiveCoeff] = useState(1.70)
  const [socialCoeff, setSocialCoeff] = useState(1.70)
  const [gaRatio, setGaRatio] = useState(0.50)

  // Execution & Results State
  const [isRunning, setIsRunning] = useState(false)
  const [runProgress, setRunProgress] = useState(0)
  const [statusMessage, setStatusMessage] = useState("")
  const [latestResult, setLatestResult] = useState(null)
  const [statisticalResult, setStatisticalResult] = useState(null)

  // Comparison State
  const [comparisonResults, setComparisonResults] = useState(null)
  const [comparing, setComparing] = useState(false)

  // Sensitivity & Ablation State
  const [sensitivityData, setSensitivityData] = useState(null)
  const [ablationData, setAblationData] = useState(null)
  const [sweepLoading, setSweepLoading] = useState(false)

  // Experiments History
  const [experimentsList, setExperimentsList] = useState([])
  const [selectedExperiment, setSelectedExperiment] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(false)

  // System Benchmark State (Preserved)
  const [liveText, setLiveText] = useState("")
  const [liveLoading, setLiveLoading] = useState(false)
  const [liveResult, setLiveResult] = useState(null)
  const [systemMetrics, setSystemMetrics] = useState(null)
  const [systemLoading, setSystemLoading] = useState(false)

  useEffect(() => {
    fetchInitialData()
    fetchSystemMetrics()
  }, [])

  const fetchInitialData = async () => {
    try {
      const [spaceRes, algoRes, docRes, cfgRes, expRes] = await Promise.all([
        axios.get(`${API_BASE}/api/optimization/search-space`),
        axios.get(`${API_BASE}/api/optimization/algorithms`),
        axios.get(`${API_BASE}/api/document/list`),
        axios.get(`${API_BASE}/api/optimization/active-config`),
        axios.get(`${API_BASE}/api/optimization/experiments`)
      ])
      setSearchSpace(spaceRes.data)
      setAlgorithms(algoRes.data.algorithms || [])
      setAvailableDocs(docRes.data.documents || [])
      setActiveConfig(cfgRes.data)
      setExperimentsList(expRes.data.experiments || [])
    } catch (err) {
      console.error("Failed loading optimization metadata", err)
    }
  }

  const fetchExperiments = async () => {
    try {
      setHistoryLoading(true)
      const res = await axios.get(`${API_BASE}/api/optimization/experiments`)
      setExperimentsList(res.data.experiments || [])
    } catch (err) {
      console.error("Failed fetching experiments", err)
    } finally {
      setHistoryLoading(false)
    }
  }

  const fetchSystemMetrics = async () => {
    try {
      setSystemLoading(true)
      const res = await axios.get(`${API_BASE}/api/benchmark/system`)
      setSystemMetrics(res.data)
    } catch (err) {
      console.error("Failed to fetch system metrics", err)
    } finally {
      setSystemLoading(false)
    }
  }

  const runChunkingBenchmark = async () => {
    setLiveLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/api/benchmark/chunking`, { text: liveText })
      setLiveResult(res.data)
    } catch (err) {
      console.error("Failed to run chunking benchmark", err)
    } finally {
      setLiveLoading(false)
    }
  }

  // Run Optimization Handler
  const handleRunOptimization = async () => {
    setIsRunning(true)
    setRunProgress(15)
    setStatusMessage(`Initializing ${selectedAlgo.toUpperCase()} population and search bounds...`)
    
    try {
      const algoParams = {}
      if (selectedAlgo === "ga" || selectedAlgo === "nsga2" || selectedAlgo === "hybrid") {
        algoParams.crossover_prob = crossoverProb
        algoParams.mutation_prob = mutationProb
      }
      if (selectedAlgo === "pso" || selectedAlgo === "hybrid") {
        algoParams.inertia_weight_max = inertiaMax
        algoParams.inertia_weight_min = inertiaMin
        algoParams.cognitive_coeff = cognitiveCoeff
        algoParams.social_coeff = socialCoeff
      }
      if (selectedAlgo === "hybrid") {
        algoParams.ga_ratio = gaRatio
      }

      if (isMultiRun) {
        setStatusMessage(`Executing ${numRuns} stochastic runs with randomized seeds...`)
        setRunProgress(40)
        const res = await axios.post(`${API_BASE}/api/optimization/statistical`, {
          algorithm: selectedAlgo,
          num_runs: numRuns,
          population_size: popSize,
          iterations: iterations,
          random_seed: randomSeed,
          document_filename: selectedDoc || undefined
        })
        setRunProgress(100)
        setStatisticalResult(res.data)
        setLatestResult(res.data.best_run)
        setStatusMessage(`Completed ${numRuns} runs for ${res.data.algorithm}!`)
      } else {
        setStatusMessage(`Evaluating iterative generations across vector retrieval space...`)
        setRunProgress(45)
        const res = await axios.post(`${API_BASE}/api/optimization/run`, {
          algorithm: selectedAlgo,
          population_size: popSize,
          iterations: iterations,
          random_seed: randomSeed,
          document_filename: selectedDoc || undefined,
          algo_params: algoParams
        })
        setRunProgress(100)
        setLatestResult(res.data)
        setStatisticalResult(null)
        setStatusMessage(`Optimal configuration discovered via ${res.data.algorithm}!`)
      }
      fetchExperiments()
    } catch (err) {
      console.error("Optimization failed", err)
      setStatusMessage("Optimization execution failed. Please verify the backend logs.")
    } finally {
      setIsRunning(false)
    }
  }

  // Compare All Algorithms Handler
  const handleRunComparison = async () => {
    setComparing(true)
    try {
      const res = await axios.post(`${API_BASE}/api/optimization/compare?population_size=${popSize}&iterations=${iterations}&random_seed=${randomSeed}${selectedDoc ? `&document_filename=${encodeURIComponent(selectedDoc)}` : ''}`)
      setComparisonResults(res.data.results)
    } catch (err) {
      console.error("Comparison benchmark failed", err)
    } finally {
      setComparing(false)
    }
  }

  // Sensitivity Analysis Handler
  const handleRunSensitivity = async () => {
    setSweepLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/api/optimization/sensitivity`, {
        document_filename: selectedDoc || undefined
      })
      setSensitivityData(res.data)
    } catch (err) {
      console.error("Sensitivity failed", err)
    } finally {
      setSweepLoading(false)
    }
  }

  // Ablation Study Handler
  const handleRunAblation = async () => {
    setSweepLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/api/optimization/ablation`, {
        document_filename: selectedDoc || undefined,
        population_size: popSize,
        iterations: iterations,
        random_seed: randomSeed
      })
      setAblationData(res.data.stages)
    } catch (err) {
      console.error("Ablation study failed", err)
    } finally {
      setSweepLoading(false)
    }
  }

  // Apply Parameter Configuration to AI Academic Assistant
  const applyParametersToAssistant = async (params, sourceName) => {
    try {
      const res = await axios.post(`${API_BASE}/api/optimization/active-config`, {
        chunk_size: params.chunk_size,
        chunk_overlap: params.chunk_overlap,
        top_k: params.top_k,
        similarity_threshold: params.similarity_threshold,
        context_token_budget: params.context_token_budget,
        mode: "optimized",
        algorithm_source: sourceName || "Optimized Lab Candidate"
      })
      setActiveConfig(res.data.active_config)
      alert(`Applied to AI Academic Assistant!\n\nChunk Size: ${params.chunk_size}\nOverlap: ${params.chunk_overlap}\nTop-K: ${params.top_k}\nThreshold: ${params.similarity_threshold}\nToken Budget: ${params.context_token_budget}`)
    } catch (err) {
      console.error("Failed to apply configuration", err)
      alert("Error applying active configuration.")
    }
  }

  // Export Experiment Handler
  const handleExport = (expId, format) => {
    window.open(`${API_BASE}/api/optimization/export/${expId}?format=${format}`, "_blank")
  }

  // Delete Experiment Handler
  const handleDeleteExperiment = async (expId) => {
    if (!window.confirm(`Delete experiment record #${expId}?`)) return
    try {
      await axios.delete(`${API_BASE}/api/optimization/experiments/${expId}`)
      fetchExperiments()
    } catch (err) {
      console.error("Failed deleting experiment", err)
    }
  }

  // SVG Chart: Fitness vs Generation & Diversity
  const renderConvergenceChart = (convergenceHistory) => {
    if (!convergenceHistory || convergenceHistory.length === 0) return null
    const width = 600
    const height = 220
    const padding = 35

    const bestFits = convergenceHistory.map(p => p.best_fitness)
    const meanFits = convergenceHistory.map(p => p.mean_fitness)
    const diversities = convergenceHistory.map(p => p.diversity)
    const minVal = Math.min(...meanFits, ...bestFits) * 0.95
    const maxVal = Math.max(...bestFits, 1.0) * 1.05
    const range = maxVal - minVal || 1.0

    const xStep = (width - padding * 2) / (convergenceHistory.length - 1 || 1)

    const bestPoints = convergenceHistory.map((p, i) => ({
      x: padding + i * xStep,
      y: height - padding - ((p.best_fitness - minVal) / range) * (height - padding * 2)
    }))

    const meanPoints = convergenceHistory.map((p, i) => ({
      x: padding + i * xStep,
      y: height - padding - ((p.mean_fitness - minVal) / range) * (height - padding * 2)
    }))

    let bestPath = ""
    bestPoints.forEach((pt, i) => bestPath += (i === 0 ? `M ${pt.x} ${pt.y}` : ` L ${pt.x} ${pt.y}`))

    let meanPath = ""
    meanPoints.forEach((pt, i) => meanPath += (i === 0 ? `M ${pt.x} ${pt.y}` : ` L ${pt.x} ${pt.y}`))

    return (
      <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <TrendingUp size={14} className="text-emerald-400" />
            Convergence Trajectory (Fitness vs Generation)
          </span>
          <div className="flex items-center gap-3 text-[11px] font-mono">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-2.5 h-0.5 bg-emerald-400 inline-block"></span> Best Fitness
            </span>
            <span className="flex items-center gap-1 text-blue-400">
              <span className="w-2.5 h-0.5 bg-blue-400 inline-block"></span> Mean Fitness
            </span>
          </div>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible font-mono">
          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#334155" strokeWidth="0.5" strokeDasharray="3,3" />
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#334155" strokeWidth="0.5" strokeDasharray="3,3" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#334155" strokeWidth="1" />
          
          {/* Axis Labels */}
          <text x={padding - 5} y={padding + 5} fill="#64748b" fontSize="9" textAnchor="end">{maxVal.toFixed(3)}</text>
          <text x={padding - 5} y={height - padding} fill="#64748b" fontSize="9" textAnchor="end">{minVal.toFixed(3)}</text>

          {/* Area fill for best fitness */}
          {bestPoints.length > 1 && (
            <path
              d={`${bestPath} L ${bestPoints[bestPoints.length - 1].x} ${height - padding} L ${bestPoints[0].x} ${height - padding} Z`}
              fill="url(#grad-fitness)"
              opacity="0.2"
            />
          )}

          {/* Mean Fitness Curve */}
          <path d={meanPath} fill="none" stroke="#60a5fa" strokeWidth="1.8" strokeDasharray="4,4" />

          {/* Best Fitness Curve */}
          <path d={bestPath} fill="none" stroke="#10b981" strokeWidth="2.5" />

          {/* Node Markers */}
          {bestPoints.map((pt, i) => (
            <g key={i}>
              <circle cx={pt.x} cy={pt.y} r="3" fill="#10b981" />
              <text x={pt.x} y={height - padding + 14} fill="#64748b" fontSize="9" textAnchor="middle">
                {convergenceHistory[i].iteration}
              </text>
            </g>
          ))}

          <defs>
            <linearGradient id="grad-fitness" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#064e3b" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>

        <div className="flex justify-between text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-800">
          <span>Initial Generation (Exploration)</span>
          <span>Iteration / Generation &rarr;</span>
          <span>Final Convergence (Exploitation)</span>
        </div>
      </div>
    )
  }

  // SVG Chart: Population Diversity & Premature Convergence
  const renderDiversityChart = (diversityHistory) => {
    if (!diversityHistory || diversityHistory.length === 0) return null
    const width = 500
    const height = 140
    const padding = 25
    const xStep = (width - padding * 2) / (diversityHistory.length - 1 || 1)

    const points = diversityHistory.map((d, i) => ({
      x: padding + i * xStep,
      y: height - padding - Math.min(1.0, d) * (height - padding * 2)
    }))

    let path = ""
    points.forEach((p, i) => path += (i === 0 ? `M ${p.x} ${p.y}` : ` L ${p.x} ${p.y}`))

    // Threshold line for premature convergence (0.05)
    const threshY = height - padding - 0.05 * (height - padding * 2)

    return (
      <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 space-y-2">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1">
            <Compass size={13} className="text-amber-400" />
            Population Diversity Index
          </span>
          <span className="text-[10px] text-amber-400 bg-amber-950/50 px-2 py-0.5 rounded border border-amber-800 font-mono">
            Critical Threshold &le; 0.05
          </span>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto font-mono">
          <line x1={padding} y1={threshY} x2={width - padding} y2={threshY} stroke="#f59e0b" strokeWidth="1" strokeDasharray="3,3" />
          <path d={path} fill="none" stroke="#38bdf8" strokeWidth="2" />
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="2.5" fill="#38bdf8" />
          ))}
        </svg>

        <div className="flex justify-between text-[9px] text-slate-500 font-mono">
          <span>Gen 1 (Max Dispersion)</span>
          <span>Normalized Hypercube Distance</span>
          <span>Gen {diversityHistory.length} (Cluster)</span>
        </div>
      </div>
    )
  }

  // SVG Chart: NSGA-II Pareto Front
  const renderParetoFront = (paretoSolutions) => {
    if (!paretoSolutions || paretoSolutions.length === 0) return null
    const width = 500
    const height = 240
    const padding = 40

    const qualities = paretoSolutions.map(s => s.quality)
    const latencies = paretoSolutions.map(s => s.latency_ms)
    const minQ = Math.min(...qualities) * 0.95
    const maxQ = Math.max(...qualities) * 1.05
    const minL = Math.min(...latencies) * 0.85
    const maxL = Math.max(...latencies) * 1.15

    return (
      <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Award size={14} className="text-amber-400" />
              Non-Dominated Pareto Front (Quality vs Latency)
            </h4>
            <p className="text-[11px] text-slate-400">Click any Pareto solution to inspect parameters and apply to the AI Assistant.</p>
          </div>
          <span className="text-[10px] bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800 font-mono font-bold">
            {paretoSolutions.length} Pareto-Optimal Points
          </span>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible font-mono">
          {/* Axis lines */}
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#475569" strokeWidth="1" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#475569" strokeWidth="1" />

          {/* Grid ticks */}
          <text x={padding - 8} y={padding + 10} fill="#94a3b8" fontSize="9" textAnchor="end">Quality &uarr;</text>
          <text x={width - padding} y={height - padding + 20} fill="#94a3b8" fontSize="9" textAnchor="end">Latency (ms) &rarr;</text>

          {paretoSolutions.map((sol, i) => {
            const x = padding + ((sol.latency_ms - minL) / (maxL - minL || 1)) * (width - padding * 2)
            const y = height - padding - ((sol.quality - minQ) / (maxQ - minQ || 1)) * (height - padding * 2)

            return (
              <g key={i} className="cursor-pointer group" onClick={() => applyParametersToAssistant(sol.parameters, `NSGA-II Pareto Solution #${i+1}`)}>
                <circle 
                  cx={x} 
                  cy={y} 
                  r="5" 
                  fill="#f59e0b" 
                  className="transition-all hover:r-7 stroke-2 stroke-slate-900"
                />
                <text x={x + 7} y={y + 3} fill="#e2e8f0" fontSize="8" className="opacity-0 group-hover:opacity-100 transition-opacity">
                  Q:{sol.quality.toFixed(3)} | {sol.latency_ms}ms
                </text>
              </g>
            )
          })}
        </svg>

        {/* Pareto solutions cards list */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-48 overflow-y-auto pr-1">
          {paretoSolutions.map((sol, i) => (
            <div key={i} className="bg-slate-800/80 border border-slate-700 p-2.5 rounded-xl text-[11px] flex justify-between items-center">
              <div>
                <span className="font-bold text-amber-400 mr-1">#{i+1}</span>
                <span className="text-slate-300">Q: <strong>{sol.quality.toFixed(3)}</strong></span>
                <span className="text-slate-500 mx-1">|</span>
                <span className="text-slate-300">{sol.latency_ms}ms</span>
                <span className="text-slate-500 mx-1">|</span>
                <span className="text-slate-300">{sol.tokens}tok</span>
              </div>
              <button
                onClick={() => applyParametersToAssistant(sol.parameters, `NSGA-II Pareto #${i+1}`)}
                className="bg-primary/20 text-primary hover:bg-primary hover:text-white px-2 py-0.5 rounded text-[10px] font-bold transition-all"
              >
                Apply
              </button>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-wider">
            <Gauge size={16} className="animate-spin text-primary" />
            <span>Optimization Techniques for Artificial Intelligence</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            Optimization Laboratory
          </h1>
          <p className="text-slate-500 text-sm max-w-2xl leading-relaxed">
            Formulating document retrieval parameter selection as a multi-objective constrained optimization problem.
            Evaluates evolutionary (GA, NSGA-II) and swarm-based (PSO, GWO, Hybrid) metaheuristics against empirical baselines.
          </p>
        </div>

        {/* Current Active Assistant Config Status Card */}
        {activeConfig && (
          <div className="bg-slate-900 text-white p-4 rounded-2xl border border-slate-800 shadow-md min-w-[260px] space-y-2 font-mono">
            <div className="flex items-center justify-between text-xs border-b border-slate-800 pb-1.5">
              <span className="text-slate-400 font-bold uppercase">Active In Assistant</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                activeConfig.mode === "optimized" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-slate-800 text-slate-300"
              }`}>
                {activeConfig.mode.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-300">
              <div>Chunk: <strong>{activeConfig.chunk_size}</strong></div>
              <div>Overlap: <strong>{activeConfig.chunk_overlap}</strong></div>
              <div>Top-K: <strong>{activeConfig.top_k}</strong></div>
              <div>Cutoff: <strong>{activeConfig.similarity_threshold}</strong></div>
            </div>
            <div className="text-[10px] text-slate-500 truncate pt-1">
              Source: {activeConfig.algorithm_source || 'Default'}
            </div>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        {[
          { id: "runner", label: "Algorithm Runner", icon: <Play size={16} /> },
          { id: "problem", label: "Problem Formulation", icon: <FileText size={16} /> },
          { id: "comparison", label: "Algorithm Comparison", icon: <BarChart2 size={16} /> },
          { id: "sensitivity", label: "Sensitivity & Ablation", icon: <Sliders size={16} /> },
          { id: "history", label: "Experiment History", icon: <Database size={16} /> },
          { id: "system", label: "System Sandbox", icon: <Cpu size={16} /> },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === tab.id
                ? "bg-slate-900 text-white shadow-md shadow-slate-950/20"
                : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* TAB 1: ALGORITHM RUNNER */}
      {activeTab === "runner" && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Experiment Configuration Panel */}
            <div className="lg:col-span-1 bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-5">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Sliders size={18} className="text-primary" />
                Experiment Configuration
              </h2>

              {/* Algorithm Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">Select Algorithm</label>
                <select
                  value={selectedAlgo}
                  onChange={(e) => setSelectedAlgo(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:ring-2 focus:ring-primary/20 outline-none"
                >
                  <option value="baseline">Baseline (Manual Default)</option>
                  <option value="ga">Genetic Algorithm (GA)</option>
                  <option value="pso">Particle Swarm Optimization (PSO)</option>
                  <option value="gwo">Grey Wolf Optimizer (GWO)</option>
                  <option value="nsga2">NSGA-II (Multi-Objective)</option>
                  <option value="hybrid">Hybrid GA + PSO</option>
                </select>
              </div>

              {/* Target Document */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">Dataset / Academic Document</label>
                <select
                  value={selectedDoc}
                  onChange={(e) => setSelectedDoc(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:ring-2 focus:ring-primary/20 outline-none truncate"
                >
                  <option value="">Standard Academic Benchmark Paper (Built-in)</option>
                  {availableDocs.map((d, i) => (
                    <option key={i} value={d.filename}>{d.filename}</option>
                  ))}
                </select>
              </div>

              {/* Common Population & Iterations */}
              {selectedAlgo !== "baseline" && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-600 block">Population / Swarm</label>
                    <input 
                      type="number"
                      min="4"
                      max="40"
                      value={popSize}
                      onChange={(e) => setPopSize(parseInt(e.target.value) || 10)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-mono outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-600 block">Iterations / Gens</label>
                    <input 
                      type="number"
                      min="2"
                      max="30"
                      value={iterations}
                      onChange={(e) => setIterations(parseInt(e.target.value) || 6)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-mono outline-none"
                    />
                  </div>
                </div>
              )}

              {/* Random Seed */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-slate-600 block">Deterministic Random Seed</label>
                <input 
                  type="number"
                  value={randomSeed}
                  onChange={(e) => setRandomSeed(parseInt(e.target.value) || 42)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-mono outline-none"
                />
              </div>

              {/* Algorithm-Specific Parameter Tuning (Dynamic based on selected algorithm) */}
              {(selectedAlgo === "ga" || selectedAlgo === "nsga2" || selectedAlgo === "hybrid") && (
                <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Evolutionary Hyperparameters</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-500 block">Crossover Rate</label>
                      <input 
                        type="number" step="0.05" min="0.1" max="1.0" 
                        value={crossoverProb} 
                        onChange={(e) => setCrossoverProb(parseFloat(e.target.value))}
                        className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500 block">Mutation Rate</label>
                      <input 
                        type="number" step="0.05" min="0.01" max="0.5" 
                        value={mutationProb} 
                        onChange={(e) => setMutationProb(parseFloat(e.target.value))}
                        className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono"
                      />
                    </div>
                  </div>
                </div>
              )}

              {(selectedAlgo === "pso" || selectedAlgo === "hybrid") && (
                <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Swarm Velocity Coefficients</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-500 block">Inertia (Max &rarr; Min)</label>
                      <input 
                        type="text" 
                        value={`${inertiaMax} - ${inertiaMin}`}
                        readOnly
                        className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono text-slate-600"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500 block">Cognitive / Social</label>
                      <input 
                        type="text" 
                        value={`${cognitiveCoeff} / ${socialCoeff}`}
                        readOnly
                        className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono text-slate-600"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Stochastic Multi-Run Toggle */}
              {selectedAlgo !== "baseline" && (
                <div className="pt-2 border-t border-slate-100 space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-slate-700">
                    <input 
                      type="checkbox" 
                      checked={isMultiRun} 
                      onChange={(e) => setIsMultiRun(e.target.checked)}
                      className="rounded text-primary focus:ring-primary w-4 h-4"
                    />
                    <span>Multi-Run Statistical Analysis (N runs)</span>
                  </label>
                  {isMultiRun && (
                    <div className="flex items-center gap-2 pl-6">
                      <span className="text-xs text-slate-500">Number of Runs:</span>
                      <input 
                        type="number" 
                        min="2" 
                        max="10" 
                        value={numRuns} 
                        onChange={(e) => setNumRuns(parseInt(e.target.value) || 3)}
                        className="w-16 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Run Button */}
              <button
                onClick={handleRunOptimization}
                disabled={isRunning}
                className="w-full bg-primary hover:bg-primary-dark text-white rounded-xl py-3.5 text-sm font-bold shadow-lg shadow-primary/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <Activity size={18} className="animate-spin" />
                    Running Optimization...
                  </>
                ) : (
                  <>
                    <Play size={18} fill="white" />
                    {isMultiRun ? `Execute ${numRuns} Statistical Runs` : "Run Optimization"}
                  </>
                )}
              </button>

              {/* Live progress indicator */}
              {isRunning && (
                <div className="space-y-1.5 pt-2">
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>{statusMessage}</span>
                    <span>{runProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <motion.div 
                      className="h-full bg-primary"
                      initial={{ width: 0 }}
                      animate={{ width: `${runProgress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Live Results & Visualization Area */}
            <div className="lg:col-span-2 space-y-6">
              {latestResult ? (
                <div className="space-y-6 animate-in fade-in duration-300">
                  {/* Results Summary Header */}
                  <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Discovered Result</span>
                        <h3 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                          <CheckCircle2 size={20} className="text-emerald-500" />
                          {latestResult.algorithm}
                        </h3>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => applyParametersToAssistant(latestResult.best_parameters, latestResult.algorithm)}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white px-3.5 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md shadow-emerald-600/25 transition-all"
                        >
                          <Sparkles size={14} />
                          Apply to Assistant
                        </button>
                        {latestResult.experiment_id && (
                          <button
                            onClick={() => handleExport(latestResult.experiment_id, "json")}
                            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 transition-all"
                            title="Export JSON"
                          >
                            <Download size={14} />
                            JSON
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Discovered Best Parameters Badges */}
                    <div className="space-y-2">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Optimal Decision Vector X*</span>
                      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
                        <ParamBadge label="Chunk Size" val={`${latestResult.best_parameters.chunk_size} ch`} />
                        <ParamBadge label="Chunk Overlap" val={`${latestResult.best_parameters.chunk_overlap} ch`} />
                        <ParamBadge label="Top-K Chunks" val={`k = ${latestResult.best_parameters.top_k}`} />
                        <ParamBadge label="Similarity Cutoff" val={`&ge; ${latestResult.best_parameters.similarity_threshold}`} />
                        <ParamBadge label="Token Budget" val={`${latestResult.best_parameters.context_token_budget} tok`} />
                      </div>
                    </div>

                    {/* Measured Performance Metrics */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                      <MetricBadge label="Best Fitness" val={latestResult.best_fitness.toFixed(4)} highlight={true} />
                      <MetricBadge label="Retrieval Quality" val={latestResult.metrics.retrieval_quality.toFixed(4)} />
                      <MetricBadge label="Retrieval Latency" val={`${latestResult.metrics.latency_ms} ms`} />
                      <MetricBadge label="Token Count" val={`${latestResult.metrics.estimated_tokens} tokens`} />
                    </div>

                    {/* Premature Convergence Banner if detected */}
                    {latestResult.premature_convergence_detected && (
                      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-3 text-xs text-amber-800 flex items-center gap-2">
                        <AlertTriangle size={18} className="text-amber-600 shrink-0" />
                        <span><strong>Possible Premature Convergence Detected:</strong> Population diversity dropped below 0.05 before 50% of the optimization iterations. Adaptive mutation or inertia expansion recommended.</span>
                      </div>
                    )}
                  </div>

                  {/* Multi-Run Statistical Summary (if executed) */}
                  {statisticalResult && (
                    <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-3">
                      <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <Activity size={16} className="text-primary" />
                        Statistical Evaluation Summary ({statisticalResult.num_runs} Stochastic Runs)
                      </h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left">
                          <thead>
                            <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase">
                              <th className="py-2">Metric</th>
                              <th>Mean</th>
                              <th>Std Dev (&sigma;)</th>
                              <th>Min</th>
                              <th>Max</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 font-mono">
                            <tr>
                              <td className="py-2 font-bold font-sans text-slate-700">Fitness</td>
                              <td className="text-emerald-600 font-bold">{statisticalResult.fitness.mean}</td>
                              <td>&plusmn;{statisticalResult.fitness.std}</td>
                              <td>{statisticalResult.fitness.min}</td>
                              <td>{statisticalResult.fitness.max}</td>
                            </tr>
                            <tr>
                              <td className="py-2 font-bold font-sans text-slate-700">Retrieval Quality</td>
                              <td className="text-blue-600 font-bold">{statisticalResult.retrieval_quality.mean}</td>
                              <td>&plusmn;{statisticalResult.retrieval_quality.std}</td>
                              <td>{statisticalResult.retrieval_quality.min}</td>
                              <td>{statisticalResult.retrieval_quality.max}</td>
                            </tr>
                            <tr>
                              <td className="py-2 font-bold font-sans text-slate-700">Latency (ms)</td>
                              <td>{statisticalResult.latency_ms.mean} ms</td>
                              <td>&plusmn;{statisticalResult.latency_ms.std}</td>
                              <td>{statisticalResult.latency_ms.min} ms</td>
                              <td>{statisticalResult.latency_ms.max} ms</td>
                            </tr>
                            <tr>
                              <td className="py-2 font-bold font-sans text-slate-700">Estimated Tokens</td>
                              <td>{statisticalResult.tokens.mean} tok</td>
                              <td>&plusmn;{statisticalResult.tokens.std}</td>
                              <td>{statisticalResult.tokens.min}</td>
                              <td>{statisticalResult.tokens.max}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Convergence Trajectory Chart */}
                  {renderConvergenceChart(latestResult.convergence_history)}

                  {/* Diversity / Exploration Chart */}
                  {latestResult.diversity_history && latestResult.diversity_history.length > 0 && (
                    renderDiversityChart(latestResult.diversity_history)
                  )}

                  {/* NSGA-II Pareto Front (if Pareto points available) */}
                  {latestResult.pareto_front && (
                    renderParetoFront(latestResult.pareto_front)
                  )}
                </div>
              ) : (
                <div className="bg-white p-12 rounded-3xl border border-dashed border-slate-200 flex flex-col items-center justify-center text-center space-y-3">
                  <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-400">
                    <Gauge size={28} className="animate-pulse" />
                  </div>
                  <h3 className="text-base font-bold text-slate-800">No Experiment Results in Current Session</h3>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Select an algorithm (Baseline, GA, PSO, GWO, NSGA-II, or Hybrid) and click <strong>Run Optimization</strong> to perform real vector retrieval parameter discovery.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PROBLEM FORMULATION */}
      {activeTab === "problem" && (
        <div className="space-y-6">
          <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-6">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Mathematical Problem Formulation</h2>
              <p className="text-xs text-slate-500 mt-1">
                Formal specification of decision variables, boundaries, constraints, and multi-criteria fitness objectives.
              </p>
            </div>

            {/* Decision Vector */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">1. Decision Vector</h3>
              <div className="bg-slate-900 text-slate-200 p-4 rounded-2xl font-mono text-xs select-all">
                X = [ x_1: chunk_size, x_2: chunk_overlap, x_3: top_k, x_4: similarity_threshold, x_5: context_token_budget ]
              </div>
            </div>

            {/* Search Space Table */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">2. Decision Variables & Realistic Bounds</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase">
                      <th className="py-2.5">Variable</th>
                      <th>Physical Meaning</th>
                      <th>Lower Bound (L)</th>
                      <th>Upper Bound (U)</th>
                      <th>Type</th>
                      <th>Baseline Default</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    <tr>
                      <td className="py-2 font-bold font-sans text-slate-800">chunk_size (x_1)</td>
                      <td className="font-sans text-slate-600">Text slice character length</td>
                      <td>200 chars</td>
                      <td>1500 chars</td>
                      <td>Integer</td>
                      <td>800</td>
                    </tr>
                    <tr>
                      <td className="py-2 font-bold font-sans text-slate-800">chunk_overlap (x_2)</td>
                      <td className="font-sans text-slate-600">Contextual boundary overlap</td>
                      <td>0 chars</td>
                      <td>300 chars</td>
                      <td>Integer</td>
                      <td>100</td>
                    </tr>
                    <tr>
                      <td className="py-2 font-bold font-sans text-slate-800">top_k (x_3)</td>
                      <td className="font-sans text-slate-600">Number of candidate chunks retrieved</td>
                      <td>1 chunk</td>
                      <td>20 chunks</td>
                      <td>Integer</td>
                      <td>3</td>
                    </tr>
                    <tr>
                      <td className="py-2 font-bold font-sans text-slate-800">similarity_threshold (x_4)</td>
                      <td className="font-sans text-slate-600">Cosine cutoff for vector relevance</td>
                      <td>0.00</td>
                      <td>1.00</td>
                      <td>Float</td>
                      <td>0.20</td>
                    </tr>
                    <tr>
                      <td className="py-2 font-bold font-sans text-slate-800">context_token_budget (x_5)</td>
                      <td className="font-sans text-slate-600">Maximum token ceiling injected into prompt</td>
                      <td>500 tokens</td>
                      <td>6000 tokens</td>
                      <td>Integer</td>
                      <td>3000</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Objective Function Formulation */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">3. Objective Functions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2">
                  <span className="text-xs font-bold text-slate-800 block">Single-Objective Fitness Function (GA / PSO / GWO / Hybrid)</span>
                  <div className="bg-slate-900 text-slate-200 font-mono text-[11px] p-3 rounded-xl">
                    Fitness(X) = w1 * RetrievalQuality + w2 * SemanticSim + w3 * Coverage - w4 * NormLatency - w5 * NormTokens - Penalty
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Default weights: w1=0.35, w2=0.25, w3=0.15, w4=0.15, w5=0.10.
                  </p>
                </div>
                <div className="bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2">
                  <span className="text-xs font-bold text-slate-800 block">Multi-Objective Formulation (NSGA-II)</span>
                  <div className="bg-slate-900 text-slate-200 font-mono text-[11px] p-3 rounded-xl space-y-1">
                    <div>Obj 1: Maximize f_1(X) = Composite Retrieval Quality</div>
                    <div>Obj 2: Minimize f_2(X) = Retrieval Latency (ms)</div>
                    <div>Obj 3: Minimize f_3(X) = Token Consumption</div>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Generates non-dominated Pareto front surfaces without fixed scalar weights.
                  </p>
                </div>
              </div>
            </div>

            {/* Constraints */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">4. Physical & Structural Constraints</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <ConstraintCard id="C1" rule="chunk_overlap < chunk_size" desc="Overlap must be strictly smaller than segmentation size." />
                <ConstraintCard id="C2" rule="chunk_overlap <= 0.5 * chunk_size" desc="Enforces max 50% overlap to prevent excessive redundancy." />
                <ConstraintCard id="C3" rule="top_k >= 1" desc="At least one chunk must be selected for answer grounding." />
                <ConstraintCard id="C4" rule="500 <= context_token_budget <= 6000" desc="Respects Groq LLM prompt token limits." />
                <ConstraintCard id="C5" rule="estimated_tokens <= context_token_budget" desc="Total context injected cannot exceed budget." />
                <ConstraintCard id="C6" rule="L_i <= x_i <= U_i" desc="All parameters must satisfy lower/upper bounds." />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: ALGORITHM COMPARISON */}
      {activeTab === "comparison" && (
        <div className="space-y-6">
          <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Multi-Algorithm Comparative Benchmark</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Direct empirical comparison across all 6 optimizers evaluated on the exact same document and query set.
                </p>
              </div>
              <button
                onClick={handleRunComparison}
                disabled={comparing}
                className="bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md transition-all disabled:opacity-50"
              >
                {comparing ? <Activity size={16} className="animate-spin" /> : <Play size={16} fill="white" />}
                Run Full Comparison Benchmark
              </button>
            </div>

            {comparisonResults ? (
              <div className="space-y-6">
                {/* Comparison Table */}
                <div className="overflow-x-auto border border-slate-200 rounded-2xl">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-500 font-bold uppercase border-b border-slate-200">
                      <tr>
                        <th className="py-3 px-4">Algorithm</th>
                        <th>Quality</th>
                        <th>Semantic Sim</th>
                        <th>Coverage</th>
                        <th>Latency</th>
                        <th>Tokens</th>
                        <th>Fitness</th>
                        <th>Runtime</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono">
                      {comparisonResults.map((r, i) => (
                        <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                          <td className="py-3 px-4 font-bold font-sans text-slate-800 flex items-center gap-2">
                            {r.algorithm.includes("Baseline") ? (
                              <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                            ) : (
                              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                            )}
                            {r.algorithm}
                          </td>
                          <td className="font-bold text-blue-600">{r.retrieval_quality.toFixed(4)}</td>
                          <td>{r.semantic_similarity.toFixed(4)}</td>
                          <td>{r.context_coverage.toFixed(4)}</td>
                          <td>{r.latency_ms} ms</td>
                          <td>{r.estimated_tokens} tok</td>
                          <td className="font-bold text-emerald-600">{r.best_fitness.toFixed(4)}</td>
                          <td className="text-slate-400">{r.runtime_seconds}s</td>
                          <td>
                            <button
                              onClick={() => applyParametersToAssistant(r.best_parameters, r.algorithm)}
                              className="text-primary hover:text-primary-dark font-bold font-sans text-[11px] underline"
                            >
                              Apply
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Comparative Bar Visualization */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-slate-50 border border-slate-200 p-5 rounded-2xl space-y-3">
                    <span className="text-xs font-bold text-slate-700 block">Retrieval Quality Comparison (Higher = Better)</span>
                    <div className="space-y-2">
                      {comparisonResults.map((r, i) => {
                        const maxQ = Math.max(...comparisonResults.map(x => x.retrieval_quality), 1.0)
                        const pct = (r.retrieval_quality / maxQ) * 100
                        return (
                          <div key={i} className="space-y-1">
                            <div className="flex justify-between text-[11px]">
                              <span className="font-medium text-slate-700">{r.algorithm}</span>
                              <span className="font-bold font-mono text-blue-600">{r.retrieval_quality.toFixed(4)}</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                              <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 p-5 rounded-2xl space-y-3">
                    <span className="text-xs font-bold text-slate-700 block">Fitness Score Comparison (Higher = Better)</span>
                    <div className="space-y-2">
                      {comparisonResults.map((r, i) => {
                        const maxF = Math.max(...comparisonResults.map(x => x.best_fitness), 1.0)
                        const pct = Math.max(10, (r.best_fitness / maxF) * 100)
                        return (
                          <div key={i} className="space-y-1">
                            <div className="flex justify-between text-[11px]">
                              <span className="font-medium text-slate-700">{r.algorithm}</span>
                              <span className="font-bold font-mono text-emerald-600">{r.best_fitness.toFixed(4)}</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                              <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400 border border-dashed border-slate-200 rounded-2xl">
                <BarChart2 size={36} className="mx-auto mb-2 text-slate-300 stroke-1" />
                <p className="text-xs font-semibold text-slate-600">No comparative benchmark has been run yet.</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Click 'Run Full Comparison Benchmark' to compute real metrics across all algorithms.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: SENSITIVITY & ABLATION */}
      {activeTab === "sensitivity" && (
        <div className="space-y-8">
          {/* Action Bar */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleRunSensitivity}
              disabled={sweepLoading}
              className="bg-primary hover:bg-primary-dark text-white px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md transition-all disabled:opacity-50"
            >
              {sweepLoading ? <Activity size={16} className="animate-spin" /> : <Sliders size={16} />}
              Run Parameter Sensitivity Sweeps
            </button>
            <button
              onClick={handleRunAblation}
              disabled={sweepLoading}
              className="bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md transition-all disabled:opacity-50"
            >
              {sweepLoading ? <Activity size={16} className="animate-spin" /> : <GitBranch size={16} />}
              Run 5-Stage Ablation Study
            </button>
          </div>

          {/* Sensitivity Results */}
          {sensitivityData && (
            <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-6">
              <h3 className="text-lg font-bold text-slate-900">Parameter Sensitivity Profiles</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Top-K Sensitivity */}
                <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
                  <span className="text-xs font-bold text-slate-700 block">Top-K vs Retrieval Quality</span>
                  <div className="space-y-2 font-mono text-xs">
                    {sensitivityData.top_k_sensitivity.map((pt, i) => (
                      <div key={i} className="flex justify-between items-center py-1 border-b border-slate-200/60">
                        <span className="text-slate-600">k = {pt.top_k}</span>
                        <span className="text-blue-600 font-bold">Quality: {pt.retrieval_quality.toFixed(4)}</span>
                        <span className="text-slate-400">{pt.latency_ms}ms</span>
                        <span className="text-slate-400">{pt.estimated_tokens}tok</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Chunk Size Sensitivity */}
                <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
                  <span className="text-xs font-bold text-slate-700 block">Chunk Size vs Quality & Latency</span>
                  <div className="space-y-2 font-mono text-xs">
                    {sensitivityData.chunk_size_sensitivity.map((pt, i) => (
                      <div key={i} className="flex justify-between items-center py-1 border-b border-slate-200/60">
                        <span className="text-slate-600">{pt.chunk_size} chars</span>
                        <span className="text-blue-600 font-bold">Quality: {pt.retrieval_quality.toFixed(4)}</span>
                        <span className="text-slate-400">{pt.latency_ms}ms</span>
                        <span className="text-slate-400">{pt.total_chunks} chunks</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Ablation Study Results */}
          {ablationData && (
            <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-6">
              <h3 className="text-lg font-bold text-slate-900">Ablation Study (Component Contribution Analysis)</h3>
              <div className="overflow-x-auto border border-slate-200 rounded-2xl">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-500 font-bold uppercase border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4">Stage</th>
                      <th>Configuration</th>
                      <th>Optimized Parameters</th>
                      <th>Quality</th>
                      <th>Latency</th>
                      <th>Tokens</th>
                      <th>Fitness</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {ablationData.map((st, i) => (
                      <tr key={i} className={i === ablationData.length - 1 ? "bg-emerald-50/50 font-bold" : ""}>
                        <td className="py-3 px-4 font-bold font-sans text-slate-800">Stage {st.stage}</td>
                        <td className="font-sans text-slate-700">{st.name}</td>
                        <td className="text-slate-500 font-sans">{st.optimized_parameters.join(", ")}</td>
                        <td className="text-blue-600 font-bold">{st.quality.toFixed(4)}</td>
                        <td>{st.latency_ms} ms</td>
                        <td>{st.tokens} tok</td>
                        <td className="text-emerald-600 font-bold">{st.fitness.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 5: EXPERIMENT HISTORY & EXPORT */}
      {activeTab === "history" && (
        <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Historical Optimization Experiments</h2>
              <p className="text-xs text-slate-500">Persistent storage of past algorithmic runs, parameter sets, and metrics.</p>
            </div>
            <button
              onClick={fetchExperiments}
              className="text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition-all"
            >
              <RefreshCw size={13} className={historyLoading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>

          {experimentsList.length > 0 ? (
            <div className="overflow-x-auto border border-slate-200 rounded-2xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-500 font-bold uppercase border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">ID</th>
                    <th>Date/Time</th>
                    <th>Algorithm</th>
                    <th>Dataset</th>
                    <th>Pop / Gens</th>
                    <th>Fitness</th>
                    <th>Parameters Discovered</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {experimentsList.map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="py-3 px-4 font-bold text-slate-800">#{exp.id}</td>
                      <td className="text-slate-500 font-sans">{exp.created_at}</td>
                      <td className="font-bold text-slate-800 font-sans">{exp.algorithm}</td>
                      <td className="text-slate-600 truncate max-w-[120px] font-sans">{exp.dataset_name}</td>
                      <td>{exp.population_size} / {exp.iterations}</td>
                      <td className="text-emerald-600 font-bold">{exp.best_fitness.toFixed(4)}</td>
                      <td className="text-[10px] text-slate-500">
                        {exp.parameters.chunk_size}ch / {exp.parameters.chunk_overlap}ov / k={exp.parameters.top_k}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => applyParametersToAssistant(exp.parameters, exp.algorithm)}
                            className="text-emerald-600 hover:text-emerald-700 font-bold font-sans text-[11px]"
                            title="Apply to Assistant"
                          >
                            Apply
                          </button>
                          <button
                            onClick={() => handleExport(exp.id, "json")}
                            className="text-slate-400 hover:text-slate-600"
                            title="Download JSON"
                          >
                            <Download size={14} />
                          </button>
                          <button
                            onClick={() => handleDeleteExperiment(exp.id)}
                            className="text-rose-400 hover:text-rose-600"
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 border border-dashed border-slate-200 rounded-2xl">
              <Database size={36} className="mx-auto mb-2 text-slate-300 stroke-1" />
              <p className="text-xs font-semibold text-slate-600">No experiments stored in database yet.</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Run an optimization in the 'Algorithm Runner' to persist experiment data.</p>
            </div>
          )}
        </div>
      )}

      {/* TAB 6: PRESERVED SYSTEM SANDBOX (Preserves original chunking distance & system bar charts) */}
      {activeTab === "system" && (
        <div className="space-y-8">
          {/* Live Chunking Benchmark Sandbox */}
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
            <div>
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Activity className="text-primary" size={20} />
                Live Chunking Benchmark Sandbox
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Input a custom paragraph or use the default text. The backend computes sentence vector embeddings and validates semantic cohesion vs fixed chunking.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 space-y-3">
                <label className="text-xs font-bold text-slate-600 block">Benchmark Input Text</label>
                <textarea
                  value={liveText}
                  onChange={(e) => setLiveText(e.target.value)}
                  placeholder="Paste academic text here to test semantic chunk alignment..."
                  className="w-full h-56 bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs font-mono focus:ring-2 focus:ring-primary/20 outline-none resize-none"
                />
                <button
                  onClick={runChunkingBenchmark}
                  disabled={liveLoading}
                  className="w-full bg-slate-900 text-white rounded-xl py-3 text-sm font-semibold hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
                >
                  {liveLoading ? <Activity size={16} className="animate-spin" /> : <Play size={16} fill="white" />}
                  Run Chunking Benchmark
                </button>
              </div>

              <div className="lg:col-span-2">
                {liveResult ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl text-center">
                        <span className="text-[10px] text-slate-400 font-semibold block">Within-Chunk MSE</span>
                        <span className="text-base font-extrabold text-emerald-600 font-mono">{liveResult.semantic_metrics.within_chunk_distance_mse}</span>
                      </div>
                      <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl text-center">
                        <span className="text-[10px] text-slate-400 font-semibold block">Boundary Contrast</span>
                        <span className="text-base font-extrabold text-blue-600 font-mono">{liveResult.semantic_metrics.boundary_shift_distance}</span>
                      </div>
                      <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl text-center">
                        <span className="text-[10px] text-slate-400 font-semibold block">Broken Sentences</span>
                        <span className="text-base font-extrabold text-emerald-600 font-mono">{liveResult.semantic_metrics.broken_sentences}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-full bg-slate-50 border border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center p-8 text-slate-400">
                    <Gauge size={32} className="stroke-1 text-slate-300 mb-1" />
                    <p className="text-xs font-semibold">Press 'Run Chunking Benchmark' to test</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const ParamBadge = ({ label, val }) => (
  <div className="bg-slate-50 border border-slate-200 p-2.5 rounded-xl text-center">
    <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">{label}</span>
    <span className="text-xs font-bold text-slate-800 font-mono">{val}</span>
  </div>
)

const MetricBadge = ({ label, val, highlight }) => (
  <div className={`p-3 rounded-xl border text-center ${
    highlight ? "bg-emerald-50 border-emerald-200" : "bg-slate-50 border-slate-200"
  }`}>
    <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">{label}</span>
    <span className={`text-base font-extrabold font-mono ${highlight ? "text-emerald-700" : "text-slate-800"}`}>
      {val}
    </span>
  </div>
)

const ConstraintCard = ({ id, rule, desc }) => (
  <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-2xl space-y-1">
    <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-slate-700">
      <span className="bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded text-[10px]">{id}</span>
      <span>{rule}</span>
    </div>
    <p className="text-[11px] text-slate-500">{desc}</p>
  </div>
)

export default OptimizationDashboard
