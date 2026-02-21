# Technical Specification: NVIDIA PersonaPlex-7B-v1 & RAG Architecture

## 1. Technology Overview
**PersonaPlex-7B-v1** is a state-of-the-art **Full-Duplex Speech-to-Speech (S2S)** language model released by NVIDIA. Unlike traditional cascaded systems (ASR -> LLM -> TTS), PersonaPlex processes audio tokens natively, allowing for real-time, interruptible conversations.

### Key Characteristics
* **Architecture:** Dual-Transformer based on **Moshi** (Kyutai) architecture.
* **Audio Codec:** Uses **Mimi** neural audio codec for high-fidelity tokenization.
* **Latency:** Ultra-low latency (~160ms - 200ms end-to-end).
* **Interaction Mode:** Full-Duplex (supports "barge-in" / user interruptions).
* **Input Modality:** Multi-modal (Audio Stream + Text Prompts for context conditioning).

---

## 2. Architectural Pattern: Side-Channel RAG
Implementing Retrieval-Augmented Generation (RAG) in an S2S model requires a **Side-Channel Architecture**. Since the model consumes audio streams continuously, we cannot pause the flow to perform blocking vector searches.

### Data Flow Strategy
1.  **Primary Channel (Audio):** User audio flows directly to PersonaPlex VRAM buffer to maintain "presence" and allow immediate back-channeling (e.g., "uh-huh").
2.  **Secondary Channel (Context):** A parallel process performs ASR (Automatic Speech Recognition) on the input stream, queries the Vector Database, and asynchronously injects the retrieved text into the PersonaPlex **System/Context Prompt**.

### Workflow Diagram (Mermaid)
```mermaid
graph TD
    UserAudio[User Audio Stream] -->|Splitter| AudioBuffer[PersonaPlex Audio Buffer]
    UserAudio -->|Splitter| ASR[Real-time ASR (Whisper/Nova-2)]
    ASR -->|Text Stream| VectorDB[(Vector Store / LangChain)]
    VectorDB -->|Retrieved Context| ContextManager[Context Injection]
    ContextManager -->|Update System Prompt| PersonaPlex[PersonaPlex-7B Model]
    AudioBuffer --> PersonaPlex
    PersonaPlex -->|Generated Audio| UserSpeaker