from dataclasses import dataclass
from typing import List, Dict, Optional
from gemvox.config import config

@dataclass
class VoiceInfo:
    id: str
    display_name: str
    tone: str
    gender: str = "Neutral"
    language_code: str = "en-US"
    description: str = ""
    is_custom: bool = False

# The 30 featured studio voices for Gemini 3.8 Flash TTS
PREBUILT_VOICES: List[VoiceInfo] = [
    VoiceInfo("Zephyr", "Zephyr", "Bright", "Female", "en-US", "Bright, engaging and articulate"),
    VoiceInfo("Puck", "Puck", "Upbeat", "Male", "en-US", "Upbeat, energetic and friendly"),
    VoiceInfo("Charon", "Charon", "Informative", "Male", "en-US", "Informative, serious and steady"),
    VoiceInfo("Kore", "Kore", "Firm", "Female", "en-US", "Firm, confident and direct"),
    VoiceInfo("Fenrir", "Fenrir", "Excitable", "Male", "en-US", "Excitable, fast-paced and animated"),
    VoiceInfo("Leda", "Leda", "Youthful", "Female", "en-US", "Youthful, pleasant and expressive"),
    VoiceInfo("Orus", "Orus", "Firm", "Male", "en-US", "Firm, grounded and commanding"),
    VoiceInfo("Aoede", "Aoede", "Breezy", "Female", "en-US", "Breezy, light and conversational"),
    VoiceInfo("Callirrhoe", "Callirrhoe", "Easy-going", "Female", "en-US", "Easy-going, friendly and relaxed"),
    VoiceInfo("Autonoe", "Autonoe", "Bright", "Female", "en-US", "Bright, warm and welcoming"),
    VoiceInfo("Enceladus", "Enceladus", "Breathy", "Male", "en-US", "Breathy, intimate and gentle"),
    VoiceInfo("Iapetus", "Iapetus", "Clear", "Male", "en-US", "Clear, neutral and articulate"),
    VoiceInfo("Umbriel", "Umbriel", "Easy-going", "Male", "en-US", "Easy-going, casual and natural"),
    VoiceInfo("Algieba", "Algieba", "Smooth", "Female", "en-US", "Smooth, polished and professional"),
    VoiceInfo("Despina", "Despina", "Smooth", "Female", "en-US", "Smooth, melodious and warm"),
    VoiceInfo("Erinome", "Erinome", "Clear", "Female", "en-US", "Clear, crisp and professional"),
    VoiceInfo("Algenib", "Algenib", "Gravelly", "Male", "en-US", "Gravelly, deep and textured"),
    VoiceInfo("Rasalgethi", "Rasalgethi", "Informative", "Male", "en-US", "Informative, explanatory and clear"),
    VoiceInfo("Laomedeia", "Laomedeia", "Upbeat", "Female", "en-US", "Upbeat, cheerful and lively"),
    VoiceInfo("Achernar", "Achernar", "Soft", "Female", "en-US", "Soft, soothing and gentle"),
    VoiceInfo("Alnilam", "Alnilam", "Firm", "Male", "en-US", "Firm, authoritative and assertive"),
    VoiceInfo("Schedar", "Schedar", "Even", "Male", "en-US", "Even, balanced and measured"),
    VoiceInfo("Gacrux", "Gacrux", "Mature", "Male", "en-US", "Mature, experienced and trustworthy"),
    VoiceInfo("Pulcherrima", "Pulcherrima", "Forward", "Female", "en-US", "Forward, confident and vivid"),
    VoiceInfo("Achird", "Achird", "Friendly", "Male", "en-US", "Friendly, approachable and conversational"),
    VoiceInfo("Zubenelgenubi", "Zubenelgenubi", "Casual", "Male", "en-US", "Casual, informal and everyday"),
    VoiceInfo("Vindemiatrix", "Vindemiatrix", "Gentle", "Female", "en-US", "Gentle, compassionate and kind"),
    VoiceInfo("Sadachbia", "Sadachbia", "Lively", "Male", "en-US", "Lively, spirited and active"),
    VoiceInfo("Sadaltager", "Sadaltager", "Knowledgeable", "Male", "en-US", "Knowledgeable, academic and wise"),
    VoiceInfo("Sulafat", "Sulafat", "Warm", "Female", "en-US", "Warm, inviting and comfortable"),
]

# Style Presets for turn-level speech_metadata.style
STYLE_PRESETS: List[Dict[str, str]] = [
    {"name": "Cheerful and Friendly", "style": "cheerful and friendly"},
    {"name": "Calm and Relaxed", "style": "calm and relaxed"},
    {"name": "Whispered Urgently", "style": "whispered urgently"},
    {"name": "Out of Breath", "style": "out of breath"},
    {"name": "Warm and Enthusiastic", "style": "warm and enthusiastic"},
    {"name": "Authoritative News Anchor", "style": "authoritative news anchor"},
    {"name": "Gentle Bedtime Story", "style": "gentle bedtime story, soothing and soft"},
    {"name": "Excited Sports Commentator", "style": "excited sports commentator, high energy"},
    {"name": "Mysterious Storyteller", "style": "mysterious storyteller, suspenseful and slow"},
    {"name": "Thoughtful and Reflective", "style": "thoughtful and reflective, slow-paced"},
    {"name": "Professional and Formal", "style": "professional, crisp and corporate"},
    {"name": "Sympathetic and Caring", "style": "sympathetic, compassionate and caring"},
]

# Inline Vocal Tags for momentary events
INLINE_VOCAL_TAGS: List[Dict[str, str]] = [
    {"tag": "<short pause>", "label": "Short Pause", "description": "Brief natural conversational pause"},
    {"tag": "<long pause>", "label": "Long Pause", "description": "Extended pause for dramatic effect or separation"},
    {"tag": "<sigh>", "label": "Sigh", "description": "Audible breath of relief, weariness, or sadness"},
    {"tag": "<cough>", "label": "Cough", "description": "Brief clearing of throat or light cough"},
    {"tag": "<whisper>", "label": "Whisper", "description": "Transition to a low, intimate whisper"},
    {"tag": "<laugh>", "label": "Laugh", "description": "Audible laughter burst"},
    {"tag": "<chuckle>", "label": "Chuckle", "description": "Subtle, quiet chuckle or amusement"},
    {"tag": "<gasp>", "label": "Gasp", "description": "Sharp intake of air from surprise or shock"},
    {"tag": "<throat-clearing>", "label": "Throat Clearing", "description": "Polite throat clear before continuing"},
    {"tag": "<yawn>", "label": "Yawn", "description": "Sleepy or tired vocal inflection"},
    {"tag": "<groan>", "label": "Groan", "description": "Expression of mild distress or physical effort"},
    {"tag": "<applause>", "label": "Applause", "description": "Audible audience applause effect"},
]

# Supported Gemini TTS Models
SUPPORTED_MODELS: List[Dict[str, str]] = [
    {
        "id": "gemini-3.8-flash-tts",
        "name": "Gemini 3.8 Flash TTS (High Fidelity)",
        "description": "Studio-grade voice fidelity, expressive acting, multi-speaker, and long-form stability."
    },
    {
        "id": "gemini-3.8-flash-lite-tts",
        "name": "Gemini 3.8 Flash-Lite TTS (Fast & Low Latency)",
        "description": "Optimized for high-throughput, lowest latency, and cost-efficient conversational speech."
    }
]

def get_all_style_presets() -> List[Dict[str, str]]:
    """Returns combined list of user-created custom style presets and built-in style presets."""
    presets: List[Dict[str, str]] = []
    custom_saved = config.get("custom_styles", [])
    for cs in custom_saved:
        presets.append({
            "name": cs.get("name", "Custom Style"),
            "style": cs.get("style", ""),
            "is_custom": True
        })
    for bp in STYLE_PRESETS:
        presets.append({
            "name": bp["name"],
            "style": bp["style"],
            "is_custom": False
        })
    return presets

def get_all_voices() -> List[VoiceInfo]:
    """Returns combined list of prebuilt voices and user-created custom voices."""
    voices = list(PREBUILT_VOICES)
    custom_saved = config.get("custom_voices", [])
    for cv in custom_saved:
        voices.append(VoiceInfo(
            id=cv.get("id"),
            display_name=f"[Custom] {cv.get('display_name')}",
            tone=cv.get("type", "Custom"),
            gender="Custom",
            language_code="User",
            description=cv.get("description", ""),
            is_custom=True
        ))
    return voices

def find_voice(voice_id: str) -> Optional[VoiceInfo]:
    for v in get_all_voices():
        if v.id.lower() == voice_id.lower():
            return v
    return None
