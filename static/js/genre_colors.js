/**
 * Genre Colors - JavaScript port of simplified_genre_colors.py
 * Provides the 12-genre color scheme for network visualization
 */

// 12 Core Genres - Accessible colors optimized for black background
const GENRE_COLORS = {
    // Primary 12 genres (vivid colors for black background)
    'pop': '#FFEB3B',           // Bright Yellow
    'rock': '#F44336',          // Material Red
    'metal': '#607D8B',         // Blue Gray
    'electronic': '#9C27B0',    // Purple
    'asian': '#FF69B4',         // Hot Pink (K-pop, J-pop, other Asian)
    'latin': '#DC143C',         // Crimson
    'country': '#FF9800',       // Orange
    'folk': '#FF9800',          // Same as country
    'r&b': '#8D6E63',           // Brown
    'soul': '#8D6E63',          // Same as R&B
    'hip-hop': '#FFD700',       // Gold
    'indie': '#00BCD4',         // Cyan
    'world': '#4CAF50',         // Green
    'classical': '#E8EAF6',     // Very Light Blue
    'orchestral': '#E8EAF6',   // Same as classical
    'ost': '#E8EAF6',          // Alias for orchestral
    
    // Fallbacks
    'other': '#C0C0C0',         // Silver
    'unknown': '#808080'        // Gray
};

// Genre mapping for classification
const GENRE_MAPPINGS = {
    'asian': ['k-pop', 'kpop', 'korean', 'j-pop', 'jpop', 'japanese', 'c-pop', 'cpop', 'chinese',
              'mandopop', 'cantopop', 'thai', 'vietnamese', 'indonesian', 'filipino'],
    'latin': ['latin', 'spanish', 'reggaeton', 'bachata', 'salsa', 'merengue', 'cumbia',
              'mexican', 'argentinian', 'brazilian', 'portuguese', 'bossa nova'],
    'electronic': ['electronic', 'edm', 'house', 'techno', 'dubstep', 'trance', 'drum and bass',
                    'synthpop', 'synthwave', 'ambient', 'dance', 'electronica'],
    'rock': ['rock', 'alternative rock', 'indie rock', 'classic rock', 'hard rock', 'punk rock',
             'grunge', 'garage rock', 'progressive rock'],
    'metal': ['metal', 'heavy metal', 'death metal', 'black metal', 'thrash metal', 'metalcore',
              'hardcore', 'doom metal', 'power metal'],
    'pop': ['pop', 'pop rock', 'electropop', 'dance pop', 'teen pop', 'bubblegum pop'],
    'hip-hop': ['hip-hop', 'rap', 'hip hop', 'trap', 'gangsta rap', 'conscious rap', 'old school rap'],
    'r&b': ['r&b', 'rnb', 'soul', 'neo-soul', 'contemporary r&b', 'motown', 'funk'],
    'soul': ['soul', 'neo-soul', 'motown', 'funk', 'r&b', 'rnb'],
    'country': ['country', 'americana', 'bluegrass', 'western', 'country rock'],
    'folk': ['folk', 'acoustic', 'singer-songwriter', 'indie folk', 'folk rock'],
    'indie': ['indie', 'independent', 'alternative', 'indie pop', 'indie folk', 'indie rock'],
    'classical': ['classical', 'orchestral', 'symphony', 'opera', 'baroque', 'romantic'],
    'orchestral': ['orchestral', 'soundtrack', 'film score', 'video game music', 'ost'],
    'ost': ['soundtrack', 'film score', 'video game music', 'ost', 'original soundtrack'],
    'world': ['world', 'african', 'middle eastern', 'celtic', 'folk', 'traditional',
              'ethnic', 'tribal', 'indigenous']
};

/**
 * Classify artist genre based on Last.fm and Spotify data
 * @param {Object} artistData - Artist data with lastfm_data and spotify_data
 * @returns {string} Primary genre string
 */
function classifyArtistGenre(artistData) {
    // Collect genres from sources with weights
    const sourceData = [];
    
    // Spotify genres (higher authority)
    if (artistData.spotify_data && artistData.spotify_data.genres) {
        const spotifyGenres = artistData.spotify_data.genres.slice(0, 5);
        spotifyGenres.forEach(genre => {
            sourceData.push({ tag: genre.toLowerCase(), source: 'spotify', weight: 2.0 });
        });
    }
    
    // Last.fm tags (lower authority)
    if (artistData.lastfm_data && artistData.lastfm_data.tags) {
        const lastfmGenres = artistData.lastfm_data.tags.slice(0, 5);
        lastfmGenres.forEach(tag => {
            sourceData.push({ tag: tag.name.toLowerCase(), source: 'lastfm', weight: 1.0 });
        });
    }
    
    // Fallback to genres_lastfm and genres_spotify arrays if present
    if (artistData.genres_spotify && Array.isArray(artistData.genres_spotify)) {
        artistData.genres_spotify.forEach(genre => {
            sourceData.push({ tag: genre.toLowerCase(), source: 'spotify', weight: 2.0 });
        });
    }
    
    if (artistData.genres_lastfm && Array.isArray(artistData.genres_lastfm)) {
        artistData.genres_lastfm.forEach(genre => {
            sourceData.push({ tag: genre.toLowerCase(), source: 'lastfm', weight: 1.0 });
        });
    }
    
    // Extract all tags for context-aware rules
    const allTags = sourceData.map(item => item.tag);
    
    // Context-aware rules for crossover artists
    if (allTags.includes('pop') && allTags.includes('country')) {
        return 'pop'; // Taylor Swift case
    }
    
    // Exclusive keywords that immediately determine genre
    const EXCLUSIVE_KEYWORDS = {
        'asian': ['k-pop', 'kpop', 'j-pop', 'jpop', 'korean pop', 'chinese pop'],
        'latin': ['reggaeton', 'bachata', 'latin pop', 'spanish pop']
    };
    
    for (const [category, keywords] of Object.entries(EXCLUSIVE_KEYWORDS)) {
        for (const item of sourceData) {
            for (const keyword of keywords) {
                if (item.tag.includes(keyword)) {
                    return category;
                }
            }
        }
    }
    
    // Score each genre category
    const genreScores = {};
    for (const item of sourceData) {
        const tag = item.tag.trim();
        const sourceWeight = item.weight;
        
        for (const [category, keywords] of Object.entries(GENRE_MAPPINGS)) {
            for (const keyword of keywords) {
                if (keyword.includes(tag) || tag.includes(keyword)) {
                    let score = sourceWeight;
                    
                    // Exact match bonus
                    if (keyword === tag) {
                        score *= 1.5;
                    }
                    
                    genreScores[category] = (genreScores[category] || 0) + score;
                    break; // Only count once per category
                }
            }
        }
    }
    
    // Return the highest scoring genre or 'other'
    if (Object.keys(genreScores).length > 0) {
        return Object.keys(genreScores).reduce((a, b) => 
            genreScores[a] > genreScores[b] ? a : b
        );
    }
    
    return 'other';
}

/**
 * Get hex color for a genre
 * @param {string} genre - Genre name
 * @returns {string} Hex color code
 */
function getGenreColor(genre) {
    return GENRE_COLORS[genre.toLowerCase()] || GENRE_COLORS['other'];
}

/**
 * Get all available genre colors for legend
 * @returns {Object} Object with genre: color pairs
 */
function getAllGenreColors() {
    return { ...GENRE_COLORS };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        GENRE_COLORS,
        GENRE_MAPPINGS,
        classifyArtistGenre,
        getGenreColor,
        getAllGenreColors
    };
}