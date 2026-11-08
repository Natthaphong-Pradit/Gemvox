import argparse
import sys
from gemvox.config import config
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.core.voice_catalog import PREBUILT_VOICES, find_voice
from gemvox.core.client import client_manager

def handle_speak(args):
    text = args.text
    voice = args.voice or config.get("default_voice", "Kore")
    style = args.style or config.get("default_style", "cheerful and friendly")
    model = args.model or config.get("default_model", "gemini-3.8-flash-tts")
    output = args.out

    print(f"Synthesizing text with Gemini 3.8 Flash TTS [Voice: {voice}, Model: {model}]...")
    wav_bytes, out_path, duration = tts_engine.synthesize_single_speaker(
        text=text,
        voice=voice,
        style=style,
        model=model,
        output_filepath=output
    )
    print(f"Generated successfully in {out_path} ({duration}s)")
    if args.play:
        print("Playing audio...")
        audio_player.play_wav_bytes(wav_bytes)
        import time
        while audio_player.is_playing:
            time.sleep(0.2)

def handle_dialogue(args):
    with open(args.file, "r", encoding="utf-8") as f:
        script = f.read()

    turns, speakers = tts_engine.parse_dialogue_script(script)
    print(f"Parsed {len(turns)} turns across {len(speakers)} speakers: {', '.join(speakers)}")

    speaker_voice_map = {}
    if args.speakers:
        for pair in args.speakers:
            if ":" in pair:
                s, v = pair.split(":", 1)
                speaker_voice_map[s.strip()] = v.strip()
    
    # Fill remaining speakers
    defaults = ["Puck", "Kore", "Zephyr", "Charon"]
    for i, s in enumerate(speakers):
        if s not in speaker_voice_map:
            speaker_voice_map[s] = defaults[i % len(defaults)]

    wav_bytes, out_path, duration = tts_engine.synthesize_multi_speaker(
        turns=turns,
        speaker_voice_map=speaker_voice_map,
        output_filepath=args.out
    )
    print(f"Dialogue generated successfully in {out_path} ({duration}s)")
    if args.play:
        audio_player.play_wav_bytes(wav_bytes)
        import time
        while audio_player.is_playing:
            time.sleep(0.2)

def handle_voices(args):
    if args.search:
        print(f"Searching Extended Voice Library for '{args.search}'...")
        results = tts_engine.search_voice_library(search_query=args.search)
        for v in results:
            print(f"{v['id']:<15} | {v['display_name']} ({v.get('gender','')}, {v.get('language_code','')}): {v.get('description','')}")
    else:
        print("Featured 30 Gemini Studio Voices:")
        for v in PREBUILT_VOICES:
            print(f"{v.id:<15} | Tone: {v.tone:<12} | Gender: {v.gender:<8} | {v.description}")

def handle_design(args):
    name = args.name
    prompt = args.prompt
    gender = args.gender or "neutral"
    lang = args.lang or "en-US"

    print(f"Designing custom voice '{name}'...")
    voice_id, sample_bytes, preview_path = tts_engine.design_voice(
        display_name=name,
        prompt_description=prompt,
        gender=gender,
        language_code=lang
    )
    print(f"Voice created successfully!")
    print(f"Assigned Voice ID: {voice_id}")
    if preview_path:
        print(f"Preview saved to: {preview_path}")

def handle_update(args):
    from gemvox.core.updater import REPO_URL, check_for_updates, download_and_install_update
    print(f"Checking GitHub repository ({REPO_URL}) for updates...")
    info = check_for_updates()
    if info.error:
        print(f"Error checking for updates: {info.error}")
        return

    print(f"Current Version : v{info.current_version}")
    print(f"Latest Version  : v{info.latest_version}")
    print(f"Install Mode    : {info.install_mode}")
    print(f"Update Package  : {info.asset_name}")

    if not info.is_newer and not getattr(args, "force", False):
        print("\nGemvox is already up to date! (Use --force to reinstall current version)")
        return

    if getattr(args, "check_only", False):
        return

    print(f"\nDownloading and installing {info.asset_name} from GitHub...")
    last_pct = -1
    def _cb(pct: int, stage: str):
        nonlocal last_pct
        step = (pct // 10) * 10
        if step > last_pct:
            last_pct = step
            print(f"  [{pct:3d}%] {stage}")

    ok, msg = download_and_install_update(info, progress_callback=_cb, relaunch=False)
    if ok:
        print(f"\nSUCCESS: {msg}")
    else:
        print(f"\nERROR: {msg}")

def parse_cli_args(args=None):
    parser = argparse.ArgumentParser(
        prog="gemvox",
        description="Gemvox: Accessible Gemini 3.8 Flash TTS Client"
    )
    parser.add_argument("--gui", action="store_true", help="Launch accessible graphical user interface (default)")
    parser.add_argument("--cli", action="store_true", help="Launch interactive accessible terminal menu")

    subparsers = parser.add_subparsers(dest="command", help="Direct commands")

    # Speak command
    p_speak = subparsers.add_parser("speak", help="Synthesize text to speech")
    p_speak.add_argument("text", help="Text to speak")
    p_speak.add_argument("--voice", "-v", help="Voice name or ID (e.g. Kore, Puck)")
    p_speak.add_argument("--style", "-s", help="Delivery style (e.g. 'cheerful and friendly')")
    p_speak.add_argument("--model", "-m", help="Gemini TTS model code")
    p_speak.add_argument("--out", "-o", help="Output WAV path")
    p_speak.add_argument("--play", "-p", action="store_true", help="Play immediately after generating")

    # Dialogue command
    p_dial = subparsers.add_parser("dialogue", help="Synthesize multi-speaker dialogue script")
    p_dial.add_argument("file", help="Script file path")
    p_dial.add_argument("--speakers", nargs="*", help="Speaker voice pairs (e.g. Joe:Puck Jane:Kore)")
    p_dial.add_argument("--out", "-o", help="Output WAV path")
    p_dial.add_argument("--play", "-p", action="store_true", help="Play immediately")

    # Voices command
    p_voices = subparsers.add_parser("voices", help="List or search voices")
    p_voices.add_argument("--search", "-s", help="Search keyword in Extended Voice Library")

    # Design command
    p_design = subparsers.add_parser("design", help="Design custom voice from natural language prompt")
    p_design.add_argument("name", help="Voice display name")
    p_design.add_argument("--prompt", "-p", required=True, help="Description prompt for the persona")
    p_design.add_argument("--gender", "-g", choices=["male", "female", "neutral"], help="Gender presentation")
    p_design.add_argument("--lang", "-l", default="en-US", help="Language code (e.g. en-US, en-GB)")

    # Update command
    p_update = subparsers.add_parser("update", help="Check for updates and auto-install directly from GitHub")
    p_update.add_argument("--check-only", action="store_true", help="Only check for updates without installing")
    p_update.add_argument("--force", "-f", action="store_true", help="Force reinstall even if already on latest version")

    parsed = parser.parse_args(args)
    return parser, parsed
