#!/usr/bin/env python3
"""Generate architecture diagram as PNG using PIL."""

from PIL import Image, ImageDraw, ImageFont
import textwrap

# Create a new image with white background
width, height = 1400, 1000
image = Image.new('RGB', (width, height), color=(255, 255, 255))
draw = ImageDraw.Draw(image)

# Define colors
COLOR_HEADER = (41, 128, 185)  # Blue
COLOR_STEP = (155, 89, 182)     # Purple
COLOR_SUPPORT = (52, 152, 219)  # Light Blue
COLOR_DATA = (46, 204, 113)     # Green
COLOR_LOG = (231, 76, 60)       # Red
COLOR_TEXT = (50, 50, 50)       # Dark gray
COLOR_ARROW = (100, 100, 100)   # Gray

try:
    title_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 28)
    section_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 18)
    text_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 14)
except:
    title_font = ImageFont.load_default()
    section_font = ImageFont.load_default()
    text_font = ImageFont.load_default()

def draw_box(x, y, w, h, text, color, text_color=(255, 255, 255)):
    """Draw a colored box with text."""
    draw.rectangle([x, y, x+w, y+h], fill=color, outline=COLOR_TEXT, width=2)
    
    # Wrap text and center it
    lines = textwrap.wrap(text, width=20)
    line_height = 16
    total_height = len(lines) * line_height
    start_y = y + (h - total_height) // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = bbox[2] - bbox[0]
        text_x = x + (w - line_width) // 2
        draw.text((text_x, start_y + i * line_height), line, fill=text_color, font=text_font)

def draw_arrow(x1, y1, x2, y2, label=""):
    """Draw an arrow between two points."""
    # Draw line
    draw.line([(x1, y1), (x2, y2)], fill=COLOR_ARROW, width=2)
    
    # Draw arrowhead
    arrow_size = 10
    if x2 > x1:  # Right arrow
        draw.polygon([(x2, y2), (x2 - arrow_size, y2 - arrow_size//2), (x2 - arrow_size, y2 + arrow_size//2)], 
                     fill=COLOR_ARROW)
    elif x2 < x1:  # Left arrow
        draw.polygon([(x2, y2), (x2 + arrow_size, y2 - arrow_size//2), (x2 + arrow_size, y2 + arrow_size//2)], 
                     fill=COLOR_ARROW)
    elif y2 > y1:  # Down arrow
        draw.polygon([(x2, y2), (x2 - arrow_size//2, y2 - arrow_size), (x2 + arrow_size//2, y2 - arrow_size)], 
                     fill=COLOR_ARROW)
    
    # Add label if provided
    if label:
        bbox = draw.textbbox((0, 0), label, font=text_font)
        label_width = bbox[2] - bbox[0]
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        draw.text((mid_x - label_width // 2, mid_y - 10), label, fill=COLOR_TEXT, font=text_font)

# Title
draw.text((50, 20), "StudyVibe: Mood-Aware Music Recommender Architecture", fill=COLOR_HEADER, font=title_font)

# Row 1: User Input
y_row1 = 100
draw_box(50, y_row1, 300, 80, "🌐 Web UI\n(Flask + Tailwind)", COLOR_SUPPORT)
draw_arrow(350, y_row1 + 40, 450, y_row1 + 40)

# Row 2: Orchestrator
y_row2 = 100
draw_box(450, y_row2, 300, 80, "📊 Pipeline\nOrchestrator\n(src/agent.py)", COLOR_HEADER)
draw_arrow(750, y_row2 + 40, 850, y_row2 + 40)

# Row 3: 5 Pipeline Steps
y_row3 = 250
step_width = 240
step_height = 100
step_y = y_row3

# Steps 1-5
step_texts = [
    "Step 1:\nParse Intent\n(Classifier)",
    "Step 2:\nResolve Activity\n(Profile Lookup)",
    "Step 3:\nRetrieve Catalog\n(Last.fm + CSV)",
    "Step 4:\nRerank Songs\n(Scorer)",
    "Step 5:\nExplain Results\n(Templates)"
]

step_x_positions = [50, 310, 570, 830, 1090]
for i, (step_text, step_x) in enumerate(zip(step_texts, step_x_positions)):
    if step_x + step_width <= width:
        draw_box(step_x, step_y, step_width, step_height, step_text, COLOR_STEP)
        
        # Draw arrows between steps
        if i < len(step_x_positions) - 1:
            draw_arrow(step_x + step_width, step_y + step_height // 2, 
                      step_x_positions[i + 1], step_y + step_height // 2)

# Row 4: Support Systems
y_row4 = 450
draw_box(50, y_row4, 280, 80, "✓ Guardrails\n(5-Layer Validation)", COLOR_DATA)
draw_arrow(330, y_row4 + 40, 400, y_row4 + 40)

draw_box(400, y_row4, 280, 80, "📀 Data Sources\n(Last.fm + CSV)", COLOR_DATA)
draw_arrow(680, y_row4 + 40, 750, y_row4 + 40)

draw_box(750, y_row4, 280, 80, "📝 Logging\n(logs/studyvibe.log)", COLOR_LOG)

# Row 5: Output
y_row5 = 650
draw_box(400, y_row5, 600, 100, "✨ Results Panel\nTop 5 Recommendations + Pipeline Trace", COLOR_SUPPORT, (0, 0, 0))

# Row 6: Key Features
y_row6 = 850
features = [
    "🔍 Transparent Explanations",
    "⚡ Real-time Audio Features",
    "🛡️ Input Validation",
    "📊 Performance Metrics"
]

feature_x = 50
for feature in features:
    bbox = draw.textbbox((0, 0), feature, font=text_font)
    feature_width = bbox[2] - bbox[0] + 20
    draw.text((feature_x, y_row6), feature, fill=COLOR_TEXT, font=text_font)
    feature_x += feature_width + 30

# Add footer
footer_text = "Extension of VibeMatcher 2.0 | Agentic Pipeline with Observable Intermediates | Rule-Based Activity Classification"
bbox = draw.textbbox((0, 0), footer_text, font=text_font)
footer_width = bbox[2] - bbox[0]
draw.text(((width - footer_width) // 2, height - 40), footer_text, fill=COLOR_TEXT, font=text_font)

# Save the image
image.save('assets/architecture.png')
print("✅ Generated assets/architecture.png successfully!")
