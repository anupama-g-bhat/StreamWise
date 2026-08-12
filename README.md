# StreamWise 🎬
> Beat the Scroll. Let the Story Roll.

## 🔗 Live Demo
[StreamWise on Streamlit Cloud](https://streamwise-ybqu5mtn7lcic5jmudkusj.streamlit.app/)

## Problem
Existing recommendation systems primarily rely on historical viewing behavior and ratings to generate personalized suggestions. However, these recommendations may not adequately capture a user's current preferences and viewing context at the time of content selection. As a result, users may spend considerable time evaluating available
options before making a viewing decision. This limitation can contribute to decision fatigue and choice paralysis, particularly when users are presented with a large number of content options.
Therefore, there is a need for a mood-aware and explainable recommendation system that considers a user's current interests and provides transparent recommendations to improve content discovery and support more efficient decision-making.

## Solution
StreamWise is proposed in this context as a mood-aware and explainable OTT recommendation system that combines hybrid recommendation techniques, natural language understanding, and recommendation explainability to enhance content discovery and decision making. 

### OTT Platform Filtering
Guest Mode fetches fresh, currently popular movies from the TMDB discover API and filters them by live streaming availability (India region), so users can limit recommendations to platforms they subscribe to. MovieLens titles (up to ~2016) are largely unavailable on current OTT catalogues due to licensing rotation, so this filter is offered in Guest Mode, which uses content-based filtering and does not depend on the older rated dataset.

### Language Filtering
Guest Mode can filter recommendations by original language, extracted from natural-language input or an explicit selector. Personal Mode does not support this — MovieLens contains only two titles referencing Indian cinema, so there is no regional content to filter. The vote-count quality threshold used elsewhere is relaxed for regional languages, whose smaller catalogues would otherwise be filtered to near-zero results, and the result-page range is
determined dynamically to sample the catalogue that actually exists.

### Feedback & Refinement
Users can mark recommendations as "Not Interested" and specify a reason (genre, storyline, mood, already watched, or other). Genre mismatches steer future automatic selections away from that genre; other reasons hide the specific title. Personal Mode feedback persists to a Supabase database keyed by user ID; Guest Mode feedback is session-scoped, preserving anonymity.

### Incognito Mode
A privacy toggle within Personal Mode. Recommendations remain personalized (the user's rating history still drives collaborative filtering), but no feedback is recorded — rejections are session-scoped only. Personalization in, no trace out.

### Evaluation Metrics
The app records acceptance, decision time, and per-session satisfaction ratings as users interact, alongside the count of recommendations shown. These feed four online metrics — Acceptance Rate, Average Decision Time, Average Satisfaction, and the Choice Efficiency Score (satisfaction ÷ decision time) — displayed in an expandable dashboard. No events are recorded during incognito sessions.

## Features

### ✅ Implemented
- Mood-based genre suggestion (slider)
- Hybrid recommendation engine (CB + CF)
- Guest Mode (cold start solution)
- Personal Mode (user selection + persistent feedback)
- TMDB poster integration
- Groq LLM mood understanding 
- OTT platform filtering (Guest Mode)
- Regional language filtering (Guest Mode) — English, Hindi, Kannada, Telugu, Tamil, Malayalam, Korean
- Explainable recommendations (both modes)
- Not Interested feedback
- Incognito Mode
- Evaluation metrics collection & dashboard
- Deployment (Streamlit Community Cloud)
- User evaluation session (real-user metric data)

 
## Tech Stack
Programming Language

    -Python

Frontend

    -Streamlit

Data Processing

    -Pandas
    -NumPy

Machine Learning

    Scikit-learn
    SVD (Surprise)

Recommendation Techniques

    Content-Based Filtering
    Collaborative Filtering (Matrix Factorization using SVD - Surprise)
    Hybrid Recommendation System
    TF-IDF Vectorization
    Cosine Similarity

LLM

    Groq API (OpenAI)

Dataset

    MovieLens Small Dataset

External APIs

    TMDB API

Data base

    Supabase (PostgreSQL) — feedback & metrics storage

Deployment

    Streamlit Community Cloud

## How to Run
## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd StreamWise
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux/Mac**

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure API Keys

Create a `.env` file and add:

```env
TMDB_API_KEY=your_tmdb_api_key
Groq_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_publishable_key
```

### 6. Run the Application

```bash
streamlit run app.py
```


### 7. Access the Application

Open your browser and navigate to:

```text
http://localhost:8501
```

*Note: The deployed version is available at the [Live Demo](#-live-demo) link above — no local setup required.*

## Workflow

1. ✅ User selects mood (slider) and genre preference
2. ✅ Groq LLM interprets free-text mood/intent 
3. ✅ Content-Based Filtering generates recommendations using movie genres, title, and TMDB descriptions
4. ✅ Collaborative Filtering generates recommendations using SVD matrix factorization (Surprise) on user rating    patterns
5. ✅ A hybrid recommendation score is calculated (weighted combination of CB and CF)
6. ✅ Recommendations filtered by selected OTT platforms (Guest Mode, via TMDB live availability) 
7. ✅ "Why You'll Like It" explanations generated (both nodes)
8. ✅ Recommendations displayed with posters via TMDB API
9. ✅ User feedback collected via "Not Interested" mechanism with reasons
10.✅ Recommendations refined based on feedback (hide titles, avoid genres)
11.✅ Interaction metrics recorded (acceptance, decision time, satisfaction)


## Project Structure

```
StreamWise/
├── data/                        # MovieLens dataset files
│   ├── movies.csv
│   ├── ratings.csv
│   ├── links.csv
│   └── tags.csv
├── notebooks/                   # Exploration & development notebooks
│   ├── 01_BasicExploration.ipynb
│   ├── 02_Content_Based_Filtering.ipynb
│   ├── 03_Collaborative_filtering.ipynb
│   ├── 04_Hybrid_recommendation.ipynb
│   ├── 05_Groq_LLM.ipynb
│   ├── 06_Evaluation.ipynb
│   ├── 07_OTT_filter.ipynb
│   └── 08_Feedback_feature.ipynb
├── notes/                       # Observation notes
│   └── Observations.md
├── images/                      # Generated plots
├── report/                      # Synopsis & documentation
├── app.py                       # Main Streamlit application
├── helpers.py                   # Core recommendation functions
├── requirements.txt             # Python dependencies
├── .python-version              # Pinned Python version for deployment
├── .gitignore
└── README.md

```


## Current Status

- ✅ Hybrid recommendation engine complete (Content-Based + Collaborative Filtering)
- ✅ Collaborative Filtering using Surprise SVD
- ✅ Offline evaluation complete (RMSE 0.88, Precision@5 0.59)
- ✅ Guest, Personal, and Incognito Modes functional
- ✅ Streamlit UI with mood-based and free-text input
- ✅ Groq LLM intent understanding
- ✅ OTT platform filtering (Guest Mode, live TMDB availability)
- ✅ Regional language filtering (Guest Mode) — English, Hindi, Kannada, Telugu, Tamil, Malayalam, Korean
- ✅ "Why You'll Like It" explainability
- ✅ "Not Interested" feedback with reason-based refinement
- ✅ Online metrics collection & dashboard (Acceptance Rate, Decision Time, Satisfaction, CES)
- ✅ Deployed to Streamlit Community Cloud
- ✅ User evaluation session with real users (in progress)