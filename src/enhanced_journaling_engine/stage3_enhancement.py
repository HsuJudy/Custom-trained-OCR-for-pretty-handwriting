#!/usr/bin/env python3
"""
Stage 3: The Enhancement Module (The "Magic")

This module transforms raw journal text into rich, narrative-driven stories while preserving
the original journal format. Uses Gemini API for creative enhancement with user guidance.
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
from src.enhanced_journaling_engine.stage2_analysis import AnalysisResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EnhancementRequest:
    """User's enhancement request for a journal entry."""
    entry_id: str
    enhancement_prompt: str
    focus_areas: List[str]  # e.g., ["sensory_details", "character_arc", "plot_development"]
    style_preferences: Dict[str, Any]  # e.g., {"tone": "reflective", "pacing": "slow"}
    preserve_original: bool = True


@dataclass
class EnhancedEntry:
    """Enhanced version of a journal entry."""
    entry_id: str
    original_text: str
    enhanced_text: str
    enhancement_prompt: str
    enhancement_notes: str
    confidence: float
    themes_enhanced: List[str]
    characters_enhanced: List[str]
    locations_enhanced: List[str]
    created_at: datetime


class EnhancementEngine:
    """Uses Gemini API to enhance journal entries with creative writing."""
    
    def __init__(self, api_key: str):
        """Initialize Gemini API client for enhancement."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Enhancement templates
        self.enhancement_templates = {
            'sensory_details': "Add vivid sensory details including sights, sounds, smells, tastes, and textures",
            'character_arc': "Expand on character development and emotional growth",
            'plot_development': "Develop the narrative arc and build tension",
            'dialogue': "Add realistic dialogue and conversations",
            'setting': "Enhance the setting description and atmosphere",
            'emotional_depth': "Deepen the emotional resonance and introspection",
            'foreshadowing': "Add subtle hints about future events",
            'reflection': "Include deeper personal insights and reflections"
        }
    
    def enhance_entry(self, entry: JournalEntry, analysis: AnalysisResult, 
                     request: EnhancementRequest) -> EnhancedEntry:
        """
        Enhance a journal entry based on user request and analysis.
        
        Args:
            entry: Original journal entry
            analysis: Analysis results for the entry
            request: User's enhancement request
            
        Returns:
            EnhancedEntry with the enhanced text
        """
        logger.info(f"Enhancing entry {entry.entry_id}")
        
        # Create enhancement prompt
        prompt = self._create_enhancement_prompt(entry, analysis, request)
        
        try:
            # Get enhanced text from Gemini
            response = self.model.generate_content(prompt)
            enhanced_text = response.text.strip()
            
            # Create enhancement notes
            enhancement_notes = self._generate_enhancement_notes(entry, enhanced_text, request)
            
            # Create enhanced entry
            enhanced_entry = EnhancedEntry(
                entry_id=entry.entry_id,
                original_text=entry.text_content,
                enhanced_text=enhanced_text,
                enhancement_prompt=request.enhancement_prompt,
                enhancement_notes=enhancement_notes,
                confidence=0.9,  # High confidence for creative enhancement
                themes_enhanced=analysis.themes,
                characters_enhanced=analysis.characters,
                locations_enhanced=analysis.locations,
                created_at=datetime.now()
            )
            
            return enhanced_entry
            
        except Exception as e:
            logger.error(f"Error enhancing entry {entry.entry_id}: {e}")
            # Return original text as fallback
            return EnhancedEntry(
                entry_id=entry.entry_id,
                original_text=entry.text_content,
                enhanced_text=entry.text_content,  # No enhancement
                enhancement_prompt=request.enhancement_prompt,
                enhancement_notes=f"Enhancement failed: {str(e)}",
                confidence=0.0,
                themes_enhanced=[],
                characters_enhanced=[],
                locations_enhanced=[],
                created_at=datetime.now()
            )
    
    def _create_enhancement_prompt(self, entry: JournalEntry, analysis: AnalysisResult, 
                                 request: EnhancementRequest) -> str:
        """Create a detailed prompt for enhancing the journal entry."""
        
        # Build focus area instructions
        focus_instructions = []
        for area in request.focus_areas:
            if area in self.enhancement_templates:
                focus_instructions.append(self.enhancement_templates[area])
            else:
                focus_instructions.append(f"Focus on: {area}")
        
        focus_text = "\n".join([f"- {instruction}" for instruction in focus_instructions])
        
        # Build style preferences
        style_text = ""
        if request.style_preferences:
            style_parts = []
            for key, value in request.style_preferences.items():
                style_parts.append(f"{key}: {value}")
            style_text = f"\nStyle Preferences:\n" + "\n".join([f"- {part}" for part in style_parts])
        
        prompt = f"""
You are an expert creative writer specializing in enhancing personal journal entries. Your task is to transform the raw journal text into a rich, narrative-driven story while preserving the authentic voice and emotional truth of the original.

ORIGINAL JOURNAL ENTRY:
Date: {entry.date.strftime('%B %d, %Y') if entry.date else 'Unknown'}
Color Code: {entry.color_code or 'None'}
Text: {entry.text_content}

ANALYSIS CONTEXT:
Themes: {', '.join(analysis.themes)}
Characters: {', '.join(analysis.characters)}
Locations: {', '.join(analysis.locations)}
Sentiment: {analysis.sentiment_label} (score: {analysis.sentiment_score})
Narrative Threads: {', '.join(analysis.narrative_threads)}
Emotional Arc: {analysis.emotional_arc}

USER ENHANCEMENT REQUEST:
{request.enhancement_prompt}

FOCUS AREAS:
{focus_text}{style_text}

ENHANCEMENT GUIDELINES:

1. PRESERVE AUTHENTICITY: Maintain the original voice and emotional truth
2. ENHANCE NARRATIVE: Add depth, detail, and flow without changing core meaning
3. RESPECT CONTEXT: Use the analysis to inform your enhancements
4. MAINTAIN STRUCTURE: Keep the diary/journal format
5. ADD DEPTH: Expand on themes, characters, and emotional resonance
6. IMPROVE FLOW: Make the text more engaging and readable
7. CONSISTENCY: Ensure enhancements align with the identified themes and threads

IMPORTANT CONSTRAINTS:
- Do not change the fundamental meaning or facts
- Preserve the personal, intimate tone
- Keep the chronological structure
- Maintain the color coding significance
- Respect the original sentiment and emotional arc

Please provide the enhanced version of the journal entry. Make it more vivid, engaging, and narrative-rich while staying true to the original voice and meaning.
"""
        return prompt
    
    def _generate_enhancement_notes(self, entry: JournalEntry, enhanced_text: str, 
                                  request: EnhancementRequest) -> str:
        """Generate notes about what was enhanced."""
        original_length = len(entry.text_content.split())
        enhanced_length = len(enhanced_text.split())
        
        notes = f"""
Enhancement Summary:
- Original length: {original_length} words
- Enhanced length: {enhanced_length} words
- Focus areas: {', '.join(request.focus_areas)}
- Style preferences: {request.style_preferences}
- Enhancement applied: {enhanced_length - original_length} words added
"""
        return notes.strip()


class EnhancementModule:
    """Main enhancement module that orchestrates entry enhancement."""
    
    def __init__(self, gemini_api_key: str):
        self.enhancement_engine = EnhancementEngine(gemini_api_key)
        self.enhanced_entries = []
    
    def enhance_entries(self, entries: List[JournalEntry], analyses: List[AnalysisResult],
                       requests: List[EnhancementRequest]) -> List[EnhancedEntry]:
        """
        Enhance multiple journal entries based on user requests.
        
        Args:
            entries: List of original journal entries
            analyses: List of analysis results for each entry
            requests: List of enhancement requests
            
        Returns:
            List of EnhancedEntry objects
        """
        logger.info(f"Starting enhancement of {len(entries)} entries")
        
        # Create lookup dictionaries
        entry_lookup = {entry.entry_id: entry for entry in entries}
        analysis_lookup = {analysis.entry_id: analysis for analysis in analyses}
        request_lookup = {request.entry_id: request for request in requests}
        
        enhanced_entries = []
        
        for entry in entries:
            entry_id = entry.entry_id
            
            # Get corresponding analysis and request
            analysis = analysis_lookup.get(entry_id)
            request = request_lookup.get(entry_id)
            
            if not analysis:
                logger.warning(f"No analysis found for entry {entry_id}")
                continue
            
            if not request:
                logger.warning(f"No enhancement request found for entry {entry_id}")
                continue
            
            # Enhance the entry
            enhanced_entry = self.enhancement_engine.enhance_entry(entry, analysis, request)
            enhanced_entries.append(enhanced_entry)
            
            # Update the original entry
            entry.enhanced_text = enhanced_entry.enhanced_text
        
        self.enhanced_entries = enhanced_entries
        logger.info(f"Completed enhancement of {len(enhanced_entries)} entries")
        
        return enhanced_entries
    
    def create_enhancement_request(self, entry_id: str, prompt: str, 
                                 focus_areas: List[str] = None,
                                 style_preferences: Dict[str, Any] = None) -> EnhancementRequest:
        """Create an enhancement request for a specific entry."""
        if focus_areas is None:
            focus_areas = ['sensory_details', 'emotional_depth']
        
        if style_preferences is None:
            style_preferences = {
                'tone': 'reflective',
                'pacing': 'natural',
                'voice': 'authentic'
            }
        
        return EnhancementRequest(
            entry_id=entry_id,
            enhancement_prompt=prompt,
            focus_areas=focus_areas,
            style_preferences=style_preferences
        )
    
    def batch_enhance(self, entries: List[JournalEntry], analyses: List[AnalysisResult],
                     enhancement_strategy: str = 'default') -> List[EnhancedEntry]:
        """
        Apply batch enhancement using predefined strategies.
        
        Args:
            entries: List of journal entries
            analyses: List of analysis results
            enhancement_strategy: Strategy to apply ('default', 'minimal', 'extensive')
            
        Returns:
            List of enhanced entries
        """
        strategies = {
            'default': {
                'focus_areas': ['sensory_details', 'emotional_depth'],
                'style_preferences': {'tone': 'reflective', 'pacing': 'natural'}
            },
            'minimal': {
                'focus_areas': ['flow', 'clarity'],
                'style_preferences': {'tone': 'preserved', 'pacing': 'original'}
            },
            'extensive': {
                'focus_areas': ['sensory_details', 'character_arc', 'plot_development', 'dialogue'],
                'style_preferences': {'tone': 'narrative', 'pacing': 'engaging'}
            }
        }
        
        strategy = strategies.get(enhancement_strategy, strategies['default'])
        
        # Create requests for all entries
        requests = []
        for entry in entries:
            request = EnhancementRequest(
                entry_id=entry.entry_id,
                enhancement_prompt=f"Enhance this journal entry using the {enhancement_strategy} strategy",
                focus_areas=strategy['focus_areas'],
                style_preferences=strategy['style_preferences']
            )
            requests.append(request)
        
        return self.enhance_entries(entries, analyses, requests)
    
    def save_enhanced_entries(self, enhanced_entries: List[EnhancedEntry], output_path: str):
        """Save enhanced entries to JSON file."""
        # Convert to serializable format
        serializable_entries = []
        for entry in enhanced_entries:
            entry_dict = asdict(entry)
            # Convert datetime to string
            entry_dict['created_at'] = entry.created_at.isoformat()
            serializable_entries.append(entry_dict)
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(serializable_entries, f, indent=2)
        
        logger.info(f"Saved {len(enhanced_entries)} enhanced entries to {output_path}")
    
    def generate_enhancement_report(self, enhanced_entries: List[EnhancedEntry]) -> Dict[str, Any]:
        """Generate a report on the enhancement process."""
        total_original_words = sum(len(entry.original_text.split()) for entry in enhanced_entries)
        total_enhanced_words = sum(len(entry.enhanced_text.split()) for entry in enhanced_entries)
        
        enhancement_stats = []
        for entry in enhanced_entries:
            original_words = len(entry.original_text.split())
            enhanced_words = len(entry.enhanced_text.split())
            enhancement_stats.append({
                'entry_id': entry.entry_id,
                'original_words': original_words,
                'enhanced_words': enhanced_words,
                'words_added': enhanced_words - original_words,
                'enhancement_ratio': enhanced_words / original_words if original_words > 0 else 1.0
            })
        
        report = {
            'total_entries': len(enhanced_entries),
            'total_original_words': total_original_words,
            'total_enhanced_words': total_enhanced_words,
            'total_words_added': total_enhanced_words - total_original_words,
            'average_enhancement_ratio': total_enhanced_words / total_original_words if total_original_words > 0 else 1.0,
            'entry_stats': enhancement_stats,
            'generated_at': datetime.now().isoformat()
        }
        
        return report


def main():
    """Example usage of the Enhancement Module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhance journal entries with creative writing')
    parser.add_argument('--entries_file', required=True, help='JSON file with journal entries')
    parser.add_argument('--analysis_file', required=True, help='JSON file with analysis results')
    parser.add_argument('--output_file', required=True, help='Output JSON file for enhanced entries')
    parser.add_argument('--report_file', required=True, help='Output JSON file for enhancement report')
    parser.add_argument('--gemini_api_key', required=True, help='Gemini API key')
    parser.add_argument('--strategy', default='default', 
                       choices=['default', 'minimal', 'extensive'],
                       help='Enhancement strategy to apply')
    
    args = parser.parse_args()
    
    # Load entries
    with open(args.entries_file, 'r') as f:
        entries_data = json.load(f)
    
    # Load analyses
    with open(args.analysis_file, 'r') as f:
        analyses_data = json.load(f)
    
    # Convert back to objects
    from src.enhanced_journaling_engine.stage1_input import JournalEntry
    from src.enhanced_journaling_engine.stage2_analysis import AnalysisResult
    
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
    
    analyses = []
    for analysis_data in analyses_data:
        analysis = AnalysisResult(
            entry_id=analysis_data['entry_id'],
            themes=analysis_data['themes'],
            characters=analysis_data['characters'],
            locations=analysis_data['locations'],
            main_themes=analysis_data['main_themes'],
            sentiment_score=analysis_data['sentiment_score'],
            sentiment_label=analysis_data['sentiment_label'],
            key_events=analysis_data['key_events'],
            emotional_arc=analysis_data['emotional_arc'],
            narrative_threads=analysis_data['narrative_threads'],
            confidence=analysis_data['confidence']
        )
        analyses.append(analysis)
    
    # Initialize enhancement module
    enhancement_module = EnhancementModule(args.gemini_api_key)
    
    # Apply batch enhancement
    enhanced_entries = enhancement_module.batch_enhance(entries, analyses, args.strategy)
    
    # Generate report
    report = enhancement_module.generate_enhancement_report(enhanced_entries)
    
    # Save results
    enhancement_module.save_enhanced_entries(enhanced_entries, args.output_file)
    
    with open(args.report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Enhanced {len(entries)} journal entries")
    print(f"📈 Added {report['total_words_added']} words ({report['average_enhancement_ratio']:.1f}x enhancement)")
    print(f"📁 Enhanced entries saved to: {args.output_file}")
    print(f"📋 Enhancement report saved to: {args.report_file}")


if __name__ == "__main__":
    main()
