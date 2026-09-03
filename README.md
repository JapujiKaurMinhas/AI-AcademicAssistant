# 🎓 Optimization-Driven AI Academic Assistant

An enterprise-grade, research-oriented AI platform that combines Retrieval-Augmented Generation (RAG) with **Metaheuristic Optimization Techniques for Artificial Intelligence**. Built with **FastAPI**, **React 19**, **Vite**, **Tailwind CSS**, and powered by **Sentence-Transformers** (`all-MiniLM-L6-v2`) and **Groq Cloud LLMs** (`groq/compound`, `groq/compound-mini`).

---

## 🔬 Research Problem & Objective

### 1. Research Motivation
Standard Retrieval-Augmented Generation (RAG) pipelines rely on manually chosen, arbitrary retrieval hyperparameters—such as chunk size, chunk overlap, top-K retrieved passages, and cosine similarity thresholds. In academic settings, poorly tuned parameters result in either:
- **Information Starvation**: Suboptimal chunks missing critical mathematical equations, citations, and definitions.
- **Context Fragmentation**: Overlapping redundant snippets that consume excessive LLM token budgets and increase response latency.

### 2. Research Title & Formulation
> **"Multi-Objective Optimization of Retrieval Parameters in an AI Academic Assistant Using Evolutionary and Swarm-Based Metaheuristic Algorithms"**

**Primary Research Question:**
*Can evolutionary and swarm-based metaheuristic optimization automatically discover superior retrieval parameters that simultaneously maximize academic retrieval relevance and semantic alignment while minimizing latency and token consumption compared with manually configured baselines?*

---

## 📐 Mathematical Problem Formulation

### Decision Variable Vector
Each candidate retrieval configuration is represented as a 5-dimensional decision vector:
$$X = [x_1, x_2, x_3, x_4, x_5]$$

| Variable | Physical Meaning | Search Bounds $[L_i, U_i]$ | Variable Type | Default Baseline |
| :--- | :--- | :--- | :--- | :--- |
| **$x_1$ (`chunk_size`)** | Text chunk length in characters | $[200, 1500]$ | Integer | $800$ |
| **$x_2$ (`chunk_overlap`)** | Consecutive boundary overlap | $[0, 300]$ | Integer | $100$ |
| **$x_3$ (`top_k`)** | Retrieved chunk count | $[1, 20]$ | Integer | $3$ |
| **$x_4$ (`similarity_threshold`)**| Minimum cosine cutoff | $[0.0, 1.0]$ | Continuous | $0.20$ |
| **$x_5$ (`context_token_budget`)**| Prompt token limit | $[500, 6000]$ | Integer | $3000$ |

### Objective Functions

#### 1. Single-Objective Composite Fitness
$$\text{Maximize } \text{Fitness}(X) = w_1 \cdot Q_{\text{retrieval}} + w_2 \cdot Q_{\text{semantic}} + w_3 \cdot Q_{\text{coverage}} - w_4 \cdot \tilde{T}_{\text{latency}} - w_5 \cdot \tilde{C}_{\text{tokens}} - \text{Penalty}(X)$$

Where:
- $Q_{\text{retrieval}}$: Mean cosine similarity of top-$k$ retrieved chunks to benchmark queries.
- $Q_{\text{semantic}}$: Query-to-context semantic alignment (top chunk cosine score).
- $Q_{\text{coverage}}$: Passage diversity score ($1.0 - \text{mean pairwise similarity}$ of retrieved chunks, discouraging redundant snippets).
- $\tilde{T}_{\text{latency}}$: Normalized retrieval latency $\in [0, 1]$.
- $\tilde{C}_{\text{tokens}}$: Normalized context token consumption $\in [0, 1]$.
- Default weights: $w_1 = 0.35, w_2 = 0.25, w_3 = 0.15, w_4 = 0.15, w_5 = 0.10$.

#### 2. Multi-Objective Formulation (NSGA-II)
$$\text{Maximize } f_1(X) = Q_{\text{composite}}$$
$$\text{Minimize } f_2(X) = T_{\text{latency}} \text{ (ms)}$$
$$\text{Minimize } f_3(X) = C_{\text{tokens}}$$

### Physical Constraints
1. **$C_1$**: $x_2 < x_1$ (Overlap must be strictly smaller than chunk size).
2. **$C_2$**: $x_2 \le 0.5 \cdot x_1$ (Overlap capped at 50% to prevent excessive redundancy).
3. **$C_3$**: $x_3 \ge 1$ (At least one chunk retrieved for grounding).
4. **$C_4$**: $500 \le x_5 \le 6000$ (Budget bounded by model context capacity).
5. **$C_5$**: $\text{EstimatedTokens}(X) \le x_5$ (Total context cannot exceed budget).
6. **$C_6$**: $L_i \le x_i \le U_i, \forall i \in \{1, \dots, 5\}$ (Parameter boundaries).

---

## 🧬 Implemented Metaheuristic Optimizers

1. **Baseline (Deterministic Control)**:
   - Evaluates standard manual defaults ($800$ ch, $100$ ov, $k=3$, $\theta=0.20$, $3000$ tok) under the identical protocol.
2. **Genetic Algorithm (GA)**:
   - Real chromosome representation, tournament selection, Simulated Binary / Arithmetic crossover, Gaussian mutation, elitism, and diversity-adaptive mutation rates.
3. **Particle Swarm Optimization (PSO)**:
   - Particle velocity and position equations with personal best ($pBest$), global best ($gBest$), and time-varying adaptive inertia weight $w(t) = w_{\max} - (w_{\max} - w_{\min}) \cdot \frac{t}{T}$.
4. **Grey Wolf Optimizer (GWO)**:
   - Social hierarchy ($\alpha, \beta, \delta, \omega$) with encircling and hunting mechanisms, controlled by exploration-exploitation coefficient $a(t) = 2 \cdot (1 - \frac{t}{T})$.
5. **NSGA-II (Multi-Objective)**:
   - Fast non-dominated sorting into Pareto fronts ($F_1, F_2, \dots$), crowding distance assignment, crowded tournament selection, and $(2N \to N)$ elitist replacement.
6. **Hybrid GA + PSO**:
   - Two-phase metaheuristic: Phase 1 executes GA for global search across disparate basins; Phase 2 seeds the PSO swarm with elite chromosomes for local exploitation and fine-tuning.

---

## 📊 Scientific Features

- **Population Diversity Tracking**: Measures normalized Euclidean distance across chromosomes/particles over generations.
- **Premature Convergence Detection**: Flags runs where diversity drops below $0.05$ before $50\%$ of iterations.
- **Parameter Sensitivity Sweeps**: Empirical curves for Top-K vs Quality, Chunk Size vs Latency, and Threshold vs Retrieved Count.
- **5-Stage Component Ablation Study**:
  - Stage A: No optimization (Baseline)
  - Stage B: Chunk Size only
  - Stage C: Chunk Size + Overlap
  - Stage D: Retrieval parameters (Top-K + Cutoff)
  - Stage E: Full 5-parameter co-optimization
- **Stochastic Multi-Run Statistical Analysis**: Computes Mean, Standard Deviation ($\sigma$), Minimum, and Maximum over $N$ randomized runs.
- **Zero Fabrication**: All charts, Pareto fronts, and tables derive strictly from executed evaluations.

---

## 🔌 Real Pipeline Integration & Retrieval Modes

Discovered parameters directly govern the AI Academic Assistant's active retrieval engine:
- **Retrieval Mode: [ Default | Optimized ]**: Toggleable directly from the Chat UI.
- **Active Configuration Badges**: Live display of current Chunk Size, Overlap, Top-K, Cutoff, and Token Budget.
- **Source Citations**: Chat outputs display retrieved evidence chunks along with cosine similarity scores.

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI (Async REST API)
- **Embeddings & Vector Retrieval**: Sentence-Transformers (`all-MiniLM-L6-v2`), PyTorch, Scikit-Learn, NumPy
- **Optimization Algorithms**: GA, PSO, GWO, NSGA-II, Hybrid GA+PSO (Custom native implementations)
- **Database**: SQLite with SQLModel / SQLAlchemy ORM
- **LLM Engine**: Groq API (`groq/compound`, `groq/compound-mini`)
- **PDF Extraction**: PyPDF2, pdfplumber

### **Frontend**
- **Framework**: React 19 + Vite 8
- **Styling**: Tailwind CSS 4 + PostCSS
- **Animations & Visualizations**: Framer Motion, Native SVG Charting Engines
- **Routing & Client**: React Router DOM v7, Axios

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Node.js v18+
- Python 3.10+
- Groq API Key

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # On Windows
# source venv/bin/activate     # On Linux/macOS
pip install -r requirements.txt
python main.py
```
*API will run on `http://localhost:8000` (`/docs` for Swagger UI).*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Web app will run on `http://localhost:5173`.*

### 4. Running the Optimization Test Suite
```bash
cd backend
venv\Scripts\python -m pytest tests/test_optimization.py -v
```

---

## 🧪 How to Run an Optimization Experiment

1. Navigate to **Optimization Lab** (`/optimization`) in the sidebar.
2. In the **Algorithm Runner** tab:
   - Select an algorithm (**GA**, **PSO**, **GWO**, **NSGA-II**, **Hybrid GA+PSO**, or **Baseline**).
   - Choose an uploaded academic document or the standard benchmark paper.
   - Configure population size, iterations, and random seed.
   - Click **Run Optimization**.
3. View the live convergence trajectory, population diversity, and discovered parameters.
4. Click **Apply to Assistant** to activate the discovered configuration in the Chat Q&A assistant.
5. In the **Algorithm Comparison** tab, run a comparative benchmark to generate comparison tables and bar charts.
6. Export the experiment results to **CSV** or **JSON** for paper inclusion.

---

## 📄 License
MIT License
