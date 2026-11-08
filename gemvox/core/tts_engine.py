import base64
import io
import os
import re
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.client import client_manager
from gemvox.core.voice_catalog import find_voice

class TTSEngine:
    """Core synthesis engine for Gemini 3.8 Flash TTS."""

    def __init__(self):
        pass

    def calculate_text_stats(self, text: str) -> Dict[str, int]:
        """
        Calculate character count, word count (supporting both English and Thai script),
        line count, and estimated speaking duration in seconds.
        """
        raw = text.strip()
        if not raw:
            return {"chars": 0, "words": 0, "lines": 0, "seconds": 0}

        lines = [ln for ln in raw.splitlines() if ln.strip()]
        chars = len(raw)

        # Clean vocal tags <...> and speaker prefixes/styles for speech duration estimation
        cleaned = re.sub(r"<[^>]+>", " ", raw)
        cleaned = re.sub(r"\[[^\]]+\]", " ", cleaned).strip()

        # Count Thai characters vs space-separated words
        thai_chars = len(re.findall(r"[\u0E00-\u0E7F]", cleaned))
        non_thai_text = re.sub(r"[\u0E00-\u0E7F]+", " ", cleaned)
        en_words = len(non_thai_text.split())
        approx_thai_words = max(1, round(thai_chars / 5.5)) if thai_chars > 0 else 0
        total_words = en_words + approx_thai_words

        # Estimate speaking rate (~2.5 words/sec, minimum 1s for non-empty text)
        est_seconds = max(1, round(total_words / 2.5))
        return {
            "chars": chars,
            "words": total_words,
            "lines": len(lines),
            "seconds": est_seconds
        }

    def _get_timestamped_filename(self, prefix: str = "gemvox") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.wav"
        return str(config.output_dir / filename)

    def _get_wav_duration(self, wav_bytes: bytes) -> float:
        try:
            with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return round(frames / float(rate), 2)
        except Exception:
            return 0.0

    def synthesize_single_speaker(
        self,
        text: str,
        voice: str = "Kore",
        style: Optional[str] = None,
        model: str = "gemini-3.8-flash-tts",
        output_filepath: Optional[str] = None
    ) -> Tuple[bytes, str, float]:
        """
        Synthesizes single-speaker audio verbatim with turn-level style instructions.
        Returns: (wav_bytes, saved_filepath, duration_seconds)
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        client = client_manager.get_client()

        announcer.play_sound("start")
        announcer.announce(tr("announce_synthesizing_single", voice=voice))

        # Construct input payload
        content_item: Dict[str, Any] = {
            "type": "text",
            "text": text.strip()
        }
        if style and style.strip():
            content_item["annotations"] = [{
                "type": "speech_metadata",
                "style": style.strip()
            }]

        input_payload = [{
            "type": "user_input",
            "content": [content_item]
        }]

        # Speech config
        speech_config = [
            {"voice": voice}
        ]

        start_time = time.time()
        try:
            interaction = client.interactions.create(
                model=model,
                input=input_payload,
                response_format={"type": "audio"},
                generation_config={
                    "speech_config": speech_config
                }
            )
        except Exception as e:
            announcer.play_sound("error")
            err = tr("announce_tts_error", error=e)
            announcer.announce(err)
            raise RuntimeError(err) from e

        if not interaction.output_audio or not interaction.output_audio.data:
            announcer.play_sound("error")
            raise RuntimeError("Model did not return any audio data.")

        wav_bytes = base64.b64decode(interaction.output_audio.data)
        elapsed = round(time.time() - start_time, 2)
        duration = self._get_wav_duration(wav_bytes)

        # Save to disk
        out_path = output_filepath or self._get_timestamped_filename(f"speech_{voice.lower()}")
        with open(out_path, "wb") as f:
            f.write(wav_bytes)

        announcer.play_sound("success")
        announcer.announce(tr("announce_single_ready", elapsed=elapsed, duration=duration))

        return wav_bytes, out_path, duration

    def synthesize_multi_speaker(
        self,
        turns: List[Dict[str, str]],
        speaker_voice_map: Dict[str, str],
        model: str = "gemini-3.8-flash-tts",
        output_filepath: Optional[str] = None
    ) -> Tuple[bytes, str, float]:
        """
        Synthesizes multi-speaker dialogue.
        turns: List of {"speaker": str, "text": str, "style": Optional[str]}
        speaker_voice_map: Dict of {speaker_name: voice_name}
        """
        if not turns:
            raise ValueError("Dialogue script turns cannot be empty.")
        if not speaker_voice_map:
            raise ValueError("Speaker voice mapping cannot be empty.")

        client = client_manager.get_client()

        speakers_count = len(speaker_voice_map)
        turns_count = len(turns)
        announcer.play_sound("start")
        announcer.announce(tr("announce_synthesizing_multi", speakers=speakers_count, turns=turns_count))

        content_items = []
        for turn in turns:
            spk = turn.get("speaker", "Speaker").strip()
            txt = turn.get("text", "").strip()
            sty = turn.get("style", "").strip()

            if not txt:
                continue

            ann: Dict[str, Any] = {
                "type": "speech_metadata",
                "speaker": spk
            }
            if sty:
                ann["style"] = sty

            content_items.append({
                "type": "text",
                "text": txt,
                "annotations": [ann]
            })

        if not content_items:
            raise ValueError("All dialogue turns were empty.")

        input_payload = [{
            "type": "user_input",
            "content": content_items
        }]

        speakers_config = [
            {"speaker": spk, "voice": v}
            for spk, v in speaker_voice_map.items()
        ]

        generation_config = {
            "speech_config": {
                "mode": "conversational",
                "speakers": speakers_config
            }
        }

        start_time = time.time()
        try:
            interaction = client.interactions.create(
                model=model,
                input=input_payload,
                response_format={"type": "audio"},
                generation_config=generation_config
            )
        except Exception as e:
            announcer.play_sound("error")
            err = tr("announce_multi_error", error=e)
            announcer.announce(err)
            raise RuntimeError(err) from e

        if not interaction.output_audio or not interaction.output_audio.data:
            announcer.play_sound("error")
            raise RuntimeError("Model did not return dialogue audio.")

        wav_bytes = base64.b64decode(interaction.output_audio.data)
        elapsed = round(time.time() - start_time, 2)
        duration = self._get_wav_duration(wav_bytes)

        out_path = output_filepath or self._get_timestamped_filename("dialogue")
        with open(out_path, "wb") as f:
            f.write(wav_bytes)

        announcer.play_sound("success")
        announcer.announce(tr("announce_multi_ready", elapsed=elapsed, duration=duration))

        return wav_bytes, out_path, duration

    def parse_dialogue_script(self, script_text: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Parses accessible dialogue script format:
        Speaker: Text to speak [style instruction]
        Example:
        Alice: Hello there! [cheerful]
        Bob: Good morning! [calm]
        Returns: (turns_list, list_of_detected_speakers)
        """
        lines = script_text.strip().splitlines()
        turns = []
        speakers = set()

        # Regex matching: "SpeakerName: Turn text [optional style]"
        pattern = re.compile(r"^([^:]+):\s*(.*?)(?:\[(.*?)\])?$")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            match = pattern.match(line)
            if match:
                speaker = match.group(1).strip()
                text = match.group(2).strip()
                style = match.group(3).strip() if match.group(3) else ""

                if text:
                    turns.append({
                        "speaker": speaker,
                        "text": text,
                        "style": style
                    })
                    speakers.add(speaker)
            else:
                # Line without speaker label: continuation of previous turn or generic turn
                if turns:
                    turns[-1]["text"] += " " + line
                else:
                    turns.append({
                        "speaker": "Speaker 1",
                        "text": line,
                        "style": ""
                    })
                    speakers.add("Speaker 1")

        return turns, sorted(list(speakers))

    def design_voice(
        self,
        display_name: str,
        prompt_description: str,
        gender: str = "neutral",
        language_code: str = "en-US",
        model: str = "gemini-3.8-flash-tts"
    ) -> Tuple[str, bytes, str]:
        """
        Creates a custom vocal persona using Voice Design from a text description.
        Returns: (voice_id, sample_audio_bytes, preview_filepath)
        """
        client = client_manager.get_client()

        announcer.play_sound("start")
        announcer.announce(tr("announce_designing_voice", name=display_name))

        voice_payload = {
            "model": model,
            "type": "prompted",
            "display_name": display_name,
            "gender": gender.lower(),
            "language_code": language_code,
            "prompted": {
                "input": prompt_description
            }
        }

        try:
            created_voice = client.voices.create(
                store=True,
                voice=voice_payload
            )
        except Exception as e:
            announcer.play_sound("error")
            err = tr("announce_design_error", error=e)
            announcer.announce(err)
            raise RuntimeError(err) from e

        voice_id = getattr(created_voice, "id", "")
        sample_bytes = b""
        preview_path = ""

        if created_voice.sample_audio and created_voice.sample_audio.data:
            sample_bytes = base64.b64decode(created_voice.sample_audio.data)
            preview_path = self._get_timestamped_filename(f"preview_{display_name.lower().replace(' ', '_')}")
            with open(preview_path, "wb") as f:
                f.write(sample_bytes)

        # Save to custom voices in config
        config.add_custom_voice(
            voice_id=voice_id,
            display_name=display_name,
            voice_type="Designed (Prompted)",
            description=prompt_description
        )

        announcer.play_sound("success")
        announcer.announce(tr("announce_design_ready", voice_id=voice_id))

        return voice_id, sample_bytes, preview_path

    def replicate_voice(
        self,
        display_name: str,
        reference_audio_path: str,
        consent_audio_path: str,
        store: bool = True,
        model: str = "gemini-3.8-flash-tts"
    ) -> str:
        """
        Replicates a voice using reference speech sample and consent verification sample.
        Returns: voice_id (or voice_key)
        """
        if not os.path.exists(reference_audio_path):
            raise FileNotFoundError(f"Reference audio not found: {reference_audio_path}")
        if not os.path.exists(consent_audio_path):
            raise FileNotFoundError(f"Consent audio not found: {consent_audio_path}")

        client = client_manager.get_client()
        announcer.play_sound("start")
        announcer.announce(tr("announce_replicating_voice", name=display_name))

        with open(reference_audio_path, "rb") as f:
            ref_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(consent_audio_path, "rb") as f:
            con_b64 = base64.b64encode(f.read()).decode("utf-8")

        voice_payload = {
            "model": model,
            "type": "replicated",
            "display_name": display_name,
            "replicated": {
                "source_audio": {
                    "data": ref_b64,
                    "mime_type": "audio/wav"
                },
                "consent_audio": {
                    "data": con_b64,
                    "mime_type": "audio/wav"
                }
            }
        }

        try:
            replicated_voice = client.voices.create(
                store=store,
                voice=voice_payload
            )
        except Exception as e:
            announcer.play_sound("error")
            err = tr("announce_replicate_error", error=e)
            announcer.announce(err)
            raise RuntimeError(err) from e

        voice_identifier = getattr(replicated_voice, "id", None) or getattr(replicated_voice, "key", "")

        config.add_custom_voice(
            voice_id=voice_identifier,
            display_name=display_name,
            voice_type="Replicated",
            description=f"Replicated from {Path(reference_audio_path).name}"
        )

        announcer.play_sound("success")
        announcer.announce(tr("announce_replicate_ready", voice_id=voice_identifier))

        return voice_identifier

    def search_voice_library(
        self,
        search_query: Optional[str] = None,
        language_code: Optional[str] = None,
        gender: Optional[str] = None,
        context_domain: Optional[str] = None,
        page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """Queries the Gemini Extended Voice Library."""
        client = client_manager.get_client()
        announcer.announce(tr("announce_querying_library"))

        kwargs: Dict[str, Any] = {"page_size": page_size}
        if search_query and search_query.strip():
            kwargs["search"] = search_query.strip()
        if language_code and language_code.strip():
            kwargs["language_code"] = [language_code.strip()]
        if gender and gender.strip() and gender.lower() != "all":
            kwargs["gender"] = [gender.strip().lower()]
        if context_domain and context_domain.strip() and context_domain.lower() != "all":
            kwargs["contexts"] = [context_domain.strip()]

        try:
            response = client.voices.list(**kwargs)
            results = []
            for v in (response.voices or []):
                results.append({
                    "id": getattr(v, "id", ""),
                    "display_name": getattr(v, "display_name", ""),
                    "language_code": getattr(v, "language_code", ""),
                    "accent": getattr(v, "accent", ""),
                    "gender": getattr(v, "gender", ""),
                    "pitch": getattr(v, "pitch", ""),
                    "description": getattr(v, "description", "")
                })
            announcer.announce(tr("announce_found_voices", count=len(results)))
            return results
        except Exception as e:
            err = tr("announce_library_error", error=e)
            announcer.announce(err)
            raise RuntimeError(err) from e

# Global TTS Engine instance
tts_engine = TTSEngine()
