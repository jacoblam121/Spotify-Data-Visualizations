#!/usr/bin/env python3
"""
Artist Verification System
==========================
Verifies correct artist identity using user's listening history and multiple validation methods.

Priority order:
1. MBID matching (most reliable)
2. Track-based verification against user's history
3. Name similarity + listener count heuristics

Handles dual-profile scenarios where display and functional profiles differ.
"""

import json
import logging
import unicodedata
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import difflib
from collections import defaultdict

logger = logging.getLogger(__name__)

# Pre-compile regex patterns for performance
REMIX_PATTERNS = re.compile(
    r'\s*(\(live.*\)|\(radio edit\)|\(remix.*\)|\(feat\..*\)|-.*remix.*|-.*version.*)',
    re.IGNORECASE
)

def normalize_title(title: str) -> str:
    """
    Normalize track title for robust matching across character sets.
    
    Uses aggressive Unicode normalization to handle international characters,
    full-width/half-width differences, and case folding.
    """
    return unicodedata.normalize('NFKC', title).casefold().strip()

def clean_title(title: str) -> str:
    """Remove remix/live/radio edit metadata from track titles."""
    return REMIX_PATTERNS.sub('', title).strip()

def canonicalize_title(title: str) -> str:
    """Full title canonicalization: clean metadata then normalize."""
    return normalize_title(clean_title(title))

@dataclass
class TrackMatch:
    """Represents a track match between user data and API data."""
    user_track: str
    api_track: str
    similarity: float
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'user_track': self.user_track,
            'api_track': self.api_track,
            'similarity': self.similarity
        }

@dataclass
class TrackMatchEvidence:
    """Structured evidence from track matching analysis."""
    total_user_tracks: int
    match_count: int
    strong_match_count: int  # score > 0.9
    perfect_match_count: int  # score > 0.98
    average_score_of_matches: float
    best_match_score: float
    matched_pairs: List[TrackMatch]
    
    @property
    def match_ratio(self) -> float:
        """Ratio of matched tracks to total user tracks."""
        return self.match_count / self.total_user_tracks if self.total_user_tracks > 0 else 0.0
    
@dataclass
class VerificationResult:
    """Result of artist verification process."""
    artist_name: str
    chosen_profile: Dict[str, Any]
    confidence_score: float
    verification_method: str
    all_candidates: List[Dict[str, Any]]
    track_matches: List[TrackMatch]
    debug_info: Dict[str, Any]

class ArtistVerifier:
    """
    Verifies artist identity using multiple validation methods.
    
    Core functionality:
    1. Load user's listening history
    2. Compare candidate profiles against user data
    3. Score profiles based on multiple criteria
    4. Return highest confidence match
    """
    
    def __init__(self, data_path: str = "spotify_data.json"):
        """
        Initialize verifier with user's listening history.
        
        Args:
            data_path: Path to user's data file (JSON for Spotify, CSV for Last.fm)
        """
        self.user_tracks_by_artist = {}
        self.user_albums_by_artist = {}
        self.user_artist_mbids = {}  # artist_name -> mbid mapping for Last.fm data
        self.data_path = data_path
        self.data_source = self._detect_data_source(data_path)
        
        # Scoring weights (tunable based on testing)
        self.weights = {
            'track_similarity': 0.5,
            'album_similarity': 0.3,
            'name_similarity': 0.15,
            'listener_reasonableness': 0.05
        }
        
        self._load_user_data()
        
    def _detect_data_source(self, data_path: str) -> str:
        """
        Detect data source type based on file extension and content.
        
        Returns:
            'spotify' or 'lastfm'
        """
        if data_path.endswith('.csv'):
            return 'lastfm'
        elif data_path.endswith('.json'):
            return 'spotify'
        else:
            # Default to Spotify if unclear
            logger.warning(f"Unable to detect data source from path {data_path}, defaulting to Spotify")
            return 'spotify'
    
    def _load_user_data(self):
        """Load and process user's listening history from either Spotify or Last.fm data."""
        try:
            logger.info(f"📊 Loading user data from {self.data_path} (detected source: {self.data_source})")
            
            if self.data_source == 'spotify':
                self._load_spotify_data()
            elif self.data_source == 'lastfm':
                self._load_lastfm_data()
            else:
                logger.error(f"❌ Unsupported data source: {self.data_source}")
                return
                
            total_artists = len(self.user_tracks_by_artist)
            total_tracks = sum(len(tracks) for tracks in self.user_tracks_by_artist.values())
            total_mbids = len(self.user_artist_mbids)
            
            logger.info(f"✅ Loaded listening history: {total_artists} artists, {total_tracks} unique tracks")
            if total_mbids > 0:
                logger.info(f"✅ Extracted {total_mbids} artist MBIDs for verification")
            
        except FileNotFoundError:
            logger.warning(f"❌ Data file not found: {self.data_path}")
            logger.warning("   Verification will rely on name similarity and listener counts only")
        except Exception as e:
            logger.error(f"❌ Error loading user data: {e}")
    
    def _load_spotify_data(self):
        """Load Spotify JSON data."""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            spotify_data = json.load(f)
        
        # Group tracks and albums by artist
        for entry in spotify_data:
            artist_name = self._extract_artist_name(entry)
            track_name = self._extract_track_name(entry)
            album_name = self._extract_album_name(entry)
            
            if artist_name and track_name:
                if artist_name not in self.user_tracks_by_artist:
                    self.user_tracks_by_artist[artist_name] = set()
                self.user_tracks_by_artist[artist_name].add(track_name.lower().strip())
                
            if artist_name and album_name:
                if artist_name not in self.user_albums_by_artist:
                    self.user_albums_by_artist[artist_name] = set()
                self.user_albums_by_artist[artist_name].add(album_name.lower().strip())
    
    def _load_lastfm_data(self):
        """Load Last.fm CSV data."""
        import pandas as pd
        
        df = pd.read_csv(self.data_path)
        
        # Process each row
        for _, row in df.iterrows():
            artist_name = str(row.get('artist', '') or '').strip()
            track_name = str(row.get('track', '') or '').strip()
            album_name = str(row.get('album', '') or '').strip()
            artist_mbid = row.get('artist_mbid', '')
            
            if artist_name and track_name:
                if artist_name not in self.user_tracks_by_artist:
                    self.user_tracks_by_artist[artist_name] = set()
                self.user_tracks_by_artist[artist_name].add(track_name.lower().strip())
                
            if artist_name and album_name:
                if artist_name not in self.user_albums_by_artist:
                    self.user_albums_by_artist[artist_name] = set()
                self.user_albums_by_artist[artist_name].add(album_name.lower().strip())
            
            # Store MBID mapping for verification
            if artist_name and artist_mbid and str(artist_mbid).strip() and str(artist_mbid) != 'nan':
                self.user_artist_mbids[artist_name] = str(artist_mbid).strip()
    
    def _extract_artist_name(self, entry: Dict) -> Optional[str]:
        """Extract artist name from Spotify data entry."""
        for field in ['artistName', 'master_metadata_album_artist_name']:
            if field in entry and entry[field]:
                return entry[field].strip()
        return None
    
    def _extract_track_name(self, entry: Dict) -> Optional[str]:
        """Extract track name from Spotify data entry."""
        for field in ['trackName', 'master_metadata_track_name']:
            if field in entry and entry[field]:
                return entry[field].strip()
        return None
    
    def _extract_album_name(self, entry: Dict) -> Optional[str]:
        """Extract album name from Spotify data entry."""
        for field in ['master_metadata_album_album_name']:
            if field in entry and entry[field]:
                return entry[field].strip()
        return None
    
    def _get_user_tracks_for_artist(self, query_artist: str) -> set:
        """Get user tracks with case-insensitive fallback."""
        # Try exact match first
        tracks = self.user_tracks_by_artist.get(query_artist, None)
        if tracks is not None:
            return tracks
        
        # Case-insensitive fallback
        query_normalized = query_artist.casefold()
        for artist_name, artist_tracks in self.user_tracks_by_artist.items():
            if artist_name.casefold() == query_normalized:
                logger.debug(f"🔍 Found case-insensitive match: '{query_artist}' -> '{artist_name}'")
                return artist_tracks
        
        return set()
    
    def _get_user_albums_for_artist(self, query_artist: str) -> set:
        """Get user albums with case-insensitive fallback."""
        # Try exact match first
        albums = self.user_albums_by_artist.get(query_artist, None)
        if albums is not None:
            return albums
        
        # Case-insensitive fallback
        query_normalized = query_artist.casefold()
        for artist_name, artist_albums in self.user_albums_by_artist.items():
            if artist_name.casefold() == query_normalized:
                logger.debug(f"🔍 Found case-insensitive album match: '{query_artist}' -> '{artist_name}'")
                return artist_albums
        
        return set()
    
    def _get_user_mbid_for_artist(self, query_artist: str) -> Optional[str]:
        """Get user MBID with case-insensitive fallback."""
        # Try exact match first
        mbid = self.user_artist_mbids.get(query_artist, None)
        if mbid is not None:
            return mbid
        
        # Case-insensitive fallback
        query_normalized = query_artist.casefold()
        for artist_name, artist_mbid in self.user_artist_mbids.items():
            if artist_name.casefold() == query_normalized:
                logger.debug(f"🔍 Found case-insensitive MBID match: '{query_artist}' -> '{artist_name}'")
                return artist_mbid
        
        return None
    
    def verify_artist_candidates(self, query_artist: str, candidates: List[Dict[str, Any]], 
                                lastfm_api=None) -> VerificationResult:
        """
        Verify which candidate profile is the correct artist.
        
        Args:
            query_artist: Original artist name from user's data
            candidates: List of candidate profiles from API
            lastfm_api: Optional LastfmAPI instance for fetching additional data
            
        Returns:
            VerificationResult with chosen profile and confidence
        """
        if not candidates:
            raise ValueError("No candidates provided for verification")
        
        logger.info(f"🔍 Verifying artist '{query_artist}' among {len(candidates)} candidates")
        
        # Step 1: Try MBID matching first (most reliable)
        mbid_match = self._try_mbid_matching(query_artist, candidates)
        if mbid_match:
            logger.info(f"✅ MBID match found for '{query_artist}'")
            return VerificationResult(
                artist_name=query_artist,
                chosen_profile=mbid_match,
                confidence_score=0.99,  # Very high confidence for MBID matches
                verification_method="MBID_MATCH",
                all_candidates=candidates,
                track_matches=[],
                debug_info={
                    'method': 'mbid_exact_match',
                    'user_mbid': self._get_user_mbid_for_artist(query_artist) or '',
                    'matched_mbid': mbid_match.get('mbid', '')
                }
            )
        
        # Step 2: Try tiered track-based verification (high confidence)
        best_track_candidate, track_confidence = self._try_track_based_verification(query_artist, candidates, lastfm_api)
        if track_confidence >= 0.85:  # High confidence threshold
            logger.info(f"✅ Strong track evidence found for '{query_artist}' (confidence: {track_confidence:.3f})")
            return VerificationResult(
                artist_name=query_artist,
                chosen_profile=best_track_candidate['candidate'],
                confidence_score=track_confidence,
                verification_method="STRONG_TRACK_MATCH",
                all_candidates=candidates,
                track_matches=best_track_candidate['evidence'].matched_pairs,
                debug_info={
                    'method': 'strong_track_evidence',
                    'track_evidence': best_track_candidate['evidence'].__dict__,
                    'perfect_matches': best_track_candidate['evidence'].perfect_match_count,
                    'strong_matches': best_track_candidate['evidence'].strong_match_count
                }
            )
        
        # Step 3: Fall back to heuristic scoring for lower confidence cases
        scored_candidates = []
        
        for candidate in candidates:
            score_breakdown = self._score_candidate(query_artist, candidate, lastfm_api)
            scored_candidates.append({
                'candidate': candidate,
                'total_score': score_breakdown['total_score'],
                'breakdown': score_breakdown
            })
        
        # Sort by total score (highest first)
        scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
        best_candidate = scored_candidates[0]
        confidence = best_candidate['total_score']
        
        # Log detailed results
        logger.info(f"📊 Verification results for '{query_artist}':")
        for i, scored in enumerate(scored_candidates[:3], 1):
            cand = scored['candidate']
            breakdown = scored['breakdown']
            # Safely format listener count
            try:
                listeners = f"{cand.get('listeners', 0):,}"
            except (ValueError, TypeError):
                listeners = str(cand.get('listeners', 'unknown'))
            
            logger.info(f"   [{i}] {cand.get('name', 'Unknown')} "
                       f"({listeners} listeners) - Score: {scored['total_score']:.3f}")
            logger.info(f"       Track: {breakdown.get('track_score', 0):.3f}, "
                       f"Album: {breakdown.get('album_score', 0):.3f}, "
                       f"Name: {breakdown.get('name_score', 0):.3f}, "
                       f"Listener: {breakdown.get('listener_score', 0):.3f}")
        
        verification_method = "TRACK_BASED" if confidence > 0.7 else "HEURISTIC_BASED"
        
        return VerificationResult(
            artist_name=query_artist,
            chosen_profile=best_candidate['candidate'],
            confidence_score=confidence,
            verification_method=verification_method,
            all_candidates=candidates,
            track_matches=best_candidate['breakdown'].get('track_matches', []),
            debug_info=best_candidate['breakdown']
        )
    
    def _try_mbid_matching(self, query_artist: str, candidates: List[Dict]) -> Optional[Dict]:
        """
        Try to find exact MBID match between user's data and candidate profiles.
        
        This method provides definitive artist identification using MusicBrainz IDs.
        Only works with Last.fm data that contains artist MBIDs.
        
        Args:
            query_artist: Artist name from user's listening history
            candidates: List of candidate artist profiles from API
            
        Returns:
            Dict: Matching candidate profile if MBID match found, None otherwise
        """
        # Only works if we have MBID data (Last.fm source)
        if self.data_source != 'lastfm' or not self.user_artist_mbids:
            logger.debug(f"MBID matching not available (source: {self.data_source}, MBIDs: {len(self.user_artist_mbids)})")
            return None
        
        # Get user's MBID for this artist
        user_mbid = self._get_user_mbid_for_artist(query_artist)
        if not user_mbid:
            logger.debug(f"No MBID found in user data for artist '{query_artist}'")
            return None
        
        logger.debug(f"Looking for MBID match: '{query_artist}' -> {user_mbid}")
        
        # Check each candidate for matching MBID
        for candidate in candidates:
            candidate_mbid = candidate.get('mbid', '').strip()
            
            if candidate_mbid and candidate_mbid == user_mbid:
                logger.info(f"🎯 MBID match found: {candidate.get('name', 'Unknown')} ({candidate_mbid})")
                return candidate
        
        logger.debug(f"No MBID match found among {len(candidates)} candidates")
        return None
    
    def _gather_track_evidence(self, query_artist: str, candidate_tracks: List[str]) -> TrackMatchEvidence:
        """
        Gather comprehensive track matching evidence using improved similarity algorithms.
        
        This implements Gemini's suggested tiered approach with proper Unicode handling.
        """
        user_tracks = self._get_user_tracks_for_artist(query_artist)
        
        if not user_tracks or not candidate_tracks:
            return TrackMatchEvidence(
                total_user_tracks=len(user_tracks),
                match_count=0,
                strong_match_count=0,
                perfect_match_count=0,
                average_score_of_matches=0.0,
                best_match_score=0.0,
                matched_pairs=[]
            )
        
        # Canonicalize all track titles for robust comparison
        canonical_user_tracks = {canonicalize_title(track): track for track in user_tracks}
        canonical_candidate_tracks = {canonicalize_title(track): track for track in candidate_tracks}
        
        matches = []
        total_similarity = 0.0
        strong_matches = 0
        perfect_matches = 0
        
        for canonical_user, original_user in canonical_user_tracks.items():
            best_match = None
            best_similarity = 0.0
            best_candidate_original = None
            
            for canonical_candidate, original_candidate in canonical_candidate_tracks.items():
                # Use difflib for similarity calculation (can be upgraded to rapidfuzz later)
                similarity = difflib.SequenceMatcher(None, canonical_user, canonical_candidate).ratio()
                
                # Boost score for exact matches or substring containment
                if canonical_user == canonical_candidate:
                    similarity = 1.0
                elif canonical_user in canonical_candidate or canonical_candidate in canonical_user:
                    similarity = max(similarity, 0.85)
                
                if similarity > best_similarity and similarity > 0.6:  # Minimum threshold
                    best_similarity = similarity
                    best_match = original_candidate
                    best_candidate_original = original_candidate
            
            if best_match:
                match = TrackMatch(original_user, best_match, best_similarity)
                matches.append(match)
                total_similarity += best_similarity
                
                # Count strong and perfect matches based on Gemini's thresholds
                if best_similarity > 0.98:
                    perfect_matches += 1
                elif best_similarity > 0.9:
                    strong_matches += 1
        
        avg_score = total_similarity / len(matches) if matches else 0.0
        best_score = max((m.similarity for m in matches), default=0.0)
        
        return TrackMatchEvidence(
            total_user_tracks=len(user_tracks),
            match_count=len(matches),
            strong_match_count=strong_matches,
            perfect_match_count=perfect_matches,
            average_score_of_matches=avg_score,
            best_match_score=best_score,
            matched_pairs=matches
        )
    
    def _try_track_based_verification(self, query_artist: str, candidates: List[Dict], lastfm_api=None) -> Tuple[Optional[Dict], float]:
        """
        Evaluate candidates using track-based evidence with tiered confidence scoring.
        
        Implements Gemini's tiered approach:
        - Tier 2: Strong track correlation (0.90-0.95 confidence)
        - Returns best candidate with confidence score
        
        Returns:
            Tuple of (best_candidate_dict, confidence_score)
        """
        best_candidate = None
        best_confidence = 0.0
        
        for candidate in candidates:
            # Get tracks for this candidate
            candidate_tracks = self._get_candidate_tracks(candidate, lastfm_api)
            if not candidate_tracks:
                continue
            
            # Gather comprehensive track evidence
            evidence = self._gather_track_evidence(query_artist, candidate_tracks)
            
            # Calculate tiered confidence based on evidence
            confidence = self._calculate_track_confidence(evidence)
            
            logger.debug(f"Track evidence for {candidate.get('name', 'Unknown')}: "
                        f"{evidence.perfect_match_count} perfect, {evidence.strong_match_count} strong, "
                        f"confidence: {confidence:.3f}")
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_candidate = {
                    'candidate': candidate,
                    'evidence': evidence
                }
        
        return best_candidate, best_confidence
    
    def _calculate_track_confidence(self, evidence: TrackMatchEvidence) -> float:
        """
        Calculate confidence score based on track evidence using adaptive tiered approach.
        
        Tier 2 (Strong Track Correlation): 0.85-0.95 confidence
        - Adapts thresholds based on total user tracks available
        - For users with few tracks, emphasizes match quality over quantity
        """
        if evidence.total_user_tracks == 0:
            return 0.0
        
        # Adaptive thresholds based on user's track count
        # For users with few tracks, lower the absolute count requirements
        track_count_factor = min(1.0, evidence.total_user_tracks / 10.0)
        
        # Adjusted thresholds
        perfect_threshold = max(1, int(3 * track_count_factor))  # 1-3 based on track count
        strong_threshold = max(2, int(5 * track_count_factor))   # 2-5 based on track count
        min_match_threshold = max(1, int(3 * track_count_factor))  # 1-3 based on track count
        
        # Tier 2a: Strong track correlation (adaptive)
        # For large catalogs (>50 tracks), lower the match ratio requirement
        if evidence.total_user_tracks > 50:
            required_match_ratio = 0.2  # 20% for large catalogs
        else:
            required_match_ratio = 0.3  # 30% for smaller catalogs
        
        if evidence.perfect_match_count >= perfect_threshold and evidence.match_ratio >= required_match_ratio:
            # Base confidence of 0.90, boost for more perfect matches
            base_confidence = 0.90
            perfect_boost = min(0.05, evidence.perfect_match_count * 0.01)
            # Additional boost for high match ratio with small libraries
            if evidence.total_user_tracks < 5 and evidence.match_ratio >= 0.5:
                base_confidence += 0.02
            return min(0.95, base_confidence + perfect_boost)
        
        elif evidence.strong_match_count >= strong_threshold:
            # Base confidence of 0.87, boost for match ratio
            base_confidence = 0.87
            ratio_boost = min(0.08, evidence.match_ratio * 0.08)
            return min(0.95, base_confidence + ratio_boost)
        
        elif evidence.match_count >= min_match_threshold and evidence.match_ratio > 0.3 and evidence.average_score_of_matches > 0.85:
            # Good coverage with high quality matches (adjusted for small libraries)
            base_confidence = 0.85
            quality_boost = (evidence.average_score_of_matches - 0.85) * 0.2
            coverage_boost = min(0.05, (evidence.match_ratio - 0.3) * 0.071)
            return min(0.90, base_confidence + quality_boost + coverage_boost)
        
        # Special case: Very small library with high-quality matches
        elif evidence.total_user_tracks <= 5 and evidence.match_count >= 1 and evidence.average_score_of_matches >= 0.95:
            # For users with very few tracks, even one perfect match is significant
            base_confidence = 0.85
            quality_boost = (evidence.average_score_of_matches - 0.95) * 0.5
            ratio_boost = evidence.match_ratio * 0.05
            return min(0.90, base_confidence + quality_boost + ratio_boost)
        
        # Below tier 2 threshold - return lower confidence for heuristic fallback
        if evidence.match_count > 0:
            # Scale based on match quality and coverage
            base_score = evidence.average_score_of_matches * evidence.match_ratio
            return min(0.75, base_score * 0.8)  # Cap below tier 2 threshold
        
        return 0.0
    
    def _score_candidate(self, query_artist: str, candidate: Dict, lastfm_api=None) -> Dict:
        """Score a candidate profile against multiple criteria."""
        
        # Get candidate's name and basic info
        candidate_name = candidate.get('name', '')
        # Safely convert listeners to int, handling malformed data
        try:
            candidate_listeners = int(candidate.get('listeners', 0))
        except (ValueError, TypeError):
            logger.warning(f"Invalid listener count for {candidate_name}: {candidate.get('listeners')}")
            candidate_listeners = 0
        
        # Initialize scores
        track_score = 0.0
        album_score = 0.0
        track_matches = []
        
        # Track-based verification (if user data available and API provided)
        if self._get_user_tracks_for_artist(query_artist) and lastfm_api:
            try:
                # Fetch top tracks for this candidate
                candidate_tracks = self._get_candidate_tracks(candidate, lastfm_api)
                if candidate_tracks:
                    track_score, track_matches = self._calculate_track_similarity(
                        query_artist, candidate_tracks
                    )
            except Exception as e:
                logger.debug(f"Could not fetch tracks for candidate {candidate_name}: {e}")
        
        # Album-based verification (similar to tracks)
        if query_artist in self.user_albums_by_artist and lastfm_api:
            try:
                candidate_albums = self._get_candidate_albums(candidate, lastfm_api)
                if candidate_albums:
                    album_score = self._calculate_album_similarity(query_artist, candidate_albums)
            except Exception as e:
                logger.debug(f"Could not fetch albums for candidate {candidate_name}: {e}")
        
        # Name similarity
        name_score = self._calculate_name_similarity(query_artist, candidate_name)
        
        # Listener count reasonableness
        listener_score = self._calculate_listener_reasonableness(candidate_listeners)
        
        # Weighted total score
        total_score = (
            track_score * self.weights['track_similarity'] +
            album_score * self.weights['album_similarity'] +
            name_score * self.weights['name_similarity'] +
            listener_score * self.weights['listener_reasonableness']
        )
        
        return {
            'total_score': total_score,
            'track_score': track_score,
            'album_score': album_score,
            'name_score': name_score,
            'listener_score': listener_score,
            'track_matches': track_matches,
            'candidate_listeners': candidate_listeners
        }
    
    def _get_candidate_tracks(self, candidate: Dict, lastfm_api) -> List[str]:
        """Fetch top tracks for a candidate artist."""
        candidate_name = candidate.get('name', '')
        try:
            # Use the candidate's exact name for track lookup
            tracks_data = lastfm_api.get_top_tracks(candidate_name, limit=20)
            return [track.get('name', '').lower().strip() for track in tracks_data]
        except:
            return []
    
    def _get_candidate_albums(self, candidate: Dict, lastfm_api) -> List[str]:
        """Fetch top albums for a candidate artist."""
        candidate_name = candidate.get('name', '')
        try:
            # Use the candidate's exact name for album lookup
            albums_data = lastfm_api.get_top_albums(candidate_name, limit=10)
            return [album.get('name', '').lower().strip() for album in albums_data]
        except:
            return []
    
    def _calculate_track_similarity(self, query_artist: str, candidate_tracks: List[str]) -> Tuple[float, List[TrackMatch]]:
        """Calculate similarity between user's tracks and candidate's tracks."""
        user_tracks = self._get_user_tracks_for_artist(query_artist)
        
        if not user_tracks or not candidate_tracks:
            return 0.0, []
        
        matches = []
        total_similarity = 0.0
        
        for user_track in user_tracks:
            best_match = None
            best_similarity = 0.0
            
            for candidate_track in candidate_tracks:
                # Use difflib for fuzzy string matching
                similarity = difflib.SequenceMatcher(None, user_track, candidate_track).ratio()
                
                # Also check for substring matches (handles "radio edit", "remix" etc.)
                if user_track in candidate_track or candidate_track in user_track:
                    similarity = max(similarity, 0.8)
                
                if similarity > best_similarity and similarity > 0.6:  # Threshold for valid match
                    best_similarity = similarity
                    best_match = candidate_track
            
            if best_match:
                matches.append(TrackMatch(user_track, best_match, best_similarity))
                total_similarity += best_similarity
        
        # Normalize by number of user tracks
        final_score = total_similarity / len(user_tracks) if user_tracks else 0.0
        
        return final_score, matches
    
    def _calculate_album_similarity(self, query_artist: str, candidate_albums: List[str]) -> float:
        """Calculate similarity between user's albums and candidate's albums."""
        user_albums = self._get_user_albums_for_artist(query_artist)
        
        if not user_albums or not candidate_albums:
            return 0.0
        
        total_similarity = 0.0
        matches = 0
        
        for user_album in user_albums:
            for candidate_album in candidate_albums:
                similarity = difflib.SequenceMatcher(None, user_album, candidate_album).ratio()
                if similarity > 0.7:  # Higher threshold for albums
                    total_similarity += similarity
                    matches += 1
                    break  # Only count best match per user album
        
        return total_similarity / len(user_albums) if user_albums else 0.0
    
    def _calculate_name_similarity(self, query_name: str, candidate_name: str) -> float:
        """Calculate similarity between query name and candidate name."""
        # Exact match gets full score
        if query_name.lower() == candidate_name.lower():
            return 1.0
        
        # Handle special cases like "*luna" vs "luna" (should be penalized)
        if '*' in query_name and query_name.replace('*', '') == candidate_name.lower():
            return 0.3  # Low score for this mismatch
        
        # Use difflib for general similarity
        return difflib.SequenceMatcher(None, query_name.lower(), candidate_name.lower()).ratio()
    
    def _calculate_listener_reasonableness(self, listeners: int) -> float:
        """Calculate a score based on listener count reasonableness."""
        if listeners <= 0:
            return 0.0
        
        # Use logarithmic scale - diminishing returns for very high listener counts
        import math
        # Normalize to 0-1 scale where 100K listeners = ~0.8, 1M = ~1.0
        normalized = math.log10(listeners + 1) / 6.0  # log10(1M) ≈ 6
        return min(normalized, 1.0)

def create_test_verification():
    """Create a test verification for problematic artists."""
    print("🧪 Artist Verification Test Suite")
    print("=" * 40)
    
    verifier = ArtistVerifier()
    
    # Test cases for problematic artists
    test_cases = [
        {
            'query_artist': '*luna',
            'mock_candidates': [
                {'name': '*luna', 'listeners': 17154, 'url': 'https://last.fm/music/*luna'},
                {'name': 'luna', 'listeners': 539768, 'url': 'https://last.fm/music/luna'},
                {'name': 'Luna', 'listeners': 245678, 'url': 'https://last.fm/music/Luna'}
            ],
            'expected_choice': '*luna'
        },
        {
            'query_artist': 'YOASOBI',
            'mock_candidates': [
                {'name': 'YOASOBI', 'listeners': 713328, 'url': 'https://last.fm/music/YOASOBI'},
                {'name': 'YOASOBI (ヨアソビ)', 'listeners': 143, 'url': 'https://last.fm/music/YOASOBI+(ヨアソビ)'},
                {'name': 'ヨアソビ', 'listeners': 110, 'url': 'https://last.fm/music/ヨアソビ'}
            ],
            'expected_choice': 'YOASOBI'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🎯 Testing: {test_case['query_artist']}")
        print("-" * 30)
        
        result = verifier.verify_artist_candidates(
            test_case['query_artist'], 
            test_case['mock_candidates']
        )
        
        chosen_name = result.chosen_profile.get('name', 'Unknown')
        expected_name = test_case['expected_choice']
        
        print(f"   Query: {test_case['query_artist']}")
        print(f"   Chosen: {chosen_name}")
        print(f"   Expected: {expected_name}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print(f"   Method: {result.verification_method}")
        
        if chosen_name == expected_name:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            print(f"   Track matches: {len(result.track_matches)}")

if __name__ == "__main__":
    create_test_verification()