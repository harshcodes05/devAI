import streamlit as st
import json
import time
import uuid
import subprocess
import shutil
from pathlib import Path

# Initialize Session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "is_indexed" not in st.session_state:
    st.session_state.is_indexed = False

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_ROOT / ".workspace" / st.session_state.session_id
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

REPO_DIR = WORKSPACE_DIR / "repo"
CODE_INDEX_PATH = WORKSPACE_DIR / "code_index.json"
SEMANTIC_INDEX_PATH = WORKSPACE_DIR / "semantic_index.json"
CODEBASE_MAP_PATH = WORKSPACE_DIR / "codebase_map.json"

st.set_page_config(page_title="DevAI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .sub-title {
        color: #A0AEC0;
        font-size: 1.1rem;
        margin-top: -5px;
        margin-bottom: 30px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #2B6CB0;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown('<div class="main-title">DevAI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Dependency-Aware Codebase Reasoning Engine</div>', unsafe_allow_html=True)

def index_repo(repo_path: Path):
    from app.code_indexer import CodeIndexer
    from app.embedding_indexer import EmbeddingIndexer
    from app.repository_analyzer import RepositoryAnalyzer

    with st.spinner("Step 1/3: Parsing AST & Building Code Index..."):
        indexer = CodeIndexer(str(repo_path))
        indexer.save_index(str(CODE_INDEX_PATH))
        
    with st.spinner("Step 2/3: Generating Vector Embeddings (Gemini API)..."):
        embedding_indexer = EmbeddingIndexer(str(CODE_INDEX_PATH), str(SEMANTIC_INDEX_PATH))
        embedding_indexer.save()
        
    with st.spinner("Step 3/3: Mapping Dependency Graph..."):
        analyzer = RepositoryAnalyzer(str(repo_path))
        analyzer.save_map(str(CODEBASE_MAP_PATH))
        
    st.session_state.is_indexed = True

if not st.session_state.is_indexed:
    st.markdown("### Step 1: Connect a Repository")
    st.write("Provide a GitHub repository to build a code-aware RAG index. You can then ask questions about it.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/user/repo")
    
    with col2:
        st.write("") # spacer
        st.write("")
        submit = st.button("Index Repository", use_container_width=True)
        
    if submit:
        if not repo_url.startswith("http"):
            st.error("Please enter a valid HTTP/HTTPS GitHub URL.")
        else:
            if REPO_DIR.exists():
                shutil.rmtree(REPO_DIR, ignore_errors=True)
            
            with st.spinner(f"Cloning {repo_url}..."):
                try:
                    subprocess.run(["git", "clone", repo_url, str(REPO_DIR)], check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    st.error(f"Failed to clone repository: {e.stderr.decode('utf-8', errors='ignore')}")
                    st.stop()
                    
            index_repo(REPO_DIR)
            st.rerun()

else:
    # --- Chat Interface ---
    
    # Sidebar Status
    with st.sidebar:
        st.markdown("### ⚙️ System Status")
        
        with open(CODEBASE_MAP_PATH, "r", encoding="utf-8") as f:
            repo_map = json.load(f)
            num_files = repo_map.get("python_files", 0)
        with open(CODE_INDEX_PATH, "r", encoding="utf-8") as f:
            num_units = len(json.load(f))
            
        col1, col2 = st.columns(2)
        col1.metric("Indexed Files", num_files)
        col2.metric("Code Units", num_units)
        st.success("🟢 V2 Engine Online")
        
        st.markdown("---")
        if st.button("🔄 Index Another Repo"):
            st.session_state.is_indexed = False
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [{"role": "assistant", "content": "Repository indexed! Ask me anything about the codebase. I'll retrieve relevant code, trace dependencies, and explain the reasoning."}]

    for message in st.session_state.messages:
        avatar = "⚡" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    if prompt := st.chat_input("E.g., 'How does the prediction pipeline handle validation?'"):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="⚡"):
            with st.spinner("Traversing dependency graph & generating response..."):
                try:
                    from app.semantic_retriever import SemanticRetriever
                    from app.context_builder import ContextBuilder
                    from app.llm_service import LLMService
                    
                    retriever = SemanticRetriever(str(SEMANTIC_INDEX_PATH))
                    results = retriever.search(prompt, top_k=5)
                    
                    if not results:
                        response = "I couldn't find any relevant code for that question."
                        st.markdown(response)
                    else:
                        builder = ContextBuilder(
                            codebase_map_path=str(CODEBASE_MAP_PATH),
                            code_index_path=str(CODE_INDEX_PATH)
                        )
                        context = builder.build(prompt, results)
                        
                        llm = LLMService()
                        response = llm.answer(prompt, context)
                        
                        st.markdown(response)
                        
                        with st.expander("🔍 View 1-Hop Execution Trace"):
                            st.markdown("This is the exact dependency-aware context injected into the LLM:")
                            st.code(context, language="python")
                            
                except Exception as e:
                    response = f"An error occurred: {str(e)}"
                    st.error(response)
                    
        st.session_state.messages.append({"role": "assistant", "content": response})
