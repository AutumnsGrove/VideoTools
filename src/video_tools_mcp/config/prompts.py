"""
Default prompts for video analysis and screenshot extraction.

This module defines the standard prompts used by the Qwen VL model
for analyzing video frames and extracting smart screenshots.
"""


DEFAULT_ANALYSIS_PROMPT = """Analyze this video frame. Describe:
1. Main subjects and their activities
2. Scene/location description
3. Notable objects or text visible
4. Emotional tone or atmosphere
Be concise and factual."""


DEFAULT_SCREENSHOT_EXTRACTION_PROMPT = """Evaluate if this frame is worth capturing as a screenshot.
Capture frames with:
- Clear faces with visible expressions
- Significant scene changes
- Text or important visual information
- Emotionally notable moments
- Unique or memorable compositions

Respond with: CAPTURE or SKIP, followed by a brief reason."""


# Alternative analysis prompts for different use cases

DETAILED_ANALYSIS_PROMPT = """Provide a detailed analysis of this video frame:
1. Main subjects: Identify all people, animals, or primary objects
2. Activities: What actions are taking place?
3. Setting: Describe the location, lighting, and environment
4. Visual elements: Colors, composition, camera angle
5. Text/Graphics: Any visible text, logos, or graphical elements
6. Mood/Atmosphere: Emotional tone and overall feeling
7. Technical notes: Any notable visual effects or production elements

Be thorough and specific."""


TECHNICAL_ANALYSIS_PROMPT = """Analyze this video frame from a technical perspective:
1. Composition: Rule of thirds, framing, subject placement
2. Lighting: Direction, quality, color temperature
3. Focus: What's in focus, depth of field
4. Camera movement: Static, panning, zooming, etc.
5. Color grading: Color palette, saturation, contrast
6. Production quality: Professional, amateur, live, recorded

Provide objective technical observations."""


OCR_FOCUSED_PROMPT = """Analyze this video frame with focus on text content:
1. Extract all visible text (OCR)
2. Identify text locations (top, center, bottom, left, right)
3. Describe text formatting (size, color, font style)
4. Note any logos, brand names, or graphics with text
5. Briefly describe the visual context around the text

Prioritize accuracy in text extraction."""


ACCESSIBILITY_PROMPT = """Describe this video frame for accessibility purposes:
1. Visual scene description for screen readers
2. Identify all people and their apparent characteristics
3. Describe actions and movements
4. Note important visual information or context
5. Describe any text or graphical information
6. Mention colors only when relevant to understanding

Be clear, descriptive, and helpful for non-visual consumption."""


# Screenshot extraction prompts for specific use cases

PRESENTATION_SCREENSHOT_PROMPT = """Evaluate if this frame is good for a presentation screenshot.
Capture frames with:
- Clear slide content or visual aids
- Speaker in good lighting with professional posture
- Readable text or diagrams
- Minimal motion blur
- Good composition for a single image

Respond with: CAPTURE or SKIP, followed by a brief reason."""


TUTORIAL_SCREENSHOT_PROMPT = """Evaluate if this frame is worth capturing for a tutorial.
Capture frames with:
- Clear UI elements or interface screenshots
- Important steps in a process
- Before/after comparisons
- Error messages or important notifications
- Code snippets or command outputs
- Diagrams or visual explanations

Respond with: CAPTURE or SKIP, followed by a brief reason."""


SOCIAL_MEDIA_SCREENSHOT_PROMPT = """Evaluate if this frame would make a good social media post.
Capture frames with:
- Visually striking or aesthetically pleasing compositions
- Expressive faces or emotional moments
- Unique or shareable content
- Clear, uncluttered scenes
- Good lighting and colors
- Moments that tell a story

Respond with: CAPTURE or SKIP, followed by a brief reason."""
