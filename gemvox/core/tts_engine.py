import base64
import io
import os
import re
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.client import client_manager
from gemvox.core.voice_catalog import (
    PREBUILT_VOICES,
    find_voice,
    get_custom_voice_record,
)

# Priority order of fallback TTS models when a model returns 404 Not Found
FALLBACK_TTS_MODELS: List[str] = [
    "gemini-2.5-flash-preview-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-pro-preview-tts",
    "gemini-3.8-flash-lite-tts",
    "gemini-3.8-flash-tts",
]

PREBUILT_VOICE_NAMES = {v.id.lower(): v.id for v in PREBUILT_VOICES}


class TTSEngine:
    """
    Core synthesis engine for Gemini TTS (supporting Gemini 2.5, 3.1, and 3.8 TTS models).
    Features automatic endpoint selection (generate_content & interactions API),
    automatic 404 model fallback discovery, and automatic raw PCM-to-WAV RIFF wrapping.
    """

    def __init__(self):
        self._unavailable_models: Set[str] = set()
        self._unavailable_interactions_models: Set[str] = set()
        self._discovered_tts_models: Optional[List[str]] = None
        self._last_working_model: Optional[str] = None

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
        safe_prefix = re.sub(r"[^a-zA-Z0-9_\-]", "_", prefix)
        filename = f"{safe_prefix}_{timestamp}.wav"
        return str(config.output_dir / filename)

    def _ensure_wav_bytes(
        self,
        audio_bytes: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
        sampwidth: int = 2
    ) -> bytes:
        """
        Ensure returned audio bytes have a valid RIFF WAV header.
        Gemini 2.5 and 3.1 TTS models return raw 24kHz 16-bit mono signed little-endian PCM
        (audio/L16), whereas Gemini 3.8 unary calls may return RIFF WAV directly.
        """
        if not audio_bytes:
            return b""
        if len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
            return audio_bytes

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_bytes)
        return buf.getvalue()

    def _extract_pcm_frames(self, wav_or_pcm: bytes) -> Tuple[bytes, int, int, int]:
        """Return (raw_pcm_frames, framerate, nchannels, sampwidth) from WAV or raw PCM."""
        if len(wav_or_pcm) >= 12 and wav_or_pcm[:4] == b"RIFF" and wav_or_pcm[8:12] == b"WAVE":
            try:
                with wave.open(io.BytesIO(wav_or_pcm), "rb") as wf:
                    return (
                        wf.readframes(wf.getnframes()),
                        wf.getframerate(),
                        wf.getnchannels(),
                        wf.getsampwidth(),
                    )
            except Exception:
                pass
        return wav_or_pcm, 24000, 1, 2

    def _decode_inline_audio(self, raw_data: Any) -> bytes:
        """Safely decode inline_data.data whether the SDK provides raw bytes or base64 str."""
        if not raw_data:
            return b""
        if isinstance(raw_data, str):
            return base64.b64decode(raw_data)
        if isinstance(raw_data, (bytes, bytearray)):
            b = bytes(raw_data)
            if b.startswith(b"RIFF"):
                return b
            # Check if bytes are actually ASCII base64 encoded RIFF ("UklGR...")
            if b.startswith(b"UklGR"):
                try:
                    return base64.b64decode(b)
                except Exception:
                    return b
            return b
        return b""

    def _get_wav_duration(self, wav_bytes: bytes) -> float:
        try:
            with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return round(frames / float(rate), 2)
        except Exception:
            return 0.0

    def _is_not_found_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return (
            "404" in msg
            or "not_found" in msg
            or "not found" in msg
            or "is not supported for" in msg
            or "does not exist" in msg
        )

    def _discover_available_tts_models(self, client: Any) -> List[str]:
        """Query client.models.list() once per session to find TTS models enabled for this API key."""
        if self._discovered_tts_models is not None:
            return self._discovered_tts_models

        found: List[str] = []
        try:
            for m in client.models.list():
                name = getattr(m, "name", "") or ""
                if name.startswith("models/"):
                    name = name[len("models/"):]
                if "tts" in name.lower() and name not in found:
                    found.append(name)
        except Exception:
            pass

        self._discovered_tts_models = found
        return found

    def _get_candidate_models(self, requested_model: str, client: Any) -> List[str]:
        """Build an ordered list of candidate TTS models to try, starting with requested_model."""
        candidates: List[str] = []

        if requested_model and requested_model not in self._unavailable_models:
            candidates.append(requested_model)

        if self._last_working_model and self._last_working_model not in candidates and self._last_working_model not in self._unavailable_models:
            candidates.append(self._last_working_model)

        # Include models discovered from the user's API key
        for dm in self._discover_available_tts_models(client):
            if dm not in candidates and dm not in self._unavailable_models:
                candidates.append(dm)

        # Include standard fallback TTS models
        for fm in FALLBACK_TTS_MODELS:
            if fm not in candidates and fm not in self._unavailable_models:
                candidates.append(fm)

        # If everything was marked unavailable (e.g. transient network issue), reset and try all
        if not candidates:
            self._unavailable_models.clear()
            candidates = [requested_model] + [m for m in FALLBACK_TTS_MODELS if m != requested_model]

        return candidates

    def _resolve_voice_and_style(self, voice: str, style: Optional[str]) -> Tuple[str, Optional[str]]:
        """
        Resolve custom/designed voices so they work seamlessly even on models that only
        accept the 30 prebuilt voice names (like Gemini 2.5 / 3.1 TTS).
        Returns (resolved_prebuilt_or_id, combined_style).
        """
        clean_style = style.strip() if style and style.strip() else ""
        if not voice:
            return "Kore", clean_style or None

        # Check if it's one of the 30 prebuilt studio voices
        if voice.lower() in PREBUILT_VOICE_NAMES:
            return PREBUILT_VOICE_NAMES[voice.lower()], clean_style or None

        # Check if it's a user custom voice with a persona description
        cv = get_custom_voice_record(voice)
        if cv:
            base_voice = cv.get("base_voice", "")
            if not base_voice:
                gender = (cv.get("gender") or "").lower()
                if gender == "male":
                    base_voice = "Charon"
                elif gender == "female":
                    base_voice = "Kore"
                else:
                    base_voice = "Zephyr"
            persona_desc = (cv.get("description") or "").strip()
            if persona_desc and not persona_desc.lower().startswith("replicated from"):
                combined = f"{persona_desc}. Delivery: {clean_style}" if clean_style else persona_desc
                return base_voice, combined
            return base_voice, clean_style or None

        return voice, clean_style or None

    def _synthesize_single_via_generate_content(
        self,
        client: Any,
        model: str,
        text: str,
        voice: str,
        style: Optional[str]
    ) -> bytes:
        """Synthesize single-speaker audio using client.models.generate_content."""
        resolved_voice, resolved_style = self._resolve_voice_and_style(voice, style)

        # If using a non-3.8 model (or custom persona), resolved_voice is guaranteed prebuilt
        target_voice = resolved_voice if not (voice.startswith("voice_") and "3.8" in model) else voice

        if resolved_style:
            prompt_text = f"Say in a {resolved_style} tone: {text.strip()}"
        else:
            prompt_text = text.strip()

        gen_config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": target_voice
                    }
                }
            }
        }

        response = client.models.generate_content(
            model=model,
            contents=prompt_text,
            config=gen_config
        )

        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    raw_audio = self._decode_inline_audio(inline_data.data)
                    if raw_audio:
                        return self._ensure_wav_bytes(raw_audio)

        raise RuntimeError("Model did not return any audio data.")

    def _synthesize_single_via_interactions(
        self,
        client: Any,
        model: str,
        text: str,
        voice: str,
        style: Optional[str]
    ) -> bytes:
        """Synthesize single-speaker audio using client.interactions.create (Gemini 3.8 schema)."""
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

        interaction = client.interactions.create(
            model=model,
            input=input_payload,
            response_format={"type": "audio"},
            generation_config={
                "speech_config": [{"voice": voice}]
            }
        )

        if not interaction.output_audio or not interaction.output_audio.data:
            raise RuntimeError("Model did not return any audio data.")

        raw_audio = self._decode_inline_audio(interaction.output_audio.data)
        return self._ensure_wav_bytes(raw_audio)

    def synthesize_single_speaker(
        self,
        text: str,
        voice: str = "Kore",
        style: Optional[str] = None,
        model: str = "gemini-2.5-flash-preview-tts",
        output_filepath: Optional[str] = None
    ) -> Tuple[bytes, str, float]:
        """
        Synthesizes single-speaker audio with automatic endpoint and model fallback if 404 occurs.
        Returns: (wav_bytes, saved_filepath, duration_seconds)
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        client = client_manager.get_client()

        announcer.play_sound("start")
        announcer.announce(tr("announce_synthesizing_single", voice=voice))

        start_time = time.time()
        candidates = self._get_candidate_models(model, client)
        last_error: Optional[Exception] = None
        wav_bytes: bytes = b""
        used_model = model

        for cand_model in candidates:
            # 1. If Gemini 3.8 model and interactions API not marked unavailable, try interactions first
            if "3.8" in cand_model and hasattr(client, "interactions") and cand_model not in self._unavailable_interactions_models:
                try:
                    wav_bytes = self._synthesize_single_via_interactions(
                        client=client,
                        model=cand_model,
                        text=text,
                        voice=voice,
                        style=style
                    )
                    if wav_bytes:
                        used_model = cand_model
                        break
                except Exception as e_inter:
                    last_error = e_inter
                    self._unavailable_interactions_models.add(cand_model)
                    if not self._is_not_found_error(e_inter):
                        # Still try generate_content before giving up on this model
                        pass

            # 2. Try standard client.models.generate_content (universal across 2.5, 3.1, and 3.8)
            try:
                wav_bytes = self._synthesize_single_via_generate_content(
                    client=client,
                    model=cand_model,
                    text=text,
                    voice=voice,
                    style=style
                )
                if wav_bytes:
                    used_model = cand_model
                    break
            except Exception as e_gen:
                last_error = e_gen
                if self._is_not_found_error(e_gen):
                    self._unavailable_models.add(cand_model)
                    continue
                else:
                    # Non-404 error (e.g. quota, invalid key, safety): stop and report immediately
                    break

        if not wav_bytes:
            announcer.play_sound("error")
            err = tr("announce_tts_error", error=last_error or "Unknown TTS synthesis error")
            announcer.announce(err)
            raise RuntimeError(err) from last_error

        self._last_working_model = used_model
        elapsed = round(time.time() - start_time, 2)
        duration = self._get_wav_duration(wav_bytes)

        # Save to disk
        out_path = output_filepath or self._get_timestamped_filename(f"speech_{voice.lower()}")
        with open(out_path, "wb") as f:
            f.write(wav_bytes)

        announcer.play_sound("success")
        announcer.announce(tr("announce_single_ready", elapsed=elapsed, duration=duration))

        return wav_bytes, out_path, duration

    def _synthesize_multi_via_interactions(
        self,
        client: Any,
        model: str,
        turns: List[Dict[str, str]],
        speaker_voice_map: Dict[str, str]
    ) -> bytes:
        """Synthesize multi-speaker dialogue via Gemini 3.8 interactions API."""
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

        input_payload = [{
            "type": "user_input",
            "content": content_items
        }]

        speakers_config = [
            {"speaker": spk, "voice": v}
            for spk, v in speaker_voice_map.items()
        ]

        interaction = client.interactions.create(
            model=model,
            input=input_payload,
            response_format={"type": "audio"},
            generation_config={
                "speech_config": {
                    "mode": "conversational",
                    "speakers": speakers_config
                }
            }
        )

        if not interaction.output_audio or not interaction.output_audio.data:
            raise RuntimeError("Model did not return dialogue audio.")

        raw_audio = self._decode_inline_audio(interaction.output_audio.data)
        return self._ensure_wav_bytes(raw_audio)

    def _synthesize_multi_via_generate_content(
        self,
        client: Any,
        model: str,
        turns: List[Dict[str, str]],
        speaker_voice_map: Dict[str, str]
    ) -> bytes:
        """
        Synthesize multi-speaker dialogue via client.models.generate_content.
        Supports 1, 2, or 3+ speakers seamlessly:
        - 1 speaker: delegates to single-speaker synthesis.
        - 2 speakers: uses native MultiSpeakerVoiceConfig in a single request.
        - 3+ speakers (or if native multi-speaker rejects >2 speakers): synthesizes turn-by-turn
          and stitches the 24kHz PCM audio frames into a single seamless WAV file.
        """
        valid_turns = [t for t in turns if t.get("text", "").strip()]
        if not valid_turns:
            raise ValueError("All dialogue turns were empty.")

        unique_speakers = []
        for t in valid_turns:
            s = t.get("speaker", "Speaker").strip()
            if s not in unique_speakers:
                unique_speakers.append(s)

        # Case 1: Only 1 speaker in script
        if len(unique_speakers) == 1:
            spk = unique_speakers[0]
            voice = speaker_voice_map.get(spk, "Kore")
            combined_text = " ".join(t["text"].strip() for t in valid_turns)
            first_style = next((t.get("style", "").strip() for t in valid_turns if t.get("style", "").strip()), None)
            return self._synthesize_single_via_generate_content(
                client=client,
                model=model,
                text=combined_text,
                voice=voice,
                style=first_style
            )

        # Case 2: 2 speakers (or try native multi_speaker_voice_config first)
        if len(unique_speakers) == 2:
            dialogue_lines = []
            style_hints = []
            for t in valid_turns:
                spk = t.get("speaker", "Speaker").strip()
                txt = t.get("text", "").strip()
                sty = t.get("style", "").strip()
                dialogue_lines.append(f"{spk}: {txt}")
                if sty:
                    style_hints.append(f"{spk} speaks in a {sty} tone")

            header = "TTS the following conversation"
            if style_hints:
                # Deduplicate style hints while preserving order
                unique_hints = list(dict.fromkeys(style_hints))
                header += " (" + "; ".join(unique_hints) + ")"
            prompt_text = f"{header}:\n" + "\n".join(dialogue_lines)

            speaker_configs = []
            for spk in unique_speakers:
                raw_voice = speaker_voice_map.get(spk, "Kore")
                resolved_voice, _ = self._resolve_voice_and_style(raw_voice, None)
                speaker_configs.append({
                    "speaker": spk,
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": resolved_voice
                        }
                    }
                })

            gen_config = {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "multi_speaker_voice_config": {
                        "speaker_voice_configs": speaker_configs
                    }
                }
            }

            response = client.models.generate_content(
                model=model,
                contents=prompt_text,
                config=gen_config
            )

            candidates = getattr(response, "candidates", None) or []
            for cand in candidates:
                content = getattr(cand, "content", None)
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and getattr(inline_data, "data", None):
                        raw_audio = self._decode_inline_audio(inline_data.data)
                        if raw_audio:
                            return self._ensure_wav_bytes(raw_audio)

        # Case 3: 3+ speakers (stitch each turn's 24kHz PCM seamlessly)
        combined_pcm = bytearray()
        sample_rate = 24000
        channels = 1
        sampwidth = 2
        # 120ms natural conversational pause between speakers
        pause_bytes = b"\x00" * int(sample_rate * channels * sampwidth * 0.12)

        for idx, t in enumerate(valid_turns):
            spk = t.get("speaker", "Speaker").strip()
            txt = t.get("text", "").strip()
            sty = t.get("style", "").strip() or None
            voice = speaker_voice_map.get(spk, "Kore")

            turn_wav = self._synthesize_single_via_generate_content(
                client=client,
                model=model,
                text=txt,
                voice=voice,
                style=sty
            )
            pcm_frames, sample_rate, channels, sampwidth = self._extract_pcm_frames(turn_wav)
            if idx > 0 and combined_pcm:
                combined_pcm.extend(pause_bytes)
            combined_pcm.extend(pcm_frames)

        if not combined_pcm:
            raise RuntimeError("Model did not return dialogue audio.")

        return self._ensure_wav_bytes(bytes(combined_pcm), sample_rate=sample_rate, channels=channels, sampwidth=sampwidth)

    def synthesize_multi_speaker(
        self,
        turns: List[Dict[str, str]],
        speaker_voice_map: Dict[str, str],
        model: str = "gemini-2.5-flash-preview-tts",
        output_filepath: Optional[str] = None
    ) -> Tuple[bytes, str, float]:
        """
        Synthesizes multi-speaker dialogue with automatic model fallback on 404.
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

        start_time = time.time()
        candidates = self._get_candidate_models(model, client)
        last_error: Optional[Exception] = None
        wav_bytes: bytes = b""
        used_model = model

        for cand_model in candidates:
            if "3.8" in cand_model and hasattr(client, "interactions") and cand_model not in self._unavailable_interactions_models:
                try:
                    wav_bytes = self._synthesize_multi_via_interactions(
                        client=client,
                        model=cand_model,
                        turns=turns,
                        speaker_voice_map=speaker_voice_map
                    )
                    if wav_bytes:
                        used_model = cand_model
                        break
                except Exception as e_inter:
                    last_error = e_inter
                    self._unavailable_interactions_models.add(cand_model)

            try:
                wav_bytes = self._synthesize_multi_via_generate_content(
                    client=client,
                    model=cand_model,
                    turns=turns,
                    speaker_voice_map=speaker_voice_map
                )
                if wav_bytes:
                    used_model = cand_model
                    break
            except Exception as e_gen:
                last_error = e_gen
                if self._is_not_found_error(e_gen):
                    self._unavailable_models.add(cand_model)
                    continue
                else:
                    break

        if not wav_bytes:
            announcer.play_sound("error")
            err = tr("announce_multi_error", error=last_error or "Unknown dialogue synthesis error")
            announcer.announce(err)
            raise RuntimeError(err) from last_error

        self._last_working_model = used_model
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
        If the cloud Voices API (client.voices.create) is unavailable on the user's API tier,
        automatically falls back to creating a Studio Persona Voice and synthesizing a real
        sample preview via TTS so Voice Design works on all API keys.
        Returns: (voice_id, sample_audio_bytes, preview_filepath)
        """
        client = client_manager.get_client()

        announcer.play_sound("start")
        announcer.announce(tr("announce_designing_voice", name=display_name))

        voice_id = ""
        sample_bytes = b""
        preview_path = ""

        # 1. Try cloud Voices API first if available on client
        if hasattr(client, "voices"):
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
                voice_id = getattr(created_voice, "id", "")
                if getattr(created_voice, "sample_audio", None) and getattr(created_voice.sample_audio, "data", None):
                    sample_bytes = self._ensure_wav_bytes(self._decode_inline_audio(created_voice.sample_audio.data))
            except Exception as e:
                if not self._is_not_found_error(e) and not isinstance(e, AttributeError):
                    announcer.play_sound("error")
                    err = tr("announce_design_error", error=e)
                    announcer.announce(err)
                    raise RuntimeError(err) from e

        # 2. Universal Studio Persona Fallback (when voices.create returns 404 on standard AI Studio keys)
        if not voice_id:
            slug = re.sub(r"[^a-z0-9]+", "_", display_name.lower()).strip("_") or "persona"
            voice_id = f"persona_{slug}_{int(time.time()) % 100000}"

            g_lower = gender.strip().lower()
            if g_lower == "male":
                base_voice = "Charon"
            elif g_lower == "female":
                base_voice = "Kore"
            else:
                base_voice = "Zephyr"

            sample_prompt = f"Hello! I am {display_name}. This is a preview of my custom designed vocal persona."
            try:
                sample_bytes, preview_path, _ = self.synthesize_single_speaker(
                    text=sample_prompt,
                    voice=base_voice,
                    style=prompt_description,
                    model=model,
                    output_filepath=self._get_timestamped_filename(f"preview_{slug}")
                )
            except Exception as e:
                announcer.play_sound("error")
                err = tr("announce_design_error", error=e)
                announcer.announce(err)
                raise RuntimeError(err) from e
        else:
            if sample_bytes:
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
        """
        Queries the Gemini Extended Voice Library, or filters the studio voice catalog
        if the remote voices endpoint is unavailable on the user's API key tier.
        """
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

        if hasattr(client, "voices"):
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
                if not self._is_not_found_error(e) and not isinstance(e, AttributeError):
                    err = tr("announce_library_error", error=e)
                    announcer.announce(err)
                    raise RuntimeError(err) from e

        # Fallback: filter built-in 30 studio voices + user custom voices locally
        q = (search_query or "").strip().lower()
        g = (gender or "").strip().lower()
        results = []
        for v in PREBUILT_VOICES:
            if g and g != "all" and v.gender.lower() != g:
                continue
            haystack = f"{v.id} {v.display_name} {v.tone} {v.gender} {v.description}".lower()
            if q and q not in haystack:
                continue
            results.append({
                "id": v.id,
                "display_name": v.display_name,
                "language_code": language_code.strip() if (language_code and language_code.strip()) else v.language_code,
                "accent": "Studio",
                "gender": v.gender,
                "pitch": v.tone,
                "description": v.description
            })

        announcer.announce(tr("announce_found_voices", count=len(results)))
        return results


# Global TTS Engine instance
tts_engine = TTSEngine()
