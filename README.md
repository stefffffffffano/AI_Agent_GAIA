# 🧠 AI Agent for GAIA Dataset

**LLM-powered AI Agent using LangGraph to tackle the GAIA benchmark**  
Built with 🧱 LangGraph • 🤖 GPT-4o • 🔎 RAG + Web Search • 🧠 Long-term Memory

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-✓-blueviolet)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-lightgrey)  
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🚀 Overview

This repository implements an **AI Agent** designed to solve questions from the **GAIA dataset** (by Hugging Face), with a focus on the **Level 1 Validation** set.

The agent is powered by **OpenAI's GPT-4o model** and orchestrated using **LangGraph**. It is equipped with two main tools:

### 🧠 Tools

1. **RAG Tool (Retrieval-Augmented Generation)**  
   - The agent generates a query based on the user's input.
   - A secondary agent refines the query to optimize it for web search.
   - The top 10 results are retrieved using **DuckDuckGo**.
   - Each page is chunked using a **sliding window** (512 tokens sampled every 256 tokens).
   - Chunks and the refined query are embedded using **OpenAI Embeddings**.
   - Chunks are ranked by **cosine similarity**, and the top 5 are returned.

2. **Memory Tool**  
   Implementation inspired by [MEMGPT](https://arxiv.org/abs/2310.08560), with a context window divided into three sections: system instructions, working context and queue of messages. Each section is properly sized in order not to overcome context window size. Sizes are constants retrieved from the configuration file, where also the API key has to be provided. An example of the structure is provided [here](src/env.example).
   - Stores relevant memories to handle long-term information beyond the LLM's context window.
   - Uses an internal vector store with semantic similarity for retrieval.
  

---

## 📊 Results

- **Dataset**: GAIA - Level 1 Validation Set  
- **Questions Solved**: 10 / 53  
- **Accuracy**: **18%**

---

## 🛠️ Installation & Usage

### 1. Clone the repository

```bash
git clone https://github.com/stefffffffffano/AI_Agent_GAIA.git
cd ai-agent-gaia
```
### 2. Download GAIA dataset  
Follow the instructions [here](https://huggingface.co/gaia-benchmark) to download GAIA dataset from Hugging Face and add it to the src folder.  

### 2. Install dependencies  
Make sure you have Python 3.10+ installed
```bash
pip install -r requirements.txt
```  
### 3. Set up environment variables  
```bash
cd src
cp .env.example .env
```    
Then open the .env file and insert your OpenAI API key and any other required variables.
### 4. Run the agent on GAIA level 1 validation
```bash
python run_agent.py
```  

---

## 📁 Project Structure  

```
AI_AGENT_GAIA/
│
├── requirements.txt            
├── README.md                   
│  
├── src/  
│   ├── run_agent.py             # Main script  
│   ├── .env.example             # Configuration API keys  
│   ├── agent/                   # LangGraph agent logic  
│   └── draw.ipynb               # Draw the graph  
```


---

## 📬 Contact

For issues, suggestions or contributions, feel free to:

- Open an [Issue](https://github.com/stefffffffffano/AI_Agent_GAIA/issues)
- Submit a Pull Request
- Or reach out directly!

Made with ❤️ for intelligent agent research and experimentation.




