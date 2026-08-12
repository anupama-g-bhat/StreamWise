import streamlit as st
import time
from helpers import (get_poster, get_smart_recommendations, get_user_intent, resolve_genre,
                     guest_recommendations_with_platform,clean_platform_names, get_recommendations,generate_explanation,
                     log_feedback, get_user_feedback, filter_rejected,compute_metrics)
# UI
st.title("StreamWise")
st.subheader("Beat the Scroll, Let the Story Roll!")

if "guest_movies" not in st.session_state:
    st.session_state["guest_movies"] = []
if "personal_movies" not in st.session_state:
    st.session_state["personal_movies"] = []
if "explanations" not in st.session_state:
    st.session_state["explanations"] = {}
if "awaiting_reason" not in st.session_state:
    st.session_state["awaiting_reason"] = None
if "current_genre" not in st.session_state:
    st.session_state["current_genre"] = ""
if "user_context" not in st.session_state:
    st.session_state["user_context"] = ""
if "guest_rejected" not in st.session_state:
    st.session_state["guest_rejected"] = set()
if "rating_logged" not in st.session_state:
    st.session_state["rating_logged"] = False
if "searched" not in st.session_state:
    st.session_state["searched"] = False

# display function
def display_movies(titles, user_id, incognito=False):
    """Fetches posters and shows movies in 3 columns"""
    movies = []
    for title in titles:
        poster = get_poster(title)
        movies.append({"title": title, "poster": poster})
    
    cols = st.columns(3)
    for i, movie in enumerate(movies):
        col = cols[i % 3]
        with col:
            if movie["poster"]:
                st.image(movie["poster"])
            else:
                st.markdown("""<div style='height:300px;display:flex; 
                            align-items:center;justify-content:center;
                            background:#f0f0f0;border-radius:10px'>
                            🎬 Poster not available</div>""",
                            unsafe_allow_html=True)
            st.write(movie["title"])

            
            title = movie["title"]
            b1, b2, b3 = st.columns(3)      # three mini-columns for the buttons
            with b1:
                if st.button("🤔", key=f"why_{i}_{title}", help="Why You'll Like It?"):
                    if title not in st.session_state["explanations"]:
                        with st.spinner("💭 Thinking..."):
                            st.session_state["explanations"][title] = generate_explanation(title, user_context=st.session_state.get("user_context", ""))
            if title in st.session_state["explanations"]:
                st.info(st.session_state["explanations"][title])

            with b2:
                if st.button("👍", key=f"yes_{i}_{title}", help="Interested"):
                    t_shown = st.session_state.get("t_shown", time.time())
                    decision_time = round(time.time() - t_shown, 2)
                    if not incognito:
                        log_feedback(user_id, title, "accept",
                                     reason=str(decision_time),
                                     genre=st.session_state["current_genre"])
                        st.toast("Noted 👍")
            
            with b3:
                if st.button("👎", key=f"no_{i}_{title}", help="Not interested"):
                    st.session_state["awaiting_reason"] = title
                    st.rerun()

            if st.session_state["awaiting_reason"] == title:
                reason = st.radio(
                    "Why not?",
                    ["genre_mismatch", "storyline", "mood_mismatch", "already_watched", "other"],
                     key=f"reason_{i}_{title}"
                )
                if st.button("Submit", key=f"submit_{i}_{title}"):
                    if incognito:
                        st.session_state["guest_rejected"].add(title)     # session only, no file
                    else:
                        log_feedback(user_id, title, "reject", reason=reason,
                         genre=st.session_state["current_genre"])
                    st.session_state["awaiting_reason"] = None
                    st.rerun()
                
def display_fresh_movies(movies):
    cols = st.columns(3)
    for i, movie in enumerate(movies):
        col = cols[i % 3]
        with col:
            if movie.get("poster_path"):
                poster_url = "https://image.tmdb.org/t/p/w500" + movie["poster_path"]
                st.image(poster_url)
            else:
                st.markdown("🎬 Poster not available")
            year = movie.get("release_date", "")[:4]   # "2024-03-01" → "2024"
            if year:
                st.write(f"{movie['title']} ({year})") 
            else:
                st.write(movie["title"])
            plats = clean_platform_names(movie.get("platforms", []))
            if plats:
                st.caption("📺 " + ", ".join(plats))
        
            title = movie["title"]
            b1, b2, b3 = st.columns(3)      # three mini-columns for the buttons
            with b1:
                if st.button("🤔", key=f"why_{i}_{title}", help="Why You'll Like It"):
                    if title not in st.session_state["explanations"]:
                        with st.spinner("💭 Thinking..."):
                            st.session_state["explanations"][title] = generate_explanation(movie, user_context=st.session_state.get("user_context", ""))
            if title in st.session_state["explanations"]:
                st.info(st.session_state["explanations"][title])
            
            with b2:
                if st.button("👍", key=f"yes_{i}_{title}", help="Interested"):
                    t_shown = st.session_state.get("t_shown", time.time())
                    decision_time = round(time.time() - t_shown, 2)
                    log_feedback("guest", title, "accept",
                                 reason=str(decision_time),
                                 genre=st.session_state["current_genre"])
                    st.toast("Noted 👍")

            with b3:
                if st.button("👎", key=f"no_{i}_{title}", help="Not interested"):
                    st.session_state["awaiting_reason"] = title
                    st.rerun()

            # Reason picker — only for the movie awaiting a reason
            if st.session_state["awaiting_reason"] == title:
                reason = st.radio(
                    "Why not?",
                    ["genre_mismatch", "storyline", "mood_mismatch", "already_watched", "other"],
                    key=f"reason_{i}_{title}"
                )
                if st.button("Submit", key=f"submit_{i}_{title}"):
                    log_feedback("guest", title, "reject", reason=reason,
                                 genre=st.session_state["current_genre"])
                    st.session_state["guest_rejected"].add(title)      # session-only hide
                    st.session_state["awaiting_reason"] = None
                    st.rerun()

# Sidebar — mode + user identity (shared across both input modes)
with st.sidebar:
    st.markdown("### 👤 Mode")
    mode = st.radio("Select Mode", ["Guest Mode", "Personal Mode"])
    if mode == "Personal Mode":
        user_id = st.number_input("User ID (1-610)", min_value=1, max_value=610, value=1, step=1)
        incognito = st.toggle("🕵️ Incognito")
    else:
        user_id = None
        incognito = False        # guest is never incognito

    


# Choose the mode 
input_mode = st.radio("How would you like to choose?",["Quick Select", "Describe your mood"])

if input_mode == "Quick Select":
    # show slider + genre
    # Mood slider
    mood = st.select_slider("How are you feeling ?",
                            options=["😠 Angry","😔 Sad", "😴 Tired", "😐 Neutral", "😊 Happy",  "🤩 Excited"])



    # Picker only shows in Guest Mode
    selected_platforms = []
    if user_id is None:
        st.markdown("**📺 Filter by platform (optional):**")
        selected_platforms = st.multiselect(
            "Select your streaming platforms",
            ["Netflix", "Amazon Prime Video", "JioHotstar", "Sony Liv"])
        
        st.markdown("**🌐 Language (optional):**")
        language = st.selectbox("Preferred language",
                    ["Any", "English", "Hindi", "Kannada", "Telugu", "Tamil", "Malayalam", "Korean"])
        language = None if language == "Any" else language
    else:
        st.caption("📺 Platform filter available in Guest Mode")
        language = None 

    

    # Genre based on mood suggestion
    genres = [
        "Action", "Adventure", "Animation",
        "Children", "Comedy", "Crime",
        "Documentary", "Drama", "Fantasy",
        "Film-Noir", "Horror", "Musical",
        "Mystery", "Romance", "Sci-Fi",
        "Thriller", "War", "Western"
    ]

    # mapping
    mood_suggestions = {
        "😠 Angry": ["Comedy", "Animation", 
                     "Musical"],
        "😔 Sad"     : ["Comedy", "Animation", 
                        "Musical"],
        "😴 Tired"   : ["Animation", "Comedy",
                        "Children"],
        "😐 Neutral" : ["Action", "Adventure",
                        "Documentary"],
        "😊 Happy"   : ["Comedy", "Romance",
                        "Musical"],
        "🤩 Excited" : ["Thriller", "Crime",
                        "Action", "Mystery"]
    }


    LANGUAGE_CODES = {
    "Any": None,
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn",
    "Telugu": "te",
    "Tamil": "ta",
    "Malayalam": "ml",
    "Korean": "ko",
    }

    # But user can change
    genre = st.selectbox("Pick a genre", genres, index=genres.index(mood_suggestions[mood][0]))

    if st.button("Get recommendations🎬"):
        with st.spinner("Finding movies..."):
            st.session_state["current_genre"] = genre
            st.session_state["user_context"] = f"They are feeling {mood.split()[-1]}."   # strips the emoji
            st.session_state["searched"] = True
            st.session_state["t_shown"] = time.time()
            if user_id is None:
                movies = guest_recommendations_with_platform(genre_name=genre, user_platforms=selected_platforms, n=12, language=language)
                movies = filter_rejected(movies, st.session_state["guest_rejected"])
                st.session_state["guest_movies"] = movies[:6]
                st.session_state["personal_movies"] = []
                st.session_state["explanations"] = {}
                st.session_state["rating_logged"] = False 
                st.session_state["t_shown"] = time.time()
                log_feedback("guest", "(session)", "shown",
                             reason=str(len(st.session_state["guest_movies"])),
                             genre=genre)
            else:
                if incognito:
                    rejected = st.session_state["guest_rejected"]
                else:
                    rejected, avoided = get_user_feedback(user_id)
                titles = get_recommendations(genre=genre, n=12, user_id=user_id)
                titles = filter_rejected(titles, rejected)
                titles = list(dict.fromkeys(titles))    # removes dupes, preserves order
                st.session_state["personal_movies"] = titles[:6]
                st.session_state["guest_movies"] = []
                st.session_state["explanations"] = {}
                st.session_state["rating_logged"] = False
                st.session_state["t_shown"] = time.time()
                if not incognito:
                    log_feedback(user_id, "(session)", "shown",
                                 reason=str(len(st.session_state["personal_movies"])),
                                 genre=genre)

    

    # Display OUTSIDE the button block
    if st.session_state["guest_movies"]:
        display_fresh_movies(st.session_state["guest_movies"])
    elif st.session_state["personal_movies"]:
        display_movies(st.session_state["personal_movies"], user_id, incognito)
    elif st.session_state["searched"]:
        st.warning("😕 No movies found for that combination. Try fewer platform filters or a different genre.")
    
    # Satisfaction rating — shown once results exist
    if st.session_state["guest_movies"] or st.session_state["personal_movies"]:
        st.markdown("---")
        rating = st.radio(
            "⭐ How satisfied are you with these recommendations?",
            [1, 2, 3, 4, 5],
            horizontal=True,
            index=None,
            key="satisfaction_quick"
        )
        if rating and not st.session_state["rating_logged"]:
            if not incognito:
                log_feedback(user_id if user_id else "guest", "(session)", "rate",
                             reason=str(rating),
                             genre=st.session_state["current_genre"])
            st.session_state["rating_logged"] = True
            st.success("Thanks for the feedback! 🙏")

    
else:
    user_text = st.text_input("Tell us how you're feeling")
    

    selected_platforms = []
    if user_id is None:
        st.markdown("**📺 Filter by platform (optional):**")
        selected_platforms = st.multiselect(
            "Select your streaming platforms",
            ["Netflix", "Amazon Prime Video", "JioHotstar","Sony Liv"])
        
        st.markdown("**🌐 Language (optional override):**")
        language_override = st.selectbox(
            "Preferred language",
            ["Auto-detect", "English", "Hindi", "Kannada", "Telugu", "Tamil", "Malayalam", "Korean"])
    else:
        st.caption("📺 Platform filter available in Guest Mode")
        language_override = "Auto-detect"

    if st.button("Get recommendations🎬"):
        with st.spinner("Finding movies..."):
            st.session_state["searched"] = True

            if user_id is None:
                intent = get_user_intent(user_text)
                genre = resolve_genre(intent)
                language = intent.get("language")
                if language_override != "Auto-detect":
                    language = language_override        # explicit choice wins over LLM guess

                st.session_state["current_genre"] = genre
                st.session_state["user_context"] = f"They described their state as: '{user_text}'."
                st.session_state["t_shown"] = time.time()
                movies = guest_recommendations_with_platform(genre_name=genre, user_platforms=selected_platforms, n=12, language=language)
                movies = filter_rejected(movies, st.session_state["guest_rejected"])
                st.session_state["guest_movies"] = movies[:6]
                st.session_state["personal_movies"] = []
                st.session_state["explanations"] = {}
                st.session_state["rating_logged"] = False 
                st.session_state["t_shown"] = time.time()
                log_feedback("guest", "(session)", "shown",
                             reason=str(len(st.session_state["guest_movies"])),
                             genre=genre)
            else:
                if incognito:
                    rejected = st.session_state["guest_rejected"]
                else:
                    rejected, avoided = get_user_feedback(user_id)
                titles, genre = get_smart_recommendations(user_text, user_id=user_id, n=12)
                st.session_state["current_genre"] = genre
                st.session_state["user_context"] = f"They described their state as: '{user_text}'."
                st.session_state["t_shown"] = time.time()
                titles = filter_rejected(titles, rejected)
                titles = list(dict.fromkeys(titles)) 
                st.session_state["personal_movies"] = titles[:6]
                st.session_state["guest_movies"] = []
                st.session_state["explanations"] = {}
                st.session_state["rating_logged"] = False
                st.session_state["t_shown"] = time.time()
                if not incognito:
                    log_feedback(user_id, "(session)", "shown",
                                 reason=str(len(st.session_state["personal_movies"])),genre=genre)



    # Display OUTSIDE the button block
    if st.session_state["guest_movies"]:
        display_fresh_movies(st.session_state["guest_movies"])
    elif st.session_state["personal_movies"]:
        display_movies(st.session_state["personal_movies"], user_id, incognito)
    elif st.session_state["searched"]:
        st.warning("😕 No movies found for that combination. Try fewer platform filters or a different genre.")
    
    # Satisfaction rating — shown once results exist
    if st.session_state["guest_movies"] or st.session_state["personal_movies"]:
        st.markdown("---")
        rating = st.radio(
            "⭐ How satisfied are you with these recommendations?",
            [1, 2, 3, 4, 5],
            horizontal=True,
            index=None,
            key="satisfaction_describe"
        )
        if rating and not st.session_state["rating_logged"]:
            if not incognito:
                log_feedback(user_id if user_id else "guest", "(session)", "rate",
                             reason=str(rating),
                             genre=st.session_state["current_genre"])
            st.session_state["rating_logged"] = True
            st.success("Thanks for the feedback! 🙏")

# ── Evaluation metrics (bottom of page) ──
st.markdown("---")
with st.expander("📊 System Evaluation Metrics"):
    m = compute_metrics()
    if m:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Acceptance Rate", f"{m['acceptance_rate']}%", help="Accepted recommendations ÷ total shown")
        c2.metric("Avg Decision Time", f"{m['avg_decision_time']}s", help="Time from recommendations shown to selection")
        c3.metric("Avg Satisfaction", f"{m['avg_satisfaction']}/5", help="User-rated satisfaction per session")
        c4.metric("CES", m['ces'], help="Choice Efficiency Score = Satisfaction ÷ Decision Time. Higher = satisfying choices made faster")
        st.caption(f"Based on {m['total_accepts']} accepts across {m['total_shown']} recommendations shown")
    else:
        st.caption("No feedback data yet")