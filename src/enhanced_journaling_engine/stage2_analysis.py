#!/usr/bin/env python3
"""
Stage 2: The Core Analysis Module (Thread Identification)

This module analyzes digitized journal entries to identify hidden narrative threads,
themes, characters, and sentiment using the Gemini API.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.enhanced_journaling_engine.stage1_input import JournalEntry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Results from analyzing a journal entry."""
    entry_id: str
    themes: List[str]
    characters: List[str]
    locations: List[str]
    main_themes: List[str]
    sentiment_score: float
    sentiment_label: str
    key_events: List[str]
    emotional_arc: str
    narrative_threads: List[str]
    confidence: float


class GeminiAnalyzer:
    """Uses Gemini API to analyze journal entries for themes, characters, and sentiment."""
    
    def __init__(self, api_key: str):
        """Initialize Gemini API client."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Predefined theme categories
        self.theme_categories = [
            "CS Simulation", "Humor", "Spiritual", "Childhood", "Achievement",
            "Personal Growth", "Relationships", "Work", "Health", "Travel",
            "Creativity", "Learning", "Challenges", "Success", "Reflection"
        ]
    
    def analyze_entry(self, entry: JournalEntry) -> AnalysisResult:
        """
        Analyze a single journal entry for themes, characters, and sentiment.
        
        Args:
            entry: JournalEntry object to analyze
            
        Returns:
            AnalysisResult with all analysis data
        """
        logger.info(f"Analyzing entry {entry.entry_id}")
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(entry)
        
        try:
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Parse the response
            analysis_data = self._parse_analysis_response(response.text)
            
            # Create analysis result
            result = AnalysisResult(
                entry_id=entry.entry_id,
                themes=analysis_data.get('themes', []),
                characters=analysis_data.get('characters', []),
                locations=analysis_data.get('locations', []),
                main_themes=analysis_data.get('main_themes', []),
                sentiment_score=analysis_data.get('sentiment_score', 0.0),
                sentiment_label=analysis_data.get('sentiment_label', 'neutral'),
                key_events=analysis_data.get('key_events', []),
                emotional_arc=analysis_data.get('emotional_arc', ''),
                narrative_threads=analysis_data.get('narrative_threads', []),
                confidence=analysis_data.get('confidence', 0.8)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing entry {entry.entry_id}: {e}")
            # Return default analysis result
            return AnalysisResult(
                entry_id=entry.entry_id,
                themes=[],
                characters=[],
                locations=[],
                main_themes=[],
                sentiment_score=0.0,
                sentiment_label='neutral',
                key_events=[],
                emotional_arc='',
                narrative_threads=[],
                confidence=0.0
            )
    
    def _create_analysis_prompt(self, entry: JournalEntry) -> str:
        """Create a detailed prompt for analyzing the journal entry."""
        
        prompt = f"""
You are an expert literary analyst specializing in personal journal analysis. Analyze the following journal entry and provide a comprehensive analysis in JSON format.

JOURNAL ENTRY:
Date: {entry.date.strftime('%B %d, %Y') if entry.date else 'Unknown'}
Color Code: {entry.color_code or 'None'}
Text: {entry.text_content}

ANALYSIS REQUIREMENTS:

1. THEMATIC ANALYSIS:
   - Identify main themes from this list: {', '.join(self.theme_categories)}
   - Suggest any new themes that emerge
   - Rate each theme's prominence (1-10)

2. CHARACTER RECOGNITION:
   - Identify all people mentioned (names, pronouns, relationships)
   - Note their role in the entry
   - Track recurring characters

3. LOCATION IDENTIFICATION:
   - Identify all places mentioned
   - Note their significance to the narrative

4. SENTIMENT ANALYSIS:
   - Provide a sentiment score (-1.0 to 1.0, where -1 is very negative, 1 is very positive)
   - Assign a sentiment label (very_negative, negative, neutral, positive, very_positive)
   - Identify emotional tone and mood

5. NARRATIVE THREADS:
   - Identify ongoing storylines or plot threads
   - Note connections to previous entries (if this is part of a series)
   - Highlight key developments or turning points

6. KEY EVENTS:
   - Extract significant events or moments
   - Note their impact on the narrative

7. EMOTIONAL ARC:
   - Describe the emotional journey within this entry
   - Note any emotional shifts or developments

Please respond with a valid JSON object in this exact format:
{{
    "themes": ["theme1", "theme2"],
    "characters": ["character1", "character2"],
    "locations": ["location1", "location2"],
    "main_themes": ["primary_theme1", "primary_theme2"],
    "sentiment_score": 0.5,
    "sentiment_label": "positive",
    "key_events": ["event1", "event2"],
    "emotional_arc": "description of emotional journey",
    "narrative_threads": ["thread1", "thread2"],
    "confidence": 0.9
}}

Focus on accuracy and provide specific, actionable insights that could be used for enhancing the narrative.
"""
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the Gemini API response into structured data."""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in response")
                return {}
            
            json_str = response_text[json_start:json_end]
            analysis_data = json.loads(json_str)
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return {}


class AnalysisModule:
    """Main analysis module that orchestrates entry analysis."""
    
    def __init__(self, gemini_api_key: str):
        self.gemini_analyzer = GeminiAnalyzer(gemini_api_key)
        self.analysis_results = []
    
    def analyze_entries(self, entries: List[JournalEntry]) -> List[AnalysisResult]:
        """
        Analyze all journal entries for themes, characters, and sentiment.
        
        Args:
            entries: List of JournalEntry objects to analyze
            
        Returns:
            List of AnalysisResult objects
        """
        logger.info(f"Starting analysis of {len(entries)} entries")
        
        results = []
        
        for i, entry in enumerate(entries):
            logger.info(f"Analyzing entry {i+1}/{len(entries)}: {entry.entry_id}")
            
            # Analyze the entry
            result = self.gemini_analyzer.analyze_entry(entry)
            results.append(result)
            
            # Update the original entry with analysis data
            entry.themes = result.themes
            entry.characters = result.characters
            entry.locations = result.locations
            entry.sentiment = result.sentiment_score
        
        self.analysis_results = results
        logger.info(f"Completed analysis of {len(results)} entries")
        
        return results
    
    def generate_theme_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """Generate a summary of all themes found across entries."""
        all_themes = []
        theme_counts = {}
        character_counts = {}
        location_counts = {}
        sentiment_scores = []
        
        for result in results:
            # Collect themes
            all_themes.extend(result.themes)
            for theme in result.themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
            
            # Collect characters
            for character in result.characters:
                character_counts[character] = character_counts.get(character, 0) + 1
            
            # Collect locations
            for location in result.locations:
                location_counts[location] = location_counts.get(location, 0) + 1
            
            # Collect sentiment scores
            sentiment_scores.append(result.sentiment_score)
        
        # Calculate statistics
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        summary = {
            'total_entries': len(results),
            'unique_themes': len(set(all_themes)),
            'theme_frequency': dict(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)),
            'character_frequency': dict(sorted(character_counts.items(), key=lambda x: x[1], reverse=True)),
            'location_frequency': dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)),
            'average_sentiment': avg_sentiment,
            'sentiment_distribution': {
                'very_negative': len([r for r in results if r.sentiment_label == 'very_negative']),
                'negative': len([r for r in results if r.sentiment_label == 'negative']),
                'neutral': len([r for r in results if r.sentiment_label == 'neutral']),
                'positive': len([r for r in results if r.sentiment_label == 'positive']),
                'very_positive': len([r for r in results if r.sentiment_label == 'very_positive'])
            }
        }
        
        return summary
    
    def identify_narrative_threads(self, results: List[AnalysisResult]) -> List[Dict[str, Any]]:
        """Identify and track narrative threads across multiple entries."""
        thread_tracker = {}
        
        for result in results:
            for thread in result.narrative_threads:
                if thread not in thread_tracker:
                    thread_tracker[thread] = {
                        'name': thread,
                        'entries': [],
                        'themes': set(),
                        'characters': set(),
                        'sentiment_arc': []
                    }
                
                # Add entry to thread
                thread_tracker[thread]['entries'].append(result.entry_id)
                thread_tracker[thread]['themes'].update(result.themes)
                thread_tracker[thread]['characters'].update(result.characters)
                thread_tracker[thread]['sentiment_arc'].append(result.sentiment_score)
        
        # Convert sets to lists for JSON serialization
        threads = []
        for thread_name, thread_data in thread_tracker.items():
            threads.append({
                'name': thread_name,
                'entries': thread_data['entries'],
                'themes': list(thread_data['themes']),
                'characters': list(thread_data['characters']),
                'sentiment_arc': thread_data['sentiment_arc'],
                'entry_count': len(thread_data['entries'])
            })
        
        # Sort by entry count (most prominent threads first)
        threads.sort(key=lambda x: x['entry_count'], reverse=True)
        
        return threads
    
    def save_analysis_results(self, results: List[AnalysisResult], output_path: str):
        """Save analysis results to JSON file."""
        # Convert results to serializable format
        serializable_results = []
        for result in results:
            result_dict = asdict(result)
            serializable_results.append(result_dict)
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Saved {len(results)} analysis results to {output_path}")
    
    def save_analysis_summary(self, summary: Dict[str, Any], threads: List[Dict[str, Any]], 
                            output_path: str):
        """Save analysis summary and narrative threads to JSON file."""
        summary_data = {
            'summary': summary,
            'narrative_threads': threads,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Saved analysis summary to {output_path}")


def main():
    """Example usage of the Analysis Module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze journal entries for themes and sentiment')
    parser.add_argument('--input_file', required=True, help='JSON file with journal entries')
    parser.add_argument('--output_file', required=True, help='Output JSON file for analysis results')
    parser.add_argument('--summary_file', required=True, help='Output JSON file for analysis summary')
    parser.add_argument('--gemini_api_key', required=True, help='Gemini API key')
    
    args = parser.parse_args()
    
    # Load entries
    with open(args.input_file, 'r') as f:
        entries_data = json.load(f)
    
    # Convert back to JournalEntry objects
    entries = []
    for entry_data in entries_data:
        entry = JournalEntry(
            entry_id=entry_data['entry_id'],
            date=datetime.fromisoformat(entry_data['date']) if entry_data['date'] else None,
            color_code=entry_data['color_code'],
            text_content=entry_data['text_content'],
            page_number=entry_data['page_number'],
            confidence=entry_data['confidence'],
            original_image_path=entry_data['original_image_path']
        )
        entries.append(entry)
    
    # Initialize analysis module
    analysis_module = AnalysisModule(args.gemini_api_key)
    
    # Analyze entries
    results = analysis_module.analyze_entries(entries)
    
    # Generate summary and threads
    summary = analysis_module.generate_theme_summary(results)
    threads = analysis_module.identify_narrative_threads(results)
    
    # Save results
    analysis_module.save_analysis_results(results, args.output_file)
    analysis_module.save_analysis_summary(summary, threads, args.summary_file)
    
    print(f"✅ Analyzed {len(entries)} journal entries")
    print(f"📊 Found {len(summary['theme_frequency'])} unique themes")
    print(f"🧵 Identified {len(threads)} narrative threads")
    print(f"📁 Results saved to: {args.output_file}")
    print(f"📋 Summary saved to: {args.summary_file}")


if __name__ == "__main__":
    main()
