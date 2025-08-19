#!/usr/bin/env python3
"""
Stage 4: The Output & Formatting Module

This module compiles enhanced entries into a single, beautiful, and consistent document
for publication. Includes chronological assembly, color-coding, and multiple output formats.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import jinja2
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.enhanced_journaling_engine.stage1_input import JournalEntry
from src.enhanced_journaling_engine.stage3_enhancement import EnhancedEntry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PublicationConfig:
    """Configuration for document publication."""
    title: str
    author: str
    subtitle: Optional[str] = None
    include_original: bool = True
    include_analysis: bool = True
    color_coding: bool = True
    theme_organization: bool = True
    page_numbers: bool = True
    table_of_contents: bool = True
    include_metadata: bool = True


class DocumentFormatter:
    """Formats journal entries into various publication formats."""
    
    def __init__(self, config: PublicationConfig):
        self.config = config
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates'),
            autoescape=True
        )
    
    def format_markdown(self, entries: List[EnhancedEntry], 
                       analysis_summary: Dict[str, Any] = None) -> str:
        """Format entries as Markdown document."""
        markdown_content = []
        
        # Title and metadata
        markdown_content.append(f"# {self.config.title}")
        if self.config.subtitle:
            markdown_content.append(f"*{self.config.subtitle}*")
        markdown_content.append(f"**By {self.config.author}**")
        markdown_content.append(f"*Generated on {datetime.now().strftime('%B %d, %Y')}*")
        markdown_content.append("")
        
        # Table of contents
        if self.config.table_of_contents:
            markdown_content.append("## Table of Contents")
            markdown_content.append("")
            for i, entry in enumerate(entries, 1):
                date_str = entry.original_text.split()[0] if entry.original_text else f"Entry {i}"
                markdown_content.append(f"{i}. [{date_str}](#entry-{i})")
            markdown_content.append("")
        
        # Analysis summary
        if self.config.include_analysis and analysis_summary:
            markdown_content.append("## Analysis Summary")
            markdown_content.append("")
            
            summary = analysis_summary.get('summary', {})
            markdown_content.append(f"- **Total Entries**: {summary.get('total_entries', 0)}")
            markdown_content.append(f"- **Unique Themes**: {summary.get('unique_themes', 0)}")
            markdown_content.append(f"- **Average Sentiment**: {summary.get('average_sentiment', 0):.2f}")
            markdown_content.append("")
            
            # Top themes
            theme_freq = summary.get('theme_frequency', {})
            if theme_freq:
                markdown_content.append("### Top Themes")
                for theme, count in list(theme_freq.items())[:5]:
                    markdown_content.append(f"- {theme}: {count} mentions")
                markdown_content.append("")
        
        # Entries
        markdown_content.append("## Journal Entries")
        markdown_content.append("")
        
        for i, entry in enumerate(entries, 1):
            # Entry header
            date_str = entry.original_text.split()[0] if entry.original_text else f"Entry {i}"
            markdown_content.append(f"### {date_str} {{#entry-{i}}}")
            
            # Color coding
            if self.config.color_coding and hasattr(entry, 'color_code') and entry.color_code:
                markdown_content.append(f"*Color: {entry.color_code}*")
            
            # Enhanced text
            markdown_content.append("")
            markdown_content.append(entry.enhanced_text)
            markdown_content.append("")
            
            # Original text (if requested)
            if self.config.include_original:
                markdown_content.append("**Original Text:**")
                markdown_content.append(f"> {entry.original_text}")
                markdown_content.append("")
            
            # Analysis metadata (if requested)
            if self.config.include_analysis:
                if entry.themes_enhanced:
                    markdown_content.append(f"**Themes:** {', '.join(entry.themes_enhanced)}")
                if entry.characters_enhanced:
                    markdown_content.append(f"**Characters:** {', '.join(entry.characters_enhanced)}")
                if entry.locations_enhanced:
                    markdown_content.append(f"**Locations:** {', '.join(entry.locations_enhanced)}")
                markdown_content.append("")
            
            markdown_content.append("---")
            markdown_content.append("")
        
        return "\n".join(markdown_content)
    
    def format_html(self, entries: List[EnhancedEntry], 
                   analysis_summary: Dict[str, Any] = None) -> str:
        """Format entries as HTML document."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Georgia', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #2c3e50;
            margin-top: 30px;
        }
        .entry {
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #bdc3c7;
            background-color: #f8f9fa;
        }
        .entry-header {
            font-weight: bold;
            color: #7f8c8d;
            margin-bottom: 10px;
        }
        .color-indicator {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid #333;
        }
        .original-text {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            font-style: italic;
        }
        .metadata {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 10px;
        }
        .toc {
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .toc a {
            color: #3498db;
            text-decoration: none;
        }
        .toc a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        {% if subtitle %}
        <p style="text-align: center; font-style: italic; color: #7f8c8d;">{{ subtitle }}</p>
        {% endif %}
        <p style="text-align: center; font-weight: bold;">By {{ author }}</p>
        <p style="text-align: center; color: #7f8c8d;">Generated on {{ generated_date }}</p>
        
        {% if table_of_contents %}
        <div class="toc">
            <h2>Table of Contents</h2>
            <ol>
            {% for entry in entries %}
                <li><a href="#entry-{{ loop.index }}">{{ entry.original_text.split()[0] if entry.original_text else 'Entry ' + loop.index|string }}</a></li>
            {% endfor %}
            </ol>
        </div>
        {% endif %}
        
        {% if include_analysis and analysis_summary %}
        <h2>Analysis Summary</h2>
        <p><strong>Total Entries:</strong> {{ analysis_summary.summary.total_entries }}</p>
        <p><strong>Unique Themes:</strong> {{ analysis_summary.summary.unique_themes }}</p>
        <p><strong>Average Sentiment:</strong> {{ "%.2f"|format(analysis_summary.summary.average_sentiment) }}</p>
        
        {% if analysis_summary.summary.theme_frequency %}
        <h3>Top Themes</h3>
        <ul>
        {% for theme, count in analysis_summary.summary.theme_frequency.items()[:5] %}
            <li>{{ theme }}: {{ count }} mentions</li>
        {% endfor %}
        </ul>
        {% endif %}
        {% endif %}
        
        <h2>Journal Entries</h2>
        
        {% for entry in entries %}
        <div class="entry" id="entry-{{ loop.index }}">
            <div class="entry-header">
                {% if color_coding and entry.color_code %}
                <span class="color-indicator" style="background-color: {{ entry.color_code }};"></span>
                {% endif %}
                {{ entry.original_text.split()[0] if entry.original_text else 'Entry ' + loop.index|string }}
            </div>
            
            <div class="enhanced-text">
                {{ entry.enhanced_text | replace('\n', '<br>') | safe }}
            </div>
            
            {% if include_original %}
            <div class="original-text">
                <strong>Original Text:</strong><br>
                {{ entry.original_text }}
            </div>
            {% endif %}
            
            {% if include_analysis %}
            <div class="metadata">
                {% if entry.themes_enhanced %}
                <strong>Themes:</strong> {{ entry.themes_enhanced | join(', ') }}<br>
                {% endif %}
                {% if entry.characters_enhanced %}
                <strong>Characters:</strong> {{ entry.characters_enhanced | join(', ') }}<br>
                {% endif %}
                {% if entry.locations_enhanced %}
                <strong>Locations:</strong> {{ entry.locations_enhanced | join(', ') }}
                {% endif %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""
        
        template = jinja2.Template(html_template)
        return template.render(
            title=self.config.title,
            subtitle=self.config.subtitle,
            author=self.config.author,
            generated_date=datetime.now().strftime('%B %d, %Y'),
            entries=entries,
            analysis_summary=analysis_summary,
            table_of_contents=self.config.table_of_contents,
            include_analysis=self.config.include_analysis,
            include_original=self.config.include_original,
            color_coding=self.config.color_coding
        )
    
    def format_json(self, entries: List[EnhancedEntry], 
                   analysis_summary: Dict[str, Any] = None) -> str:
        """Format entries as structured JSON document."""
        document = {
            'metadata': {
                'title': self.config.title,
                'author': self.config.author,
                'subtitle': self.config.subtitle,
                'generated_at': datetime.now().isoformat(),
                'total_entries': len(entries),
                'config': asdict(self.config)
            },
            'analysis_summary': analysis_summary,
            'entries': []
        }
        
        for entry in entries:
            entry_data = {
                'entry_id': entry.entry_id,
                'enhanced_text': entry.enhanced_text,
                'original_text': entry.original_text if self.config.include_original else None,
                'enhancement_prompt': entry.enhancement_prompt,
                'enhancement_notes': entry.enhancement_notes,
                'themes': entry.themes_enhanced,
                'characters': entry.characters_enhanced,
                'locations': entry.locations_enhanced,
                'created_at': entry.created_at.isoformat()
            }
            document['entries'].append(entry_data)
        
        return json.dumps(document, indent=2)


class OutputModule:
    """Main output module that orchestrates document generation."""
    
    def __init__(self, config: PublicationConfig):
        self.config = config
        self.formatter = DocumentFormatter(config)
    
    def generate_document(self, entries: List[EnhancedEntry], 
                         analysis_summary: Dict[str, Any] = None,
                         output_formats: List[str] = None) -> Dict[str, str]:
        """
        Generate documents in multiple formats.
        
        Args:
            entries: List of enhanced entries
            analysis_summary: Analysis summary data
            output_formats: List of formats to generate ('markdown', 'html', 'json')
            
        Returns:
            Dictionary mapping format to generated content
        """
        if output_formats is None:
            output_formats = ['markdown', 'html']
        
        # Sort entries chronologically
        sorted_entries = self._sort_entries_chronologically(entries)
        
        documents = {}
        
        for format_type in output_formats:
            logger.info(f"Generating {format_type} document")
            
            if format_type == 'markdown':
                content = self.formatter.format_markdown(sorted_entries, analysis_summary)
            elif format_type == 'html':
                content = self.formatter.format_html(sorted_entries, analysis_summary)
            elif format_type == 'json':
                content = self.formatter.format_json(sorted_entries, analysis_summary)
            else:
                logger.warning(f"Unknown format: {format_type}")
                continue
            
            documents[format_type] = content
        
        return documents
    
    def _sort_entries_chronologically(self, entries: List[EnhancedEntry]) -> List[EnhancedEntry]:
        """Sort entries by date, with fallback to entry order."""
        def get_entry_date(entry):
            # Try to extract date from original text
            words = entry.original_text.split()
            if words:
                # Simple date extraction - could be enhanced
                return words[0]
            return entry.entry_id
        
        return sorted(entries, key=get_entry_date)
    
    def save_documents(self, documents: Dict[str, str], output_dir: str):
        """Save generated documents to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        for format_type, content in documents.items():
            if format_type == 'markdown':
                filename = f"{self.config.title.lower().replace(' ', '_')}.md"
            elif format_type == 'html':
                filename = f"{self.config.title.lower().replace(' ', '_')}.html"
            elif format_type == 'json':
                filename = f"{self.config.title.lower().replace(' ', '_')}.json"
            else:
                continue
            
            file_path = output_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files.append(str(file_path))
            logger.info(f"Saved {format_type} document to: {file_path}")
        
        return saved_files
    
    def generate_publication_report(self, entries: List[EnhancedEntry], 
                                  analysis_summary: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a comprehensive publication report."""
        total_words = sum(len(entry.enhanced_text.split()) for entry in entries)
        total_original_words = sum(len(entry.original_text.split()) for entry in entries)
        
        # Theme distribution
        all_themes = []
        for entry in entries:
            all_themes.extend(entry.themes_enhanced)
        
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Character distribution
        all_characters = []
        for entry in entries:
            all_characters.extend(entry.characters_enhanced)
        
        character_counts = {}
        for character in all_characters:
            character_counts[character] = character_counts.get(character, 0) + 1
        
        report = {
            'publication_info': {
                'title': self.config.title,
                'author': self.config.author,
                'generated_at': datetime.now().isoformat(),
                'total_entries': len(entries),
                'total_words': total_words,
                'total_original_words': total_original_words,
                'enhancement_ratio': total_words / total_original_words if total_original_words > 0 else 1.0
            },
            'theme_analysis': {
                'unique_themes': len(set(all_themes)),
                'theme_frequency': dict(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True))
            },
            'character_analysis': {
                'unique_characters': len(set(all_characters)),
                'character_frequency': dict(sorted(character_counts.items(), key=lambda x: x[1], reverse=True))
            },
            'analysis_summary': analysis_summary
        }
        
        return report


def main():
    """Example usage of the Output Module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate publication documents from enhanced entries')
    parser.add_argument('--enhanced_entries_file', required=True, help='JSON file with enhanced entries')
    parser.add_argument('--analysis_summary_file', help='JSON file with analysis summary')
    parser.add_argument('--output_dir', required=True, help='Output directory for documents')
    parser.add_argument('--title', required=True, help='Document title')
    parser.add_argument('--author', required=True, help='Document author')
    parser.add_argument('--subtitle', help='Document subtitle')
    parser.add_argument('--formats', nargs='+', default=['markdown', 'html'], 
                       choices=['markdown', 'html', 'json'],
                       help='Output formats to generate')
    
    args = parser.parse_args()
    
    # Load enhanced entries
    with open(args.enhanced_entries_file, 'r') as f:
        entries_data = json.load(f)
    
    # Convert back to EnhancedEntry objects
    entries = []
    for entry_data in entries_data:
        entry = EnhancedEntry(
            entry_id=entry_data['entry_id'],
            original_text=entry_data['original_text'],
            enhanced_text=entry_data['enhanced_text'],
            enhancement_prompt=entry_data['enhancement_prompt'],
            enhancement_notes=entry_data['enhancement_notes'],
            confidence=entry_data['confidence'],
            themes_enhanced=entry_data['themes_enhanced'],
            characters_enhanced=entry_data['characters_enhanced'],
            locations_enhanced=entry_data['locations_enhanced'],
            created_at=datetime.fromisoformat(entry_data['created_at'])
        )
        entries.append(entry)
    
    # Load analysis summary if provided
    analysis_summary = None
    if args.analysis_summary_file:
        with open(args.analysis_summary_file, 'r') as f:
            analysis_summary = json.load(f)
    
    # Create publication config
    config = PublicationConfig(
        title=args.title,
        author=args.author,
        subtitle=args.subtitle
    )
    
    # Initialize output module
    output_module = OutputModule(config)
    
    # Generate documents
    documents = output_module.generate_document(entries, analysis_summary, args.formats)
    
    # Save documents
    saved_files = output_module.save_documents(documents, args.output_dir)
    
    # Generate publication report
    report = output_module.generate_publication_report(entries, analysis_summary)
    
    # Save report
    report_path = Path(args.output_dir) / 'publication_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Generated documents in {len(args.formats)} formats")
    print(f"📄 Saved files:")
    for file_path in saved_files:
        print(f"   - {file_path}")
    print(f"📋 Publication report saved to: {report_path}")
    print(f"📊 Document stats: {report['publication_info']['total_entries']} entries, "
          f"{report['publication_info']['total_words']} words")


if __name__ == "__main__":
    main()
