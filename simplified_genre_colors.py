#!/usr/bin/env python3
"""
Simplified 12-Genre Color Scheme for D3.js Network Visualization
==============================================================
User-requested simplified genre scheme with accessibility improvements.
"""

# 12 Core Genres - Accessible colors optimized for black background
GENRE_COLORS = {
    # Primary 12 genres requested by user (with accessibility fixes)
    'pop': '#FFEB3B',           # Bright Yellow (not pastel - more visible)
    'rock': '#F44336',          # Material Red (distinct from crimson)
    'metal': '#607D8B',         # Blue Gray (not disabled gray)
    'electronic': '#9C27B0',    # Purple - synthetic/digital feel
    'asian': '#FF69B4',         # Hot Pink - K-pop, J-pop, other Asian
    'latin': '#DC143C',         # Crimson (distinct from red)
    'country': '#FF9800',       # Orange - earthy/traditional
    'folk': '#FF9800',          # Same as country (combined category)
    'r&b': '#8D6E63',           # Brown - soulful
    'soul': '#8D6E63',          # Same as R&B (combined category)
    'hip-hop': '#FFD700',       # Gold - prestigious/luxurious
    'indie': '#00BCD4',         # Cyan - alternative/independent
    'world': '#4CAF50',         # Green - global music (non-Asian/Latin)
    'classical': '#E8EAF6',     # Very Light Blue (not white!)
    'orchestral': '#E8EAF6',   # Same as classical (OSTs, soundtracks)
    'ost': '#E8EAF6',          # Alias for orchestral
    
    # Fallbacks
    'other': '#C0C0C0',         # Silver - unclassified
    'unknown': '#808080'        # Gray - error fallback
}

# Genre mapping for multi-genre classification
GENRE_MAPPINGS = {
    # Asian music categories
    'asian': ['k-pop', 'kpop', 'korean', 'j-pop', 'jpop', 'japanese', 'c-pop', 'cpop', 'chinese',
              'mandopop', 'cantopop', 'thai', 'vietnamese', 'indonesian', 'filipino'],
    
    # Latin music categories  
    'latin': ['latin', 'spanish', 'reggaeton', 'bachata', 'salsa', 'merengue', 'cumbia',
              'mexican', 'argentinian', 'brazilian', 'portuguese', 'bossa nova'],
    
    # Electronic music categories
    'electronic': ['electronic', 'edm', 'house', 'techno', 'dubstep', 'trance', 'drum and bass',
                    'synthpop', 'synthwave', 'ambient', 'dance', 'electronica'],
    
    # Rock categories
    'rock': ['rock', 'alternative rock', 'indie rock', 'classic rock', 'hard rock', 'punk rock',
             'grunge', 'garage rock', 'progressive rock'],
    
    # Metal categories  
    'metal': ['metal', 'heavy metal', 'death metal', 'black metal', 'thrash metal', 'metalcore',
              'hardcore', 'doom metal', 'power metal'],
    
    # Pop categories
    'pop': ['pop', 'pop rock', 'electropop', 'dance pop', 'teen pop', 'bubblegum pop'],
    
    # Hip-hop categories
    'hip-hop': ['hip-hop', 'rap', 'hip hop', 'trap', 'gangsta rap', 'conscious rap', 'old school rap'],
    
    # R&B/Soul categories
    'r&b': ['r&b', 'rnb', 'soul', 'neo-soul', 'contemporary r&b', 'motown', 'funk'],
    'soul': ['soul', 'neo-soul', 'motown', 'funk', 'r&b', 'rnb'],  # Alias mapping
    
    # Country/Folk categories
    'country': ['country', 'americana', 'bluegrass', 'western', 'country rock'],
    'folk': ['folk', 'acoustic', 'singer-songwriter', 'indie folk', 'folk rock'],
    
    # Indie categories
    'indie': ['indie', 'independent', 'alternative', 'indie pop', 'indie folk', 'indie rock'],
    
    # Classical/Orchestral categories
    'classical': ['classical', 'orchestral', 'symphony', 'opera', 'baroque', 'romantic'],
    'orchestral': ['orchestral', 'soundtrack', 'film score', 'video game music', 'ost'],
    'ost': ['soundtrack', 'film score', 'video game music', 'ost', 'original soundtrack'],
    
    # World music (non-Asian, non-Latin)
    'world': ['world', 'african', 'middle eastern', 'celtic', 'folk', 'traditional',
              'ethnic', 'tribal', 'indigenous']
}

def classify_artist_genre(artist_data) -> str:
    """
    Classify artist into one of the 12 simplified genres.
    
    Args:
        artist_data: Enhanced artist data with lastfm_data and spotify_data
        
    Returns:
        Primary genre string (one of the 12 core genres)
    """
    all_genres = []
    
    # Collect genres from all sources
    if artist_data.get('lastfm_data') and artist_data['lastfm_data'].get('tags'):
        lastfm_genres = [tag['name'].lower() for tag in artist_data['lastfm_data']['tags'][:5]]
        all_genres.extend(lastfm_genres)
    
    if artist_data.get('spotify_data') and artist_data['spotify_data'].get('genres'):
        spotify_genres = [genre.lower() for genre in artist_data['spotify_data']['genres'][:5]]
        all_genres.extend(spotify_genres)
    
    # Score each genre category
    genre_scores = {}
    for genre in all_genres:
        genre_lower = genre.lower().strip()
        for category, keywords in GENRE_MAPPINGS.items():
            for keyword in keywords:
                if keyword in genre_lower or genre_lower in keyword:
                    genre_scores[category] = genre_scores.get(category, 0) + 1
                    break  # Only count once per category
    
    # Return the highest scoring genre or 'other'
    if genre_scores:
        primary_genre = max(genre_scores, key=genre_scores.get)
        return primary_genre
    
    return 'other'

def get_multi_genres(artist_data, max_genres: int = 3) -> list:
    """
    Get up to max_genres for multi-genre artists (for Gemini's border approach).
    
    Args:
        artist_data: Enhanced artist data
        max_genres: Maximum number of genres to return
        
    Returns:
        List of genre strings, primary first
    """
    all_genres = []
    
    # Collect genres from all sources
    if artist_data.get('lastfm_data') and artist_data['lastfm_data'].get('tags'):
        lastfm_genres = [tag['name'].lower() for tag in artist_data['lastfm_data']['tags'][:5]]
        all_genres.extend(lastfm_genres)
    
    if artist_data.get('spotify_data') and artist_data['spotify_data'].get('genres'):
        spotify_genres = [genre.lower() for genre in artist_data['spotify_data']['genres'][:5]]
        all_genres.extend(spotify_genres)
    
    # Score each genre category
    genre_scores = {}
    for genre in all_genres:
        genre_lower = genre.lower().strip()
        for category, keywords in GENRE_MAPPINGS.items():
            for keyword in keywords:
                if keyword in genre_lower or genre_lower in keyword:
                    genre_scores[category] = genre_scores.get(category, 0) + 1
                    break
    
    # Return top scoring genres
    if genre_scores:
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        return [genre for genre, score in sorted_genres[:max_genres]]
    
    return ['other']

def get_genre_color(genre: str) -> str:
    """Get hex color for a genre."""
    return GENRE_COLORS.get(genre.lower(), GENRE_COLORS['other'])

def test_simplified_genres():
    """Test the simplified genre system."""
    print("🎨 Testing Simplified 12-Genre System")
    print("=" * 39)
    
    print(f"\n🌈 Core 12 Genres:")
    core_genres = ['pop', 'rock', 'metal', 'electronic', 'asian', 'latin', 
                   'country', 'r&b', 'hip-hop', 'indie', 'world', 'classical']
    
    for genre in core_genres:
        color = get_genre_color(genre)
        print(f"   {genre:12} {color}")
    
    print(f"\n🧪 Testing Multi-Genre Classification:")
    
    # Test cases for multi-genre artists
    test_cases = [
        {
            'name': '*Luna (Electronic + Asian)',
            'lastfm_data': {'tags': [{'name': 'electronic'}, {'name': 'k-pop'}, {'name': 'korean'}]},
            'spotify_data': {'genres': ['k-pop', 'electronic']}
        },
        {
            'name': 'Paramore (Pop + Rock)',
            'lastfm_data': {'tags': [{'name': 'rock'}, {'name': 'pop punk'}, {'name': 'alternative'}]},
            'spotify_data': {'genres': ['pop punk', 'emo', 'rock']}
        }
    ]
    
    for test_case in test_cases:
        artist_name = test_case['name']
        primary_genre = classify_artist_genre(test_case)
        multi_genres = get_multi_genres(test_case, max_genres=3)
        
        print(f"   {artist_name}:")
        print(f"     Primary: {primary_genre} ({get_genre_color(primary_genre)})")
        print(f"     Multi: {multi_genres}")
    
    print(f"\n✅ Simplified genre system ready!")

if __name__ == "__main__":
    test_simplified_genres()