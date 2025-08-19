# Enhanced Journaling Engine

Transform your handwritten journals into enhanced, published editions using AI-powered analysis and creative enhancement.

## 🎯 System Overview

The Enhanced Journaling Engine is a modular system that transforms raw handwritten journal pages into rich, narrative-driven stories while preserving the authentic voice and emotional truth of your original entries.

### The Four-Stage Pipeline

```
📸 Input → 🧠 Analysis → ✨ Enhancement → 📄 Output
```

## 🏗️ System Architecture

### Stage 1: Input Module (OCR & Metadata Capture)
- **Custom OCR Model**: Transcribes your handwriting with high accuracy
- **Timestamp/Date Recognition**: Automatically extracts dates from entries
- **Color-Coded Sticker Detection**: Identifies and tracks color-coded themes
- **Metadata Extraction**: Captures page numbers, confidence scores, and positioning

### Stage 2: Analysis Module (Thread Identification)
- **Thematic Tagging**: Uses Gemini API to identify narrative themes
- **Character Recognition**: Tracks recurring characters and relationships
- **Sentiment Analysis**: Analyzes emotional tone and journey
- **Narrative Thread Tracking**: Identifies ongoing storylines across entries

### Stage 3: Enhancement Module (The "Magic")
- **Creative Enhancement**: Transforms raw text into rich narratives
- **User-Guided Prompts**: Customizable enhancement strategies
- **Original Text Preservation**: Maintains authenticity while adding depth
- **Style Consistency**: Ensures coherent voice throughout

### Stage 4: Output Module (Document Generation)
- **Chronological Assembly**: Orders entries by date
- **Color-Coding Application**: Visual theme organization
- **Multiple Formats**: Markdown, HTML, and JSON output
- **Publication-Ready**: Beautiful, formatted documents

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Gemini API key
- Journal page images (JPG, PNG, PDF)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up your Gemini API key
export GEMINI_API_KEY="your_api_key_here"
```

### Basic Usage
```bash
# Run the complete pipeline
python src/enhanced_journaling_engine/main.py \
  --input_dir journal_pages/ \
  --gemini_api_key YOUR_API_KEY \
  --title "My Enhanced Journal" \
  --author "Your Name"
```

### Advanced Usage
```bash
# Run with custom enhancement strategy
python src/enhanced_journaling_engine/main.py \
  --input_dir journal_pages/ \
  --gemini_api_key YOUR_API_KEY \
  --title "My Journal" \
  --author "Your Name" \
  --enhancement_strategy extensive \
  --output_formats markdown html json

# Run single stage
python src/enhanced_journaling_engine/main.py \
  --input_dir journal_pages/ \
  --gemini_api_key YOUR_API_KEY \
  --stage input
```

## 📁 Input Requirements

### Supported Formats
- **Images**: JPG, JPEG, PNG, TIFF, BMP
- **Documents**: PDF (automatically converted to images)
- **Organization**: Files in chronological order

### Color-Coded Stickers
The system automatically detects and tracks color-coded stickers:
- **Red**: Urgent/Important themes
- **Blue**: Work/Professional content
- **Green**: Personal growth/Health
- **Yellow**: Creative/Inspiration
- **Purple**: Spiritual/Reflection
- **Orange**: Relationships/Social

### Date Recognition
Automatically recognizes dates in various formats:
- `January 15, 2025`
- `Jan 15, 2025`
- `15/01/2025`
- `15-01-2025`
- `15.01.2025`

## 🎨 Enhancement Strategies

### Default Strategy
- Adds sensory details and emotional depth
- Maintains authentic voice
- Natural pacing and flow

### Minimal Strategy
- Preserves original structure
- Minimal text changes
- Focus on clarity and flow

### Extensive Strategy
- Rich narrative development
- Character arc expansion
- Dialogue and plot development
- Maximum creative enhancement

## 📊 Output Formats

### Markdown
- Clean, readable format
- Perfect for further editing
- GitHub-compatible

### HTML
- Beautiful web-ready documents
- Color-coded entries
- Responsive design
- Interactive table of contents

### JSON
- Structured data format
- Perfect for further processing
- Complete metadata included

## 🔧 Configuration Options

### Publication Settings
```bash
--title "My Journal"              # Document title
--author "Your Name"              # Author name
--subtitle "A Journey Through..." # Optional subtitle
--output_dir "output/"            # Output directory
```

### Enhancement Options
```bash
--enhancement_strategy default    # default/minimal/extensive
--include_original true           # Include original text
--include_analysis true           # Include analysis metadata
--color_coding true               # Apply color coding
--theme_organization true         # Organize by themes
```

### Output Options
```bash
--output_formats markdown html    # Output formats
--table_of_contents true          # Include TOC
--page_numbers true               # Include page numbers
```

## 📈 Analysis Features

### Theme Detection
Automatically identifies themes from your entries:
- **CS Simulation**: Technical/project content
- **Humor**: Lighthearted moments
- **Spiritual**: Religious/philosophical content
- **Childhood**: Nostalgic memories
- **Achievement**: Success stories
- **Personal Growth**: Development moments
- **Relationships**: Social interactions
- **Work**: Professional content
- **Health**: Wellness topics
- **Travel**: Journey experiences

### Character Tracking
- Identifies recurring people
- Tracks relationship dynamics
- Notes character development arcs

### Sentiment Analysis
- Emotional tone tracking
- Sentiment scoring (-1.0 to 1.0)
- Emotional journey mapping

### Narrative Threads
- Identifies ongoing storylines
- Tracks plot development
- Highlights key turning points

## 🎯 Use Cases

### Personal Journal Enhancement
Transform daily journal entries into a cohesive memoir with rich narrative depth.

### Creative Writing Development
Use the enhancement features to develop raw ideas into polished creative pieces.

### Academic Research
Analyze personal journals for research purposes with automated theme extraction.

### Book Creation
Generate publishable content from handwritten notes and journal entries.

### Content Creation
Create blog posts, articles, or social media content from personal reflections.

## 📁 Output Structure

```
output/
├── stage1_entries.json          # Raw OCR results
├── stage2_analysis.json         # Analysis results
├── stage2_summary.json          # Analysis summary
├── stage3_enhanced.json         # Enhanced entries
├── stage3_report.json           # Enhancement report
├── pipeline_summary.json        # Complete pipeline summary
└── documents/
    ├── my_enhanced_journal.md   # Markdown version
    ├── my_enhanced_journal.html # HTML version
    ├── my_enhanced_journal.json # JSON version
    └── publication_report.json  # Publication statistics
```

## 🔍 Example Output

### Original Entry
```
January 15, 2025
Today I started working on my CS simulation. It was frustrating at first but I finally got it working.
```

### Enhanced Entry
```
January 15, 2025

The morning light filtered through my office window as I sat down at my desk, ready to tackle the CS simulation that had been looming in my mind. The frustration was palpable as I stared at the blinking cursor, my fingers hovering over the keyboard like a pianist preparing for a complex piece.

The first few hours were a battle of wills between me and the code. Error messages seemed to mock my efforts, each one a reminder of the gap between my vision and the reality of implementation. But persistence has always been my ally, and slowly, methodically, I began to see patterns emerge from the chaos.

When the simulation finally sprang to life, the satisfaction was electric. Lines of code transformed into a living, breathing system, responding to my inputs with the precision I had envisioned. It was a moment of pure triumph, a reminder that the most rewarding victories often come after the hardest struggles.

The experience taught me something valuable about problem-solving: sometimes the most important step is simply refusing to give up.
```

## 🛠️ Customization

### Custom Enhancement Prompts
You can create custom enhancement requests for specific entries:

```python
from src.enhanced_journaling_engine.stage3_enhancement import EnhancementRequest

request = EnhancementRequest(
    entry_id="entry_0001",
    enhancement_prompt="Add more dialogue and make it more dramatic",
    focus_areas=["dialogue", "plot_development"],
    style_preferences={"tone": "dramatic", "pacing": "fast"}
)
```

### Custom Theme Categories
Modify the theme detection in `stage2_analysis.py`:

```python
self.theme_categories = [
    "Your Custom Theme 1",
    "Your Custom Theme 2",
    # ... add your themes
]
```

### Custom Color Detection
Adjust color ranges in `stage1_input.py`:

```python
self.color_ranges = {
    'your_color': ([h_min, s_min, v_min], [h_max, s_max, v_max]),
    # ... add your colors
}
```

## 🔧 Troubleshooting

### Common Issues

**OCR Not Working**
- Ensure images are high quality (300+ DPI)
- Check that text is clearly visible
- Verify custom model path if using one

**Analysis Failing**
- Check Gemini API key is valid
- Ensure internet connection
- Verify API quota limits

**Enhancement Issues**
- Check enhancement strategy settings
- Verify text length isn't too long
- Ensure API key has sufficient quota

### Performance Tips

**Large Datasets**
- Process in batches
- Use minimal enhancement for speed
- Consider running stages separately

**API Costs**
- Use default enhancement strategy
- Process entries in smaller batches
- Monitor API usage

## 📚 API Reference

### Main Engine
```python
from src.enhanced_journaling_engine.main import EnhancedJournalingEngine

engine = EnhancedJournalingEngine(config)
result = engine.run_full_pipeline("journal_pages/")
```

### Individual Stages
```python
# Stage 1: Input
entries = engine.run_stage1_input("journal_pages/")

# Stage 2: Analysis
analyses = engine.run_stage2_analysis(entries)

# Stage 3: Enhancement
enhanced = engine.run_stage3_enhancement(entries, analyses)

# Stage 4: Output
documents = engine.run_stage4_output(enhanced, analysis_summary)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini API for AI analysis and enhancement
- OpenCV for image processing and color detection
- Jinja2 for document templating
- The open-source community for inspiration and tools

---

**Transform your handwritten thoughts into published stories with the Enhanced Journaling Engine!** 🚀
