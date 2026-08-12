## Dataset Observations
- 9742 movies, 100836 ratings
- 610 users
- Sparsity: 98.3%
- Rating scale: 0.5 to 5.0
- Most common rating: 4.0 (26818 times)
- Genres pipe separated

## Functions Built
- movies_by_genres(genre) — filters by genre
- get_poster(title) — fetches TMDB poster
- get_movie_description(title) -  fetches the overview 
- get_cb_recommendations(genre, n) - content based filtering
- get_cf_recommendations(user_id, n) -  collborative filtering
- get_hybrid_recommendations(user_id, genre, n,alpha=0.5,beta=0.5) - combines both filtering
- get_recommendations(genre, n, user_id=None) — toggles between guest and personal mode

## Content Based Filtering

TF-IDF converts movie attributes such as genres, keywords, and descriptions into numerical vectors. Cosine Similarity is then used to measure how similar movies are based on these features. This provides an efficient content-based recommendation approach

Genres alone are not enough to represent a movie. For example, two comedy movies can have completely different themes. TMDB descriptions help capture the actual story and essence of a movie, leading to more personalized recommendations.

Similarity shows how closely movies are related, while ratings indicate user preference. Multiplying both gives higher importance to movies that are similar to titles the user has rated highly.

Instead of comparing movies to a random movie from a genre, the genre itself is used as a reference document. This helps identify movies that best represent the genre and produces more accurate recommendations.

## Collaborative Filtering
The user–movie rating matrix is highly sparse because most users rate only a small fraction of the available movies. This makes it difficult to identify meaningful similarities between users or items using traditional collaborative filtering methods. Surprise SVD addresses this challenge by learning hidden patterns from the available ratings instead of relying on direct user-user or item-item comparisons.

Surprise SVD decomposes the user–item rating matrix into lower-dimensional latent user and item factor matrices using Funk SVD (Matrix Factorization). These latent factors capture hidden preferences of users and characteristics of movies. The predicted rating is computed as the interaction (dot product) of the user and item latent vectors, along with user bias, item bias, and the global average rating.

Unlike memory-based collaborative filtering, which explicitly computes similarities between users or items, Surprise SVD is a model-based approach that learns latent representations from historical ratings. This enables it to generalize better, handle sparse datasets more effectively, and provide accurate recommendations even when users have rated only a few movies.

After the model is trained, it predicts ratings for all movies that a user has not yet rated or watched. These predicted ratings are then ranked in descending order, and the movies with the highest predicted scores are recommended to the user. This personalized recommendation process helps users discover movies that closely match their inferred preferences.

## Hybrid Model
Content-Based Filtering recommends movies based on movie attributes such as genres, keywords, and descriptions. However, similar content does not always match user preferences. Collaborative Filtering uses user rating patterns to discover movies liked by users with similar tastes.

Combining both approaches produces more personalized recommendations while also handling cold-start situations where new users have insufficient rating history.

Recommendations from both Content-Based and Collaborative Filtering are ranked in order of relevance. Higher-ranked movies are assigned higher scores because they are considered more relevant. This allows the system to prioritize the strongest recommendations when generating the final list.

Collaborative Filtering captures real user preferences and behavior, making recommendations more personalized. Content-Based Filtering provides stability and helps with cold-start users. Equal weights were assigned to Content-Based Filtering and Collaborative Filtering to ensure a balanced recommendation strategy. 

Using a 0.5/0.5 weighting allows the system to benefit from the strengths of both approaches without giving excessive importance to either method.

Precision@5: 0.59, Recall@5: 0.23 using Surprise SVD with proper train-test split.

## Issues Faced

TMDB Poster Mismatch Issue
While fetching movie posters, "Toy Story" was incorrectly matched with the poster of a newer movie version. This occurred because the movie title alone was used as the search query. The issue was resolved by including the release year in the TMDB search request, resulting in more accurate poster retrieval.

Case Sensitivity in Genre Filtering
The genre filter initially required exact capitalization. User inputs such as "comedy" returned empty results because the stored genre was "Comedy". The issue was resolved by making the comparison case-insensitive.

DataFrame vs Series Issue
While iterating over movie titles, the loop returned the column name ("title") instead of the actual movie titles. This occurred because the column was not converted into a list before iteration. The issue was resolved using .tolist() to extract the actual values.

ConnectionResetError During Streamlit Execution
Repeatedly closing and reopening the Streamlit application during testing occasionally interrupted active TMDB API connections, resulting in ConnectionResetError. The issue was resolved by implementing try/except blocks and adding a timeout parameter to handle connection failures gracefully.

IndexError Due to Incorrect Brackets
The get_poster() function initially assumed that every movie title contained a release year in brackets, such as "Toy Story (1995)". During testing, some titles lacked this format, causing split ("(")[1] to raise an IndexError. The issue was resolved by checking for the presence of brackets before extracting the year.

MediaFileStorageError in Poster Retrieval
The get_poster() function initially returned the string "No movies found" when a poster was unavailable. This caused MediaFileStorageError during image rendering. Replacing the string with None allowed proper handling of missing posters.

Notebook Memory Isolation Issue
Different recommendation modules were initially developed in separate Jupyter notebooks for better organization. However, each notebook maintained its own memory and variables, making integration difficult. The issue highlighted the importance of consolidating shared logic when building a complete application.

User ID Type Mismatch in Feedback Filtering
After Guest Mode feedback (stored under the identifier "guest") was added to the feedback file, filtering by a numeric user ID silently returned no results. A CSV column containing both numbers and the string "guest" is loaded by pandas as text, so an integer comparison (user_id == 1) no longer matched the stored value ("1"). The issue was resolved by comparing both sides as strings, and is a reminder that mixed-type columns are read as text.


## Genre Taxonomy Verification
During testing, certain recommended titles (e.g., "Dead Fury", "Sapphire Blue") appeared unfamiliar or seemingly mismatched. Verification against the MovieLens genres column confirmed these recommendations were accurate — the system correctly surfaces genre-matching content regardless of title popularity, demonstrating reliable genre-based filtering even for lesser-known titles.

Note: A small number of posters fetched via TMDB API may display incorrect orientation due to source metadata issues. This is a TMDB-side limitation outside our control.

## Model Evaluation 

The dataset was divided into 80% training data and 20% testing data using an 80/20 train-test split with random_state = 42 to ensure reproducibility. The Surprise SVD model was trained on the training set and evaluated on the unseen test set. Performance was measured using RMSE, MAE, Precision@5, and Recall@5.

| Metric | Value |
|--------|-------|
| RMSE | 0.8813 |
| MAE | 0.6779 |
| Precision@5 | 0.5930 |
| Recall@5 | 0.2297 |

RMSE (0.8813): On average, the model's predicted ratings differ from the actual ratings by about 0.88 rating points. A lower RMSE indicates better prediction accuracy.

MAE (0.6779): The average absolute prediction error is approximately 0.68 rating points, showing that the model makes reasonably accurate rating predictions.

Precision@5 (0.5930): Around 59.3% of the top 5 recommended movies are relevant to the user, indicating good recommendation quality.

Recall@5 (0.2297): The model retrieves about 22.97% of all relevant movies within its top 5 recommendations, suggesting that while the recommendations are generally relevant, some relevant movies are not included in the top recommendations.

Overall, the results indicate that the Surprise SVD model provides accurate rating predictions and high-quality personalized recommendations, making it an effective approach for handling sparse movie recommendation datasets.


## LLM Intent Understanding
Many users may not know the exact genre they want to watch and instead describe their preferences in plain language. Using the Groq LLM allows the system to understand the user's intent and generate more personalized recommendations.

The LLM analyzes the user's input and extracts only the information that is explicitly mentioned, leaving all other fields as null.

It extracts:
mood – how the user is feeling
vibe – the type of experience the user wants
genre_preference – the preferred genre (if specified)
reference_title – a movie mentioned by the user (if any)
avoid_genres – genres the user wants to exclude

The system distinguishes between mood and vibe to better understand user intent.

Mood represents how the user is currently feeling.
Vibe represents the type of content the user explicitly wants to watch.
Mood and vibe can be different. For example, a user may feel sad but want to watch a suspense movie.
When both are present, vibe is given higher priority because it reflects the user's explicit viewing preference.

Preference Selection Order
The system evaluates user preferences in a predefined order and uses the first available preference to generate recommendations.

Selection Order:
Genre Preference – If the user explicitly mentions a genre, it is used because it is the most specific request.
Vibe – If no genre is provided, the system checks the type of content the user wants to watch.
Mood – If neither genre nor vibe is available, the user's emotional state is considered.
Default (Drama) – If no clear preference can be extracted, the system defaults to Drama to ensure recommendations are always generated.

## OTT Platform Filter

An OTT availability filter was added so users can restrict recommendations to the streaming platforms they subscribe to (Netflix, Amazon Prime Video, JioHotstar, and others), using TMDB's watch-providers data for the India region.

During implementation, the platform filter frequently returned very few or zero movies.Diagnostic testing traced this to the MovieLens dataset itself: its titles extend only to around 2016. Streaming catalogues rotate continually as licensing deals expire, so older titles — including international ones — are frequently no longer available on current Indian OTT services, or appear only as rent/buy rather than subscription (flatrate). As a result, filtering MovieLens movies by platform correctly removed nearly all of them. This was confirmed by checking known titles — for example, "Toy Story" resolves to JioHotstar and "Shrek" to Amazon Prime Video, with neither present on Netflix.

To resolve this, TMDB's discover endpoint was introduced as a live content source for Guest Mode. Instead of drawing from the older MovieLens corpus, Guest Mode now fetches fresh, currently popular movies directly from TMDB for the requested genre, each already carrying its ID, title, poster, release date, and streaming availability. These fresh titles are far more likely to be present ontoday's OTT platforms, which allows the platform filter to return meaningful results.

Because TMDB and MovieLens use different genre vocabularies (for example,"Sci-Fi" versus "Science Fiction", "Children" versus "Family", "Musical" versus "Music"), a small translation layer maps the LLM's genre names to TMDB's genre IDs before querying. Genres with no TMDB equivalent, such as "Film-Noir", fall back to Drama, consistent with the system's existing default.

The streaming region is currently fixed to India (IN), matching the project's target users. The region is already a parameter throughout the pipeline, so region selection (via a dropdown) is a straightforward future enhancement.

## Platform Availability & Data Quality 
The filter reports subscription (flatrate) availability only, since a user selecting their platforms expects titles they can stream immediately without additional payment. Several providers appear only under TMDB's rent/buy
categories for the Indian region — inspection of sample titles showed Zee5 and YouTube listed under "rent" and "buy" rather than "flatrate". Providers with no reliable flatrate presence therefore return no results under a subscription filter, and the selector was limited to Netflix, Amazon Prime Video, JioHotstar, and Sony Liv, each verified to return genuine subscription availability. Note that providers may offer both models — Amazon, for example, has a subscription catalogue ("Amazon Prime Video") alongside a separate rental store ("Amazon Video") — and only the subscription entry is matched. Displaying rent/buy availability as clearly labelled secondary options is noted as a future enhancement.

Platform matching was made case-insensitive after testing revealed that TMDB's provider names did not always match the application's labels exactly (for example, "Sony Liv" rather than "Sony LIV"). Comparing both sides in lowercase removed this class of mismatch. The discovery query was also refined to target platforms directly using TMDB's with_watch_providers parameter with a platform-to-provider-ID mapping, so the system requests movies available on the selected platform rather than fetching globally popular movies and checking whether they happen to be available there. The mapping retains all researched providers, so others can be enabled if their data quality improves.

Because the discovery endpoint sorts deterministically by popularity, repeated searches with identical inputs returned the same titles. A randomly selected result page (1–3) was introduced to provide variety across searches while keeping recommendations within the popular, recognisable range.

## Regional Language Filtering

A guide review raised a valid limitation: recommendations were confined to international, primarily English-language content, even though the system's own reference-title handling (a request such as "similar to Vincenzo") could imply a specific language. Investigation confirmed this — the LLM correctly identified the reference title but reduced it to a genre alone, losing the language signal entirely.

Language support was added to Guest Mode, which draws from TMDB's discover endpoint. The LLM's intent-extraction prompt was extended with a language field, populated only when a language, region, or a reference title strongly
associated with one is mentioned; a missing comma in the prompt's example schema was found to cause this field to be omitted inconsistently from the model's response, and was corrected. The extracted language is translated to
an ISO 639-1 code and passed to TMDB's with_original_language parameter.

Personal Mode was evaluated for the same capability and found infeasible: a direct search of MovieLens found only two titles referencing Indian cinema out of 9,742 movies, and the dataset carries no language metadata at all. The
limiting factor is the absence of regional content in the dataset itself, rather than any technical constraint on filtering it.

Testing surfaced a further issue specific to regional languages. The existing vote-count quality threshold, calibrated for globally popular content, proved too strict for regional catalogues — a Kannada comedy query returned no results despite TMDB's unfiltered catalogue containing 415 such titles. Vote count reflects audience reach rather than quality, and regional cinema naturally receives fewer international votes even when well received within its own audience. The threshold was therefore removed for regional languages. This surfaced a second issue: the existing random-page selection assumed a fixed page range appropriate for large, globally popular catalogues, and produced empty results when applied to a smaller filtered set. The page range
is now determined dynamically per query, using TMDB's own reported page count, so results are sampled from the catalogue that genuinely exists rather than an assumed one.

## Why You'll Like It (Explainability)

To make recommendations transparent, each suggested movie can display a short "Why You'll Like It" reason generated by the Groq LLM. Rather than pre-generating explanations for every movie, they are produced on demand — only when the user clicks a movie's "Why?" button. This lazy-loading approach conserves the LLM
token budget, since explanations are generated only for movies the user is actually interested in.

A single explanation function handles both modes despite their different data shapes. Guest Mode passes a movie object that already contains the TMDB overview, while Personal Mode passes only a MovieLens title string. The function detects the input type and, for the title-string case, fetches the overview from TMDB
before generating the explanation, so both modes produce equally specific reasons.

Because Streamlit re-runs the entire script on every interaction, the recommendation list and generated explanations are stored in st.session_state.This ensures that clicking a "Why?" button does not regenerate or lose the displayed movies, and that previously generated explanations remain visible. Explanations are also cached per movie, so clicking the same button twice does not trigger a second LLM call. The stored explanations are cleared whenever a new search is performed.

Note: LLM-generated explanations can occasionally introduce plausible but inaccurate plot details when a movie's overview is sparse. As the explanations serve as suggestive guidance rather than factual summaries, this limitation is acceptable within the system's scope.

## Feedback & Refinement ("Not Interested")

A feedback mechanism was added so users can mark recommendations they do not want, and the system refines future results accordingly. Each movie carries a "Not Interested" button that reveals a reason picker: wrong genre, storyline, mood mismatch, already watched, or other. Capturing the reason rather than a plain rejection allows different responses — a genre mismatch causes that genreto be avoided in future automatic selections, while the remaining reasons simply hide the specific title.

Feedback storage differs by mode, following the same identity-based reasoning used elsewhere in the system. Guest Mode has no user identity, so its rejections are held in st.session_state and last only for the session, consistent with its anonymous nature. Personal Mode has a user_id, its feedback is written to persistent storage and persists across sessions (see Persistent Feedback Storage). A single file serves all users, with a user_id column distinguishing them, mirroring how a database table would store the data. The schema records user_id, movie title, action, reason,the genre being browsed, and a timestamp. The action and timestamp fields are included in anticipation of later metrics (acceptance rate, decision time, satisfaction), so the same file can capture accept and rating events without a schema change.

When recommendations are generated, rejected titles are removed, and for automatic genre selection any avoided genres are skipped. Because filtering removes items, a larger buffer is fetched before trimming to the required count, mirroring the approach used for the platform filter. Guest rejections are also logged to the file under an anonymous identifier so that aggregate evaluation metrics can include guest activity, while session state alone controls what each guest sees.

User identity is selected through a sidebar control. Personal Mode exposes a numeric input for the MovieLens user ID (1–610), allowing different users to be demonstrated; the collaborative filtering component then produces distinct recommendations per user, making personalisation visible. In a production system this identifier would be set internally following authentication; direct selection is used here for demonstration, and full user authentication is noted as future scope.

During this work the collaborative filtering component was found to ignore genre, returning the same highly predicted titles regardless of the selected genre. It was updated to rank only within the requested genre's candidate pool, so the hybrid now respects the chosen genre while still ranking by predicted user preference.

Because all guests share the "guest" identifier in the feedback file, guest rejections are never read back from it for filtering — doing so would leak one guest's rejections to another. Instead, each guest's rejections are held in their own session state, keeping anonymous sessions independent. The file's guest rows exist only for aggregate metrics.

## Incognito Mode

Incognito Mode was added as a privacy option within Personal Mode, modelled on the private-browsing behaviour of web browsers. It is exposed as a toggle that appears only once a user identity is selected, reflecting that incognito is asetting on a personal session rather than a separate mode.

The behaviour combines the two existing modes: like Personal Mode, it reads the user's rating history so that collaborative filtering still produces personalised recommendations; like Guest Mode, it writes nothing to persistent storage. When incognito is active, "Not Interested" feedback is held only in session state, so
rejected titles are hidden for the duration of the session but no record is written to the feedback file. Recommendation quality is therefore unchanged, while the session leaves no trace.

This required only a single conditional at each write and read point — feedback is written to the file unless incognito is active, and rejected titles are read from session state rather than the file. The personalisation path (the collaborative filtering call keyed by user ID) is deliberately left unchanged, as incognito restricts what is stored, not what is used.


## Evaluation Metrics Collection

To support the online evaluation metrics defined in the project, the application records user interactions as they occur. Three signals are captured alongside the existing rejection feedback: an acceptance signal, the time taken to decide, and a per-session satisfaction rating.

Each recommendation carries an "Interested" control, which records an accept event. The wording was chosen deliberately — the system recommends rather than streams, so the signal represents acceptance of a recommendation rather than playback. Decision Time is measured by recording a timestamp when recommendations are displayed and computing the elapsed interval when a recommendation is accepted. A satisfaction rating (1–5) is presented once beneath the results and recorded a single time per search, guarded by a session flag so that Streamlit's
re-runs do not create duplicate entries.

The number of recommendations actually displayed is also logged, rather than assumed, because platform and rejection filtering can reduce a result set below the requested count. This provides an accurate denominator for the acceptance rate. All events reuse the existing feedback schema, with the reason field holding the elapsed seconds for accept events, the score for rating events, and the displayed count for shown events, so no schema change was required.

Metrics are computed across all recorded activity, reflecting overall system performance rather than individual users, and are displayed in an expandable panel beneath the recommendations. Acceptance Rate is the number of accepted recommendations divided by the total shown; Decision Time and Satisfaction are averages of their recorded values; and the Choice Efficiency Score is satisfaction divided by decision time, so a higher value indicates that satisfying choices were made more quickly. Consistent with the privacy guarantee, no events are recorded
during incognito sessions.

Note: the values currently shown are derived from development testing and are not representative of genuine usage. A separate evaluation session with real users is required before these figures can be reported.

## Persistent Feedback Storage (Supabase)

Feedback was initially written to a local CSV file, which is sufficient during development but unsuitable for a deployed application. Streamlit Community Cloud provides only ephemeral storage, so a file written by the deployed app can be lost when the application restarts or sleeps — evaluation data collected from real users would not survive. An external database was therefore required.

Supabase was selected over alternatives such as Google Sheets because authentication requires only a project URL and a publishable key, rather than a service-account credential file, and because it is a managed PostgreSQL database
rather than a spreadsheet, which is closer to how production systems store data. A single feedback table mirrors the previous CSV schema, with user_id, movie title, action, reason, and genre stored as text and the timestamp stored as a proper timestamp type.

Two configuration details required attention. Row Level Security, which restricts access at the level of individual rows, is enabled by default on new tables and denies all access when no policies are defined; inserts then fail silently, appearing to succeed while writing nothing. As the feedback data is anonymous evaluation activity rather than per-user private information, row level security was disabled for this table. Secondly, the client library appends the REST path to the configured project URL, so including that path in the stored URL produced
a duplicated path and an invalid-request error.

The three feedback functions were rewritten to query the database rather than read the file. Filtering by user is now

## Deployment

The application was deployed to Streamlit Community Cloud from a private GitHub repository. Keeping the repository private during the submission period avoids any risk of the work being copied before it is assessed, while the deployed application itself is set to public so that evaluation participants can access it without needing accounts. API credentials are supplied through the platform's secrets manager rather than the local environment file, which is excluded from version control.

The initial deployment failed with a module import error for the collaborative filtering library. The package is partly implemented in C and requires compilation when no pre-built distribution is available for the target Python
version; the build environment could not compile it. Pinning the deployment to Python 3.11, for which a pre-built distribution exists, resolved the issue without any code changes.

Two characteristics of the free hosting tier are worth noting. Applications are suspended after a period of inactivity and take roughly thirty seconds to resume on the next visit, so the application should be opened shortly before any demonstration. Local file storage is also ephemeral, which was the reason for migrating feedback collection to an external database before deployment.

## Refining Explanation Personalisation

During the evaluation, a participant entered an emotionally specific free-text description of their state and received an explanation describing the film's themes without any reference to the mood expressed. Inspecting the
implementation showed that the explanation function accepted a user-context parameter, but the application never supplied it — the language model therefore received only the movie's title and overview, and could only describe the film itself rather than its suitability for the user.

Two changes were required. The user's context is now stored when recommendations are generated — the selected mood in the guided input path, and the free-text description in the natural-language path — and passed to the
explanation function. The prompt was also rewritten: rather than asking why a user might enjoy the film, it now instructs the model to acknowledge the user's stated state, connect a specific element of the film to it, and give the reason, while avoiding plot summary. Both changes were necessary; supplying the context without instructing the model to use it still produced generic descriptions.

The mood vocabulary was also extended. The original set covered sadness, tiredness, neutrality, happiness and excitement, but had no entry for anger — a negative state with high arousal, which the existing options do not represent. Anger was added and mapped to uplifting genres, consistent with the mood-repair approach applied to other negative states. The addition required updating the genre mapping, the language model's permitted mood values, and the interface options together, as any of these alone would produce a mismatch.

## User Evaluation Results

The deployed application was evaluated with approximately ten participants, who used it independently on their own devices. Because Guest Mode is anonymous by design, individual sessions cannot be distinguished within the collected data; results are therefore reported as aggregate activity. Analysis is restricted to the evaluation dates, excluding developer testing conducted on other days. Activity in Incognito Mode is deliberately not recorded, so any evaluation conducted in that mode is absent from the dataset — an inherent consequence of
offering a no-tracking option.

In Guest Mode, twenty-five search sessions produced one hundred and fifty recommendations, of which nineteen were accepted, giving an acceptance rate of 12.7%. Because each search presents six recommendations and a user typically
selects at most one, the acceptance rate is structurally bounded at approximately 16.7%; the observed figure represents roughly three-quarters of that maximum. Median decision time was 40.2 seconds, reported in preference to
the mean of 50.0 seconds as it is less affected by extended sessions arising from unsupervised remote testing. Eleven session ratings were recorded, of which nine were four or above on a five-point scale, giving an average of
3.91. Only three rejections occurred, none of which cited a genre mismatch.

A supplementary session evaluated Personal Mode, which the first cohort had not used. Fifteen sessions produced ninety recommendations with seven acceptances (7.8%), a median decision time of 28.5 seconds, and an average satisfaction of 3.27. Satisfaction here was polarised rather than uniformly moderate, with three ratings of one and four of five, in contrast to the tight clustering around four observed in Guest Mode.

The lower and more variable satisfaction in Personal Mode is best explained by the evaluation design rather than the recommendation approach. Participants were assigned MovieLens user identifiers and therefore received recommendations derived from another individual's rating history rather than their own. Where an assigned profile happened to align with a participant's taste, satisfaction was high; where it did not, it was low. The bimodal distribution is consistent with this explanation. Guest Mode, by contrast, draws on current popular titles with
poster and availability information, which are more immediately recognisable.