# Imports
import pandas as pd
import numpy as np
import requests
import random
from surprise import SVD, Dataset, Reader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import os
import json
from groq import Groq
import csv
from datetime import datetime
from supabase import create_client

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Get the folder where helpers.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build absolute paths
df_movies = pd.read_csv(
    os.path.join(BASE_DIR, 'data', 'movies.csv')
)
df_ratings = pd.read_csv(
    os.path.join(BASE_DIR, 'data', 'ratings.csv')
)


# Setup — surprise
reader = Reader(rating_scale=(0.5, 5.0))
data_1 = Dataset.load_from_df(
    df_ratings[['userId', 'movieId', 'rating']], 
    reader
)
trainset = data_1.build_full_trainset()
svd_model = SVD()
svd_model.fit(trainset)

# set up - avg ratings
avg_ratings = df_ratings.groupby('movieId')['rating'].mean()

# Setup — TF-IDF (basic genre+title for now)
df_movies['features'] = df_movies['title'] + " " + df_movies['genres'].str.replace("|", " ")
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(df_movies['features'])
cosine_sim = cosine_similarity(tfidf_matrix)

# Functions
#1
def movies_by_genres(genre):
    return df_movies[df_movies["genres"].str.contains(genre, case=False)]["title"]

#2
def get_poster(title):
    try:

        clean_title = title.split("(")[0].strip()
        year = title.split("(")[1].replace(")","").strip()

        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": clean_title,
            "year": year
        }
        
        response = requests.get(url, params=params)
        data = response.json()

        if not data["results"]:                       # handling edge cases  if the result is empty 
            return None
        else :
            poster_path = data['results'][0]['poster_path']

            full_url =  "https://image.tmdb.org/t/p/w500" + poster_path
            
            return full_url
    except :
        return None




#3
def get_movie_description(title):
    try:
        clean_title = title.split("(")[0].strip()
        year = title.split("(")[1].replace(")","").strip()
        
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query":  clean_title,
            "year":  year
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if not data["results"]:
            return ""
            
        return data["results"][0].get('overview', "")
        
    except:
        return ""



#4
def get_cb_recommendations(genre, n=5, random=True):
    
    genre_movies = movies_by_genres(genre)
    
    if len(genre_movies) == 0:
        return []
    
    if random:
        sample = genre_movies.sample(
            min(10, len(genre_movies))
        ).tolist()
    else:
        sample = genre_movies.head(10).tolist()
    
    features = []
    titles = []
    movie_ids = []
    
    # Genre reference
    genre_reference = " ".join([genre] * 5)
    features.append(genre_reference)
    titles.append("REFERENCE")
    movie_ids.append(None)
    
    # Movie features
    for title in sample:
        desc = get_movie_description(title)
        genre_text = df_movies[df_movies['title'] == title]['genres'].values[0].replace("|", " ")
        
        mid = df_movies[df_movies['title'] == title]['movieId'].values[0]
        
        combined = f"{genre_text} {desc}"
        features.append(combined)
        titles.append(title)
        movie_ids.append(mid)
    
    # TF-IDF
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(features)
    
    # Cosine Similarity
    sim_matrix = cosine_similarity(tfidf_matrix)
    
    # Similarity scores vs reference
    sim_scores = list(enumerate(sim_matrix[0]))
    sim_scores = sim_scores[1:]  # Skip reference
    
    # Multiply similarity × avg rating 🎯
    weighted_scores = []
    for idx, sim in sim_scores:
        mid = movie_ids[idx]
        avg_rating = avg_ratings.get(mid, 3.0)
        weighted = sim * avg_rating
        weighted_scores.append((idx, weighted))
    
    # Sort by weighted score
    weighted_scores = sorted(
        weighted_scores,
        key=lambda x: x[1],
        reverse=True
    )
    
    # Return top n
    recommended = [
        titles[i[0]] 
        for i in weighted_scores[:n]
    ]
    return recommended

#5
def get_cf_recommendations(user_id, n=5, genre=None):
    # Step 1 — watched movies
    watched = df_ratings[df_ratings['userId'] == user_id]['movieId'].tolist()
    
    # Step 2 — candidate pool
    all_movies = df_movies['movieId'].tolist()
    
    #  narrow the pool to the requested genre
    if genre:
        genre_ids = set(
            df_movies[df_movies["genres"].str.contains(genre, case=False)]["movieId"]
        )
        all_movies = [m for m in all_movies if m in genre_ids]
    
    unwatched = [m for m in all_movies if m not in watched]
    
    # Step 3 — predict ratings
    predictions = []
    for movie_id in unwatched:
        pred = svd_model.predict(user_id, movie_id)
        predictions.append((movie_id, pred.est))
    
    # Step 4 — sort by predicted rating
    predictions.sort(key=lambda x: x[1], reverse=True)
    
    # Step 5 — get top n titles
    titles = []
    for movie_id, score in predictions[:n]:
        title = df_movies[df_movies['movieId'] == movie_id]['title'].values
        if len(title) > 0:
            titles.append(title[0])
    
    return titles



#6
def get_hybrid_recommendations(user_id,genre, n=5,alpha=0.5,beta=0.5):
    """
    Generate hybrid recommendations combining
    Content Based and Collaborative Filtering.
    
    Args:
        user_id: User ID for CF (None for Guest Mode)
        genre: Genre preference
        n: Number of recommendations
        alpha: Weight for CB score
        beta: Weight for CF score
    
    Returns:
        List of recommended movie titles
    """

    cb_recs = get_cb_recommendations(genre, n=10)
    cf_recs = get_cf_recommendations(user_id, n=10, genre=genre) 
    
    # Assign scores based on position
    # First item = highest score
    
    cb_scores = {}
    for i, movie in enumerate(cb_recs):
        cb_scores[movie] = len(cb_recs) - i
        # Position 0 → highest score
    
    cf_scores = {}
    for i, movie in enumerate(cf_recs):
        cf_scores[movie] = len(cf_recs) - i
        

    # Get all unique movies from both
    all_movies = set(cb_recs + cf_recs)
    
    # Calculate combined score for each
    final_scores = {}
    for movie in all_movies:
        cb_s = cb_scores.get(movie, 0)
        cf_s = cf_scores.get(movie, 0)
        
        final_scores[movie] = (alpha * cb_s) + (beta * cf_s)
    
    # Sort by score — highest first
    sorted_movies = sorted(
        final_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Return top n titles
    return [movie for movie, score in sorted_movies[:n]]


#7
def get_recommendations(genre, n=5,user_id=None):
     
    """
    Main entry point — routes to Guest Mode (CB only)
    or Personal Mode (Hybrid) based on user_id.
    """
    
    if user_id is None:
        # Guest Mode — CB only
        return get_cb_recommendations(genre, n=n)
    else:
        # Personal Mode — Hybrid
        return get_hybrid_recommendations(user_id, genre, n=n)
    
    
client = Groq(api_key=os.getenv("Groq_API_KEY"))

    
#8
def get_user_intent(user_text):
    prompt = f"""
    User said: "{user_text}"
    
    Extract the following and return ONLY valid JSON:
    
    {{
    "mood": one of [Sad, Tired, Neutral, Happy, Excited, Angry, null],
    "genre_preference": genre name or null,
    "reference_title": movie/show name or null,
    "similarity_intent": "similar" or "different" or null,
    "avoid_genres": list of genres to avoid or empty list,
    "vibe": one of [feel-good, suspense, dark, light, emotional, joyful, heartfelt, revenge, inspirational, null]
    }}
    
    Available genres: Action, Adventure, Animation, Children, 
    Comedy, Crime, Documentary, Drama, Fantasy, Film-Noir, 
    Horror, Musical, Mystery, Romance, Sci-Fi, Thriller, War, Western
    
    Note: "rom-com" means Romance + Comedy.
    Only include what's explicitly or implicitly mentioned.
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = response.choices[0].message.content
    
    try:
        return json.loads(raw)
    except Exception as e:
        print(f"Parse error: {e}")  # shows WHY it failed
        return {
            "mood": None, "genre_preference": None,
            "reference_title": None, "similarity_intent": None,
            "avoid_genres": [],
            "vibe" : None
        }

# For LLM logic (no emojis)
mood_to_genres = {
    "Angry"   : ["Comedy", "Animation", "Musical"],
    "Sad"     : ["Comedy", "Animation", "Musical"],
    "Tired"   : ["Animation", "Comedy", "Children"],
    "Neutral" : ["Action", "Adventure", "Documentary"],
    "Happy"   : ["Comedy", "Romance", "Musical"],
    "Excited" : ["Thriller", "Crime", "Action", "Mystery"]
}

vibe_to_genres = {
    "joyful"        : ["Comedy", "Children", "Musical", "Animation"],
    "suspense"      : ["Thriller", "Mystery", "Crime", "Horror", "Sci-Fi"],
    "revenge"       : ["Action", "Crime", "Thriller", "Drama", "Western"],
    "heartfelt"     : ["Drama", "Romance", "Children", "Adventure"],
    "inspirational" : ["Drama", "Documentary", "Adventure", "War"],
    "feel-good"     : ["Comedy", "Romance", "Children", "Musical", "Adventure"],
    "dark"          : ["Drama", "Thriller", "Crime", "Film-Noir", "Horror", "War", "Sci-Fi"],
    "light"         : ["Comedy", "Children", "Animation", "Musical", "Adventure"],
    "emotional"     : ["Drama", "Romance", "Documentary", "Children"]
}

#9
def resolve_genre(intent, avoided_genres=None):
    if avoided_genres is None:
        avoided_genres = set()

    # 1. Explicit genre — ALWAYS respected, avoid-list ignored 🎯
    if intent.get('genre_preference'):
        return intent['genre_preference']

    # 2. Vibe — pick first NOT avoided
    if intent.get('vibe') and intent['vibe'] in vibe_to_genres:
        for g in vibe_to_genres[intent['vibe']]:
            if g not in avoided_genres:
                return g                      # first survivor wins

    # 3. Mood — same pattern
    if intent.get('mood') and intent['mood'] in mood_to_genres:
        for g in mood_to_genres[intent['mood']]:
            if g not in avoided_genres:
                return g

    # 4. Default
    return "Drama"


#10
def filter_avoid_genres(titles, avoid_genres):
    """
    Remove movies whose genres match 
    any in avoid_genres list.
    """
    if not avoid_genres:
        return titles  # nothing to avoid
    
    filtered = []
    for title in titles:
        # Get this movie's genres
        movie_row = df_movies[df_movies['title'] == title]
        if len(movie_row) == 0:
            continue
        
        movie_genres = movie_row['genres'].values[0]
        
        # Check if ANY avoid genre is in this movie
        should_avoid = False
        for avoid in avoid_genres:
            if avoid in movie_genres:
                should_avoid = True
                break
        
        # Keep only if not avoided
        if not should_avoid:
            filtered.append(title)
    
    return filtered

#11
def get_smart_recommendations(user_text, user_id=None, n=5):
    '''
    Full LLM pipeline: text → intent → genre → recommendations
    '''
    # Step 1 — Extract intent from text
    intent = get_user_intent(user_text)
   

    # Step 2 — Resolve genre
    genre = resolve_genre(intent)
    

    # Get MORE than needed (buffer for filtering)
    buffer_n = n * 4   # e.g. 20 if n=5
    recommendations = get_recommendations(genre=genre, n=buffer_n, user_id=user_id)
    
    # Filter out avoided genres
    avoid = intent.get('avoid_genres', [])
    recommendations = filter_avoid_genres(recommendations, avoid)
    
    # Return top n from filtered
    return recommendations[:n], genre

AVAILABLE_PLATFORMS = [
    "Netflix",
    "Amazon Prime Video",
    "JioHotstar",
    "Sony Liv",
    "Zee5",
    "YouTube"
]

#12
def get_watch_providers(title, region="IN"):
    """
    Get streaming platforms for a movie in a region.
    Returns a list of platform names.
    """
    try:
        # Step A — get the movie's TMDB ID first
        clean_title = title.split("(")[0].strip()
        year = title.split("(")[1].replace(")", "").strip()
        
        search_url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": clean_title,
            "year": year
        }
        response = requests.get(search_url, params=params, timeout=5)
        data = response.json()
        
        if not data["results"]:
            return []
        
        movie_id = data["results"][0]["id"]   # get the ID
        
        # Step B — call the watch providers endpoint
        provider_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
        
        # Step B — call the watch providers endpoint
        prov_params = {"api_key": TMDB_API_KEY}
        
        prov_response = requests.get(provider_url, params=prov_params, timeout=5)
        prov_data = prov_response.json()
        
        # Step C — dig into results → region → flatrate
        results = prov_data.get("results", {})
        region_data = results.get(region, {})
        flatrate = region_data.get("flatrate", [])
        
        # Step D — extract just the platform names
        platforms = [p["provider_name"] for p in flatrate]
        
        return platforms
        
    except:
        return []
    
#13
def filter_by_platform(titles, user_platforms, region="IN"):
    """
    Keep only movies available on the user's platforms.
    Uses 'contains' matching to catch variations.
    """
    filtered = []
    
    for title in titles:
        movie_platforms = get_watch_providers(title, region)
        
        # Check if ANY user platform matches (contains)
        for user_plat in user_platforms:
            for movie_plat in movie_platforms:
                if user_plat in movie_plat:   #  'contains' check!
                    filtered.append(title)
                    break
            else:
                continue   # no match, keep checking
            break   # match found, stop
    
    return filtered


#14
def get_recommendations_with_platform(genre, user_platforms=None, n=5, user_id=None, region="IN"):
    """
    Get recommendations, optionally filter by platform.
    If user_platforms is empty → skip filtering.
    """
    # If no platforms chosen → skip filter
    if not user_platforms:
        return get_recommendations(genre=genre, n=n, user_id=user_id)
    
    # Otherwise → buffer, filter, return top n
    buffer_n = n * 4
    titles = get_recommendations(genre=genre, n=buffer_n, user_id=user_id)
    filtered = filter_by_platform(titles, user_platforms, region)
    return filtered[:n]


#15

def get_genre_map():
    """
    Build a dictionary that translates genre NAMES → TMDB genre IDs.
    e.g. {"Animation": 16, "Action": 28, ...}
    """
    url = "https://api.themoviedb.org/3/genre/movie/list"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    response = requests.get(url, params=params, timeout=5).json()

    genre_map = {}
    for g in response["genres"]:
        genre_map[g["name"]] = g["id"]     # "Animation" → 16

    return genre_map

GENRE_MAP = get_genre_map()
LLM_TO_TMDB_GENRE = {
    "Sci-Fi":   "Science Fiction",
    "Children": "Family",
    "Musical":  "Music",
}

PLATFORM_IDS = {
    "Netflix": 8,
    "Amazon Prime Video": 119,
    "JioHotstar": 2336,
    "Zee5": 232,
    "Sony Liv": 237,
    "YouTube": 192,
}

#16
def get_genre_id(llm_genre):
    tmdb_name = LLM_TO_TMDB_GENRE.get(llm_genre, llm_genre)   # translate, or keep as-is
    drama_id  = GENRE_MAP["Drama"]
    genre_id  = GENRE_MAP.get(tmdb_name, drama_id)            # find ID, or fall back to Drama
    return genre_id

#17
def discover_movies_by_genre(genre_id, n=20, provider_ids=None):
    try:
        url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "watch_region": "IN",
            "vote_count.gte": 100,
            "page": random.randint(1, 3),
        }
        # if platforms given, ask TMDB for movies ON those platforms
        if provider_ids:
            params["with_watch_providers"] = "|".join(str(pid) for pid in provider_ids)
            params["watch_region"] = "IN"

        response = requests.get(url, params=params, timeout=5).json()
        return response.get("results", [])[:n]
    except:
        return []          # network died → return empty, don't crash

#18
def get_providers_by_id(movie_id, region="IN"):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
        params = {"api_key": TMDB_API_KEY}
        response = requests.get(url, params=params, timeout=10).json()
        results = response.get("results", {})
        region_data = results.get(region, {})
        flatrate = region_data.get("flatrate", [])
        return [p["provider_name"] for p in flatrate]
    except:
        return []

#19
def guest_recommendations_with_platform(genre_name, user_platforms=None, n=5, region="IN"):
    genre_id = get_genre_id(genre_name)

    # NEW — convert platform names → provider IDs
    provider_ids = None
    if user_platforms:
        provider_ids = [PLATFORM_IDS[p] for p in user_platforms if p in PLATFORM_IDS]

    # Pass provider_ids into discover
    buffer = discover_movies_by_genre(genre_id, n=n * 4, provider_ids=provider_ids)

    survivors = []
    for movie in buffer:
        platforms = get_providers_by_id(movie["id"], region)
        if not platforms:
            continue
        if not user_platforms:
            movie["platforms"] = platforms
            survivors.append(movie)
        else:
            for user_plat in user_platforms:
                for movie_plat in platforms:
                    if user_plat.lower() in movie_plat.lower():
                        movie["platforms"] = platforms
                        survivors.append(movie)
                        break
                else:
                    continue
                break
        if len(survivors) >= n:
            break
    return survivors

#20
def clean_platform_names(plats):
    """Collapse '... with Ads' variants and remove duplicates."""
    cleaned = set()                      # set = automatic dedup 🎯
    for p in plats:
        name = p.replace(" with Ads", "")   # strip the "with Ads" tag
        cleaned.add(name)
    return sorted(cleaned)

#21
def generate_explanation(movie, user_context=""):
    """
    Generate a 'Why You'll Like It' reason.
    Accepts EITHER a movie dict (Guest) OR a title string (Personal).
    """
    # Normalize input — figure out title + overview regardless of shape
    if isinstance(movie, dict):
        title = movie.get("title", "")
        overview = movie.get("overview", "")
    else:
        # It's a title string (Personal Mode)
        title = movie
        overview = get_movie_description(title)   # fetch it 🎯

    prompt = f"""
    {user_context}

    Movie: {title}
    Description: {overview}

    Write ONE sentence (max 25 words) explaining why this movie suits how
    they are feeling right now. Connect a specific element of the movie —
    its tone, story, or characters — to their emotional state.
    Begin by acknowledging their state, then give the reason.
    Do NOT summarise the plot. Do NOT include the movie title.
    Return ONLY the sentence.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()



#22
def log_feedback(user_id, movie_title, action, reason="", genre=""):
    """Insert one feedback event into Supabase."""
    try:
        supabase.table("feedback").insert({
            "user_id": str(user_id),
            "movie_title": movie_title,
            "action": action,
            "reason": reason,
            "genre": genre,
            "timestamp": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print(f"Feedback log failed: {e}")     # don't crash the app


#23
def get_user_feedback(user_id):
    """Read a user's rejections from Supabase."""
    try:
        res = supabase.table("feedback").select("*") \
            .eq("user_id", str(user_id)) \
            .eq("action", "reject").execute()
        rows = res.data
    except Exception as e:
        print(f"Feedback read failed: {e}")
        return set(), set()

    rejected_titles = {r["movie_title"] for r in rows}
    avoided_genres = {r["genre"] for r in rows
                      if r["reason"] == "genre_mismatch" and r["genre"]}
    return rejected_titles, avoided_genres

#24
def filter_rejected(movies, rejected_titles):
    """
    Remove movies the user has rejected.
    Works with BOTH dicts (Guest) and title strings (Personal).
    """
    if not rejected_titles:
        return movies

    kept = []
    for m in movies:
        title = m["title"] if isinstance(m, dict) else m     # handle both shapes 
        if title not in rejected_titles:
            kept.append(m)
    return kept

#25
def compute_metrics():
    """Compute evaluation metrics from Supabase feedback."""
    try:
        res = supabase.table("feedback").select("*").execute()
        rows = res.data
    except Exception as e:
        print(f"Metrics read failed: {e}")
        return None

    if not rows:
        return None

    df = pd.DataFrame(rows)

    shown   = df[df["action"] == "shown"]
    accepts = df[df["action"] == "accept"]
    rates   = df[df["action"] == "rate"]

    total_shown = pd.to_numeric(shown["reason"], errors="coerce").sum()
    acceptance_rate = (len(accepts) / total_shown * 100) if total_shown else 0

    decision_times = pd.to_numeric(accepts["reason"], errors="coerce").dropna()
    avg_decision = decision_times.mean() if len(decision_times) else 0

    satisfaction = pd.to_numeric(rates["reason"], errors="coerce").dropna()
    avg_satisfaction = satisfaction.mean() if len(satisfaction) else 0

    ces = (avg_satisfaction / avg_decision) if avg_decision else 0

    return {
        "acceptance_rate": round(acceptance_rate, 1),
        "avg_decision_time": round(avg_decision, 1),
        "avg_satisfaction": round(avg_satisfaction, 2),
        "ces": round(ces, 3),
        "total_shown": int(total_shown),
        "total_accepts": len(accepts),
    }