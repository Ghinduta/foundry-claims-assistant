# AI-103 practice assessment review (screenshots 1-24)

**What the screenshots show:** a MeasureUp-style practice test on starttest.com (`ITDStart.aspx`, "Question Progress (n/50)") in practice mode with **Show/Hide Solution** turned on. For single-choice items the page marks every option correct or incorrect, outlines the user's radio button in red (wrong) or green (right), and shows an explanation box. Newer-style items also show **Objective / What This Item Tests / Additional Reading / Rationale**. For dropdown and drag-drop items the Answer Area shows the user's selections and the Rationale names the correct ones, but no per-slot right/wrong marks appear. I graded those by comparing the selection with the rationale.

Several screenshots don't show the question-number header. Where the number is missing I give the image number and mark the question number "?". Doc links are listed by their visible titles. The screenshots don't include the URLs.

Exam areas: Plan and manage / Generative AI and agents / Computer vision / Text analysis / Information extraction. Speech items (objective 4.x) are filed under Text analysis.

---

## Q1 (images 1-2)
- **Question:** A Python client uses the **Voice Live API** for a Microsoft Foundry agent. It streams microphone input, plays audio locally and handles conversation events. The session must support multilingual conversations and reduce speaker feedback from local audio playback. Which session settings? (two dropdowns)
- **Options:** Session modalities: (text-only / audio-only / text and audio). Audio handling: various combinations, including "Noise reduction and multilingual VAD" and "multilingual VAD and echo cancellation". The full dropdown lists aren't visible.
- **User chose:** Session modalities = **Text and audio**. Audio handling = **Noise reduction and multilingual VAD**.
- **Correct:** Text and audio + **multilingual VAD and echo cancellation**.
- **Result:** Wrong (1 of 2 slots).
- **Explanation:** You need text+audio for spoken interaction plus conversation events, multilingual VAD for turn detection, and echo cancellation to stop the mic from picking up locally played audio. Links: "Develop a voice live agent", "Voice Live API".
- **Objective:** 4.2 Implement speech solutions. **Area:** Text analysis (speech).
- **Miss type:** (c) scenario judgement. "Speaker feedback from local playback" means echo cancellation, not noise reduction.

## Q2? (image 3; header not visible, probably Q2)
- **Question:** An app will transcribe large quantities of audio files with **Azure Speech in Foundry Tools batch transcription**. Recommend storage that minimizes development effort.
- **Options:** A. Azure Cosmos DB, B. Azure Data Lake Storage, C. Azure SQL Database, D. Azure Storage
- **User chose:** D. **Correct:** D. **Result:** Right.
- **Explanation:** Azure Storage is the only storage provider batch transcription supports by default. Links: "Create a batch transcription - Speech service", "Create speech-enabled apps with the Speech service - Training".
- **Area:** Text analysis (speech).

## Q3 (image 4)
- **Question:** A call-center app sends recordings to Speech speech-to-text. WER is high with many **substitution** errors. What should you add to the training data?
- **Options:** A. custom product and people names, B. overlapping speakers, C. people talking in the background
- **User chose:** A. **Correct:** A. **Result:** Right.
- **Explanation:** Substitution errors call for training on product and people names. Overlapping speakers cause deletion errors, and background speech causes insertion errors. Links: "Test accuracy of a Custom Speech model", "Create speech-enabled apps with the Speech service - Training".
- **Area:** Text analysis (speech).

## Q? (image 5)
- **Question:** An app lets users create notes by speech. Recommend the Azure Speech in Foundry Tools model. It must support noisy environments.
- **Options:** A. base, B. base with customizations, C. custom speech-to-text, D. default
- **User chose:** B. **Correct:** C. **Result:** Wrong.
- **Explanation:** Custom speech-to-text lets you train the model on the ambient noise. The explanation mentions a factory floor that isn't in the visible stem. Links: "Speech-to-text FAQ", "Create speech-enabled apps with the Speech service - Training".
- **Area:** Text analysis (speech).
- **Miss type:** (c) scenario judgement. The plausible-sounding "base with customizations" was chosen over the actual product, custom speech-to-text.

## Q? (image 6)
- **Question:** App1 analyzes social media sentiment and returns negative sentiment for feedback that contains positive feedback. You need more granular information. What should you add to the API requests?
- **Options:** A. `loggingOptOut=true`, B. `StringIndexType=TextElements_v8`, C. `opinionMining=true`
- **User chose:** C. **Correct:** C. **Result:** Right.
- **Explanation:** `opinionMining=true` adds aspect-based sentiment, so one sentence can return both positive and negative sentiment. The other options control logging and offset/length units. Links: "Text Analysis Runtime - Analyze Text - REST API", "How to perform sentiment analysis and opinion mining", "Extract insights from text with the Language service - Training".
- **Area:** Text analysis.

## Q? (images 7-8)
- **Question:** Azure Speech transcribes live support calls and stored recordings. Recordings contain proprietary product codes and en-US speakers with regional accents, and the default model substitutes common words for the codes. You have org audio samples and reference transcripts. You need better accuracy for live and stored audio. Which **Speech Studio project type**?
- **Options:** A. Batch speech to text, B. Custom speech, C. Real-time speech to text, D. Custom voice
- **User chose:** D. **Correct:** B. **Result:** Wrong.
- **Explanation:** Custom speech uses org audio and transcripts to improve recognition of domain vocabulary and accents. Batch and real-time are transcription modes, not customization projects, and **custom voice is for text-to-speech**. Links: "What is custom speech?", "What is Speech Studio?".
- **Objective:** 4.2 Implement speech solutions. **Area:** Text analysis (speech).
- **Miss type:** (a) service/feature name. The user mixed up Custom voice (TTS) with Custom speech (STT).

## Q8 (images 9-10)
- **Question:** A Foundry project has a deployed RAG agent (product manuals for grounding, an order-status tool, multi-turn). You want automated Responsible AI evaluation in a CI/CD release stage with a JSONL test set that includes expected tool calls, grounding sources and harmful prompts. It must run without a manual portal workflow and put the results in the Foundry project. Which workflow?
- **Options:** A. Call the Azure AI Content Safety API for each prompt/response; B. **Microsoft Foundry SDK cloud evaluation run** against the agent with the JSONL set and built-in agent, grounding and safety evaluators; C. Foundry portal evaluation run with textual similarity and fluency evaluators; D. Application Insights monitoring (dashboards, latency/token metrics, alerts)
- **User chose:** B. **Correct:** B. **Result:** Right.
- **Explanation:** An SDK cloud evaluation run automates from CI/CD with JSONL and built-in agent, grounding and safety evaluators, and stores the results in the project. The portal run is manual, App Insights covers operational telemetry, and Content Safety alone doesn't evaluate tool calls or grounding. Links: "Observability in generative AI", "Evaluate generative AI applications", "Responsible AI in Azure workloads".
- **Objective:** 1.4 Implement responsible AI across GenAI and agentic systems. **Area:** Plan and manage.

## Q9 (images 11-12), user's answer not visible
- **Question:** Field-service app. Manuals in Azure Blob Storage as PDF, Word and PowerPoint, with text, screenshots, diagrams and photos. An agent and an Azure AI Search index ground responses. Recommend an **agent input capability** (must handle uploaded photo/screenshot + text) and an **indexing pipeline** (keep page and bounding-region metadata for images across file types, and allow retrieval from text or image input).
- **Options (from the rationale):** Agent: vision-enabled chat model deployment / embedding model deployment / speech synthesis model deployment / text-only chat model deployment. Pipeline: Document Layout skill + multimodal embeddings / Document Extraction skill + text embeddings / image verbalization / Text Split skill + image embeddings.
- **Correct:** **Vision-enabled chat model deployment** + **Document Layout skill and multimodal embeddings**.
- **User chose:** not visible. The Answer Area isn't in either screenshot, so I can't grade it.
- **Explanation:** Vision-enabled chat handles image+text prompts. Document Layout + multimodal embeddings keep page and bounding-region metadata and support text or image queries. Image verbalization converts images to text and doesn't support image-based retrieval. Links: "Vision-enabled models", "What is Microsoft Foundry?", "Quickstart: Multimodal search in the Azure portal".
- **Area:** Generative AI and agents (multimodal RAG). It could also count as Information extraction. The objective line isn't visible.

## Q? (image 13)
- **Question:** An app uses a Microsoft Foundry Service resource. Which **Azure CLI** command returns the resource endpoint?
- **Options:** A. `az cognitiveservices account show`; B. `az cognitiveservices account show --name myresource`; C. `az cognitiveservices account show --name myresource --resource-group cognitive-services-resource-group`; D. `az cognitiveservices account show --resource-group cognitive-services-resource-group`
- **User chose:** B. **Correct:** C. **Result:** Wrong.
- **Explanation:** You need both `--name` and `--resource-group` to show the account, and the output includes the endpoint. Links: "az cognitiveservices account", "Create and consume Cognitive Services - Training".
- **Area:** Plan and manage.
- **Miss type:** (d) other. This is Azure CLI syntax: `show` needs both `--name` and `--resource-group`.

## Q? (images 14-15)
- **Question:** A Foundry project for a customer-support agent. Manuals and escalation procedures are stored as PDFs and web pages in enterprise repositories, and the agent currently drafts answers from a base LLM only. Requirements: generate natural-language answers, ground them in enterprise repository content, and avoid retraining when content changes. Which combination?
- **Options:** A. Azure Machine Learning, managed online endpoints, Azure Blob Storage; B. Azure Functions, Microsoft Foundry Agent Service tools, Azure Blob Storage; C. **Azure OpenAI in Microsoft Foundry Models, Microsoft Foundry Agent Service, and Azure AI Search**; D. Azure OpenAI in Microsoft Foundry Models, Microsoft Foundry Agent Service, and **Grounding with Bing Search**
- **User chose:** D. **Correct:** C. **Result:** Wrong.
- **Explanation:** Azure AI Search gives RAG over enterprise content with no retraining. **Grounding with Bing is for web data**, not enterprise repositories. Links: "Select Azure PaaS solutions for AI", "Manage Grounding with Bing in Microsoft Foundry and Azure".
- **Objective:** 1.1 Choose the appropriate Foundry services for GenAI and agents. **Area:** Plan and manage.
- **Miss type:** (c) scenario judgement (enterprise data needs AI Search; Bing is for public web).

## Q15 (image 16), stem not visible, only the rationale and answer area
- **Question (from the rationale):** Choose deployment types for an **online shopping assistant** (needs low latency variance, EU data zone) and a **product-content enrichment** job (large async job, 24-hour turnaround, lower cost, EU data zone). Drag-drop.
- **Options:** Data Zone Batch, Data Zone Provisioned, Data Zone Standard, Global Batch, Global Provisioned, Global Standard, Standard
- **User chose:** Online shopping assistant = **Data Zone Provisioned**. Product-content enrichment = **Standard**.
- **Correct:** Data Zone Provisioned + **Data Zone Batch**.
- **Result:** Wrong (1 of 2 slots).
- **Explanation:** Provisioned gives low latency variance and Data Zone keeps processing in the EU. Batch suits large async 24-hour jobs at lower cost. Standard doesn't give the EU data-zone boundary or the batch cost benefit. Link: "Deployment types for Microsoft Foundry Models".
- **Area:** Plan and manage.
- **Miss type:** (c) scenario judgement (batch vs standard, data zone vs regional).

## Q16? (images 17-18; header not visible, falls between Q15 and Q17)
- **Question:** A RAG app ingests PDF and HTML, chunks it, stores chunks with metadata and updates Azure AI Search indexes, and a labeled retrieval eval set runs after each release. Build a monitoring dashboard with sections for **Data ingestion quality** and **Relevance performance**. Drag signals.
- **Options:** Chunk overlap token count; Source availability by index; Pipeline update success status; Embedding vector dimension count; Validation failure rate over time; Routing classifier confidence score; Retrieval evaluation score on a labeled query set
- **User chose:** Data ingestion quality = **Chunk overlap token count**. Relevance performance = **Retrieval evaluation score on a labeled query set**.
- **Correct:** **Validation failure rate over time** + Retrieval evaluation score on a labeled query set.
- **Result:** Wrong (1 of 2 slots).
- **Explanation:** Validation failure rate is the direct ingestion-quality signal. Chunk overlap and embedding dimension count are configuration values, not monitoring signals. Source availability is index health, and pipeline update status is release execution. Links visible: "Build an unstructured data pipeline for RAG", "Data ingestion". Earlier links are cut off.
- **Area:** Generative AI and agents (RAG pipeline monitoring). The objective isn't visible, so this could also be Plan and manage.
- **Miss type:** (c) scenario judgement (a config value vs a monitoring signal).

## Q17 (image 19)
- **Question:** An app uses Microsoft Foundry Service. Which **two** methods can authenticate to Azure AI Services?
- **Options:** A. a SAML token, B. a subscription key, C. Microsoft Entra ID, D. Kerberos
- **User chose:** only C was ticked. **Correct:** B and C.
- **Result:** Wrong (subscription key missed).
- **Explanation:** You can use single-service or multi-service subscription keys, or a Microsoft Entra ID service principal with RBAC. SAML and Kerberos aren't supported. Links: "Authentication in Azure Cognitive Services", "Secure Cognitive Services - Training".
- **Area:** Plan and manage.
- **Miss type:** (d) other. The user picked one answer on a pick-two item. The screenshot doesn't show whether this was a knowledge gap or an incomplete submission.

## Q18 (images 20-21; image 20 is the answer/rationale half, image 21 is the stem)
- **Question:** A Foundry project linked to Resource1 (East US). You deploy **gpt-4o** as **Deployment1**, and the app calls it through the **OpenAI v1-compatible API**. Requirements: pay-as-you-go throughput, inference allowed in any Azure region, automatic move to new default model versions, and the request must target the deployment.
- **Options:** Deployment type: Global Standard / Global Batch / Regional Provisioned / Standard (full list not visible). Version policy + request parameter: several combinations (full list not visible).
- **User chose:** **Global Standard**, plus **"Upgrade once the new default version becomes available; model: Deployment1"**.
- **Correct:** same as the user's selection. **Result:** Right.
- **Explanation:** Global Standard is pay-as-you-go and processes in any region. For a v1-compatible request, the `model` parameter takes the **deployment name** (Deployment1), not the model name. Links: "Create and deploy an Azure OpenAI in Microsoft Foundry Models resource (classic)", "Deploy Microsoft Foundry Models in the Foundry portal", "Exercise - Configure governance controls".
- **Area:** Plan and manage.

## Q19 (images 22-23)
- **Question:** A Foundry project hosts a customer support agent. Requirements: (1) **persist user preferences across sessions and devices, isolated by authenticated user**; (2) use governed product docs for grounded answers, and call an external ITSM API only through approved agent integration endpoints.
- **Options (from the rationale):** User context: Foundry Agent Service memory / per-conversation session state / prompt instructions / agent evaluators. Knowledge+action: Foundry IQ knowledge bases and Foundry Agent Service tools / AI Gateway / Foundry Control Plane / Model Router / guardrails / system message design.
- **User chose:** User context = **Per-conversation session state**. Knowledge+action = **Foundry IQ knowledge bases and Foundry Agent Service tools**.
- **Correct:** **Foundry Agent Service memory** + Foundry IQ knowledge bases and Foundry Agent Service tools.
- **Result:** Wrong (1 of 2 slots).
- **Explanation:** Foundry Agent Service memory (preview) gives persistent, user-scoped context across sessions and devices. Session state doesn't persist across sessions or devices. Links: "Create and use memory in Foundry Agent Service (preview)", "Process to build agents across your organization", "Introduction".
- **Area:** Generative AI and agents.
- **Miss type:** (a) feature name. The user didn't know about the Agent Service **memory** feature.

## Q20 (image 24), correct answer not visible
- **Question:** A Foundry Agent Service procurement agent uses an **OpenAPI tool** to look up vendors and create purchase orders. Its managed identity has direct read/write DB access. Requirements: lookups and POs up to $10,000 run without approval, POs above $10,000 need manager approval, and production writes use least-privilege access through the purchasing API.
- **Options:** not visible (only the selected dropdown values show).
- **User chose:** POs above $10,000 = **Require human-in-the-loop execution**. Production system access = **Use task-scoped API access**.
- **Correct:** not shown. The solution or rationale panel isn't open in this screenshot, so I can't grade it.
- **Area:** Generative AI and agents (agent governance). Could also be Plan and manage (responsible AI/governance).

---

## Summary table

| Q # (image) | Area | Result | Miss type | Topic |
|---|---|---|---|---|
| Q1 (1-2) | Text analysis (speech) | Wrong (1/2) | c | Voice Live echo cancellation + VAD |
| Q2? (3) | Text analysis (speech) | Right | - | Batch transcription needs Azure Storage |
| Q3 (4) | Text analysis (speech) | Right | - | Substitution errors: train names |
| ? (5) | Text analysis (speech) | Wrong | c | Noisy env: custom speech-to-text |
| ? (6) | Text analysis | Right | - | opinionMining=true for granular sentiment |
| ? (7-8) | Text analysis (speech) | Wrong | a | Custom speech vs custom voice |
| Q8 (9-10) | Plan and manage | Right | - | SDK cloud evaluation in CI/CD |
| Q9 (11-12) | Gen AI and agents (or Info extraction) | Not visible | - | Vision model + Document Layout multimodal |
| ? (13) | Plan and manage | Wrong | d | az CLI account show needs RG |
| ? (14-15) | Plan and manage | Wrong | c | AI Search vs Bing grounding |
| Q15 (16) | Plan and manage | Wrong (1/2) | c | Data Zone Batch vs Standard |
| Q16? (17-18) | Gen AI and agents (or Plan and manage) | Wrong (1/2) | c | RAG ingestion-quality monitoring signal |
| Q17 (19) | Plan and manage | Wrong | d | Auth: subscription key + Entra ID |
| Q18 (20-21) | Plan and manage | Right | - | Global Standard, model=deployment name |
| Q19 (22-23) | Gen AI and agents | Wrong (1/2) | a | Agent Service memory for user prefs |
| Q20 (24) | Gen AI and agents | Not visible | - | HITL approval + task-scoped API |
