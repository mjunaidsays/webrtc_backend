import openai
import asyncio
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = settings.OPENAI_API_KEY

async def get_insights_from_transcript(transcript: str) -> str:
    """Generate meeting insights from transcript using OpenAI GPT-4.1-nano (new API)"""
    
    system_prompt = '''You are an expert meeting analyst. Your job is to analyze the provided meeting transcript and extract the following, using clear, concise bullet points for each section:

# Meeting Summary
- Summarize the main topics, goals, and outcomes of the meeting in 3-6 bullet points.
- Use direct, professional language and avoid repetition.
- Focus on what was discussed, decided, and any important context.

---

# Action Items
- List all actionable tasks, follow-ups, or assignments mentioned in the meeting.
- Each item should be specific, actionable, and, if possible, include the responsible person or team.
- If no action items were discussed, write "None identified."

---

# Key Decisions
- List all key decisions made during the meeting, each as a bullet point.
- For each decision, briefly state what was decided and who made the decision (if mentioned).
- If no decisions were made, write "None identified."

Always use the above structure and headings. Separate each section with '---'. Do not include any content outside these sections. Be as informative and actionable as possible.'''

    try:
        response = await asyncio.to_thread(
            lambda: openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please analyze this meeting transcript:\n\n{transcript}"}
                ],
                max_tokens=1000,
                temperature=0.3
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        return f"# Meeting Summary\nUnable to generate summary due to technical issues.\n\n---\n# Action Items\nNone identified.\n\n---\n# Key Decisions\nNone identified."

# def get_insights_from_transcript_sync(transcript: str) -> str:
#     """Synchronous version for backward compatibility"""
#     return asyncio.run(get_insights_from_transcript(transcript)) 