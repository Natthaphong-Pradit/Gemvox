import os
import sys
from gemvox.config import config
from gemvox.accessibility import announcer
from gemvox.core.voice_catalog import (
    PREBUILT_VOICES,
    STYLE_PRESETS,
    INLINE_VOCAL_TAGS,
    SUPPORTED_MODELS,
    get_all_voices,
    find_voice
)
from gemvox.core.tts_engine import tts_engine
try:
    from gemvox.core.client import client_manager
except ImportError:
    from gemvox.core import client_manager

def print_accessible_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def prompt_input(prompt_text: str, default: str = "") -> str:
    if default:
        p = f"{prompt_text} [Default: {default}]: "
    else:
        p = f"{prompt_text}: "
    val = input(p).strip()
    return val if val else default

def cli_single_speaker():
    print_accessible_header("1. SINGLE-SPEAKER TEXT-TO-SPEECH")
    print("Tip: You can use inline vocal tags like <short pause>, <sigh>, <cough> directly in your text.")
    print("Available tags:", ", ".join([t["tag"] for t in INLINE_VOCAL_TAGS]))
    print()

    text = prompt_input("Enter text to speak")
    if not text:
        print("Cancelled: Text cannot be empty.")
        return

    # Choose voice
    def_voice = config.get("default_voice", "Kore")
    voice = prompt_input(f"Enter voice name or ID", default=def_voice)

    # Style
    def_style = config.get("default_style", "cheerful and friendly")
    print("\nSample styles: cheerful and friendly | calm and relaxed | whispered urgently | warm and enthusiastic")
    style = prompt_input("Enter delivery style instruction", default=def_style)

    # Model
    model = config.get("default_model", "gemini-3.8-flash-tts")

    print("\nGenerating speech with Gemini 3.8 Flash TTS...")
    try:
        wav_bytes, out_path, duration = tts_engine.synthesize_single_speaker(
            text=text,
            voice=voice,
            style=style,
            model=model
        )
        print(f"\nSUCCESS: Speech generated successfully!")
        print(f"Duration: {duration} seconds")
        print(f"Saved to: {out_path}")
        
        play = prompt_input("Play audio now? (y/n)", default="y")
        if play.lower().startswith("y"):
            print("Playing audio... (Press Ctrl+C if you need to return immediately)")
            audio_player.play_wav_bytes(wav_bytes)
            # Wait for playback to complete
            import time
            while audio_player.is_playing:
                time.sleep(0.2)
            print("Playback finished.")
    except Exception as e:
        print(f"Error: {e}")

def cli_multi_speaker():
    print_accessible_header("2. MULTI-SPEAKER DIALOGUE")
    print("Enter your dialogue script line by line in the format:")
    print("  Speaker: Text to say [optional style]")
    print("Example:")
    print("  Joe: Good morning Jane! [cheerful]")
    print("  Jane: Hello Joe, wonderful to see you. [calm]")
    print("Type 'DONE' on a new line when finished (or 'SAMPLE' to load demo script):\n")

    lines = []
    while True:
        line = input("> ").strip()
        if line.upper() == "DONE":
            break
        elif line.upper() == "SAMPLE":
            sample_script = (
                "Joe: Welcome to Gemvox dialogue mode! [cheerful and friendly]\n"
                "Jane: It is great to hear both of us in a single audio track. [calm and relaxed]"
            )
            print(f"Loaded sample:\n{sample_script}")
            lines = sample_script.splitlines()
            break
        elif line:
            lines.append(line)

    if not lines:
        print("Cancelled: No dialogue provided.")
        return

    script_text = "\n".join(lines)
    turns, speakers = tts_engine.parse_dialogue_script(script_text)
    print(f"\nDiscovered {len(speakers)} speakers: {', '.join(speakers)}")

    speaker_voice_map = {}
    default_voices = ["Puck", "Kore", "Zephyr", "Charon", "Fenrir"]
    for idx, spk in enumerate(speakers):
        def_v = default_voices[idx % len(default_voices)]
        v = prompt_input(f"Enter voice for '{spk}'", default=def_v)
        speaker_voice_map[spk] = v

    print("\nGenerating dialogue with Gemini 3.8 Flash TTS...")
    try:
        wav_bytes, out_path, duration = tts_engine.synthesize_multi_speaker(
            turns=turns,
            speaker_voice_map=speaker_voice_map
        )
        print(f"\nSUCCESS: Dialogue generated successfully!")
        print(f"Duration: {duration} seconds")
        print(f"Saved to: {out_path}")

        play = prompt_input("Play audio now? (y/n)", default="y")
        if play.lower().startswith("y"):
            print("Playing dialogue...")
            audio_player.play_wav_bytes(wav_bytes)
            import time
            while audio_player.is_playing:
                time.sleep(0.2)
            print("Playback finished.")
    except Exception as e:
        print(f"Error: {e}")

def cli_voice_design():
    print_accessible_header("3. VOICE DESIGN STUDIO")
    print("Describe a character to synthesize a custom persistent voice ID.")
    name = prompt_input("Voice Display Name", default="Gentle Storyteller")
    gender = prompt_input("Gender (male/female/neutral)", default="female")
    lang = prompt_input("Language code (e.g. en-US, en-GB)", default="en-US")
    prompt = prompt_input("Persona description prompt", default="A soft, gentle bedtime storyteller speaking in a calm, soothing cadence.")

    print("\nDesigning voice with Gemini...")
    try:
        voice_id, sample_bytes, preview_path = tts_engine.design_voice(
            display_name=name,
            prompt_description=prompt,
            gender=gender,
            language_code=lang
        )
        print(f"\nSUCCESS: Voice created successfully!")
        print(f"Assigned Voice ID: {voice_id}")
        if preview_path:
            print(f"Preview saved to: {preview_path}")
            play = prompt_input("Play sample audio preview? (y/n)", default="y")
            if play.lower().startswith("y"):
                audio_player.play_wav_bytes(sample_bytes)
                import time
                while audio_player.is_playing:
                    time.sleep(0.2)
        print(f"Tip: You can now use '{voice_id}' anywhere voice is requested.")
    except Exception as e:
        print(f"Error: {e}")

def cli_browse_voices():
    print_accessible_header("4. BROWSE 30 FEATURED STUDIO VOICES")
    for v in PREBUILT_VOICES:
        print(f"  * {v.id:<14} | Tone: {v.tone:<12} | Gender: {v.gender:<8} | {v.description}")
    
    audition = prompt_input("\nEnter a voice name to audition (or press Enter to return)", default="")
    if audition:
        found = find_voice(audition)
        voice_id = found.id if found else audition
        print(f"Auditioning {voice_id}...")
        try:
            wav_bytes, _, _ = tts_engine.synthesize_single_speaker(
                text=f"Hello, I am {voice_id}. This is a preview of my voice in Gemvox.",
                voice=voice_id,
                style="natural and clear"
            )
            audio_player.play_wav_bytes(wav_bytes)
            import time
            while audio_player.is_playing:
                time.sleep(0.2)
        except Exception as e:
            print(f"Error: {e}")

def cli_settings():
    print_accessible_header("5. SETTINGS & CONFIGURATION")
    print(f"Current API Key: {'*' * 10 if config.api_key else 'NOT SET'}")
    print(f"Default Model: {config.get('default_model')}")
    print(f"Default Voice: {config.get('default_voice')}")
    print(f"Output Directory: {config.output_dir}")
    print(f"Spoken Announcements: {config.get('speech_announcements')}")
    print(f"Sound Cues: {config.get('sound_cues')}")

    print("\nOptions:")
    print("1. Set Gemini API Key")
    print("2. Test API Key Connection")
    print("3. Toggle Spoken Status Announcements")
    print("4. Toggle Sound Cues (Beeps)")
    print("5. Check for Updates & Auto-Install from GitHub")
    print("6. Return to Main Menu")

    choice = prompt_input("Select an option", default="6")
    if choice == "1":
        new_key = prompt_input("Enter new Gemini API Key")
        if new_key:
            config.api_key = new_key
            print("API Key saved.")
    elif choice == "2":
        print("Testing connection...")
        success, msg = client_manager.validate_key()
        print(f"Result: {msg}")
    elif choice == "3":
        curr = config.get("speech_announcements", True)
        config.set("speech_announcements", not curr)
        print(f"Spoken Announcements set to: {not curr}")
    elif choice == "4":
        curr = config.get("sound_cues", True)
        config.set("sound_cues", not curr)
        print(f"Sound Cues set to: {not curr}")
    elif choice == "5":
        from gemvox.core.updater import check_for_updates, download_and_install_update
        print("Checking GitHub repository (Natthaphong-Pradit/Gemvox) for updates...")
        info = check_for_updates()
        if info.error:
            print(f"Update check failed: {info.error}")
            return
        print(f"Current Version : v{info.current_version}")
        print(f"Latest Version  : v{info.latest_version}")
        print(f"Install Mode    : {info.install_mode}")
        if info.is_newer:
            ans = prompt_input(f"New version v{info.latest_version} available! Download and install now? (y/n)", default="y")
        else:
            ans = prompt_input(f"Already on latest version (v{info.current_version}). Reinstall anyway? (y/n)", default="n")
        if ans.lower().startswith("y"):
            ok, msg = download_and_install_update(info, relaunch=False)
            print(msg)

def run_interactive_cli():
    """Main loop of the accessible interactive CLI."""
    announcer.announce("Gemvox interactive console mode started.")
    while True:
        print_accessible_header("GEMVOX: ACCESSIBLE GEMINI 3.8 FLASH TTS (CLI)")
        print("1. Single-Speaker TTS (Speak text with styles and vocal tags)")
        print("2. Multi-Speaker Dialogue (Podcast, conversation, interview)")
        print("3. Voice Design Studio (Prompt custom vocal personas)")
        print("4. Browse 30 Studio Voices & Audition")
        print("5. Settings & API Key")
        print("6. Launch Accessible Graphical Interface (GUI)")
        print("7. Exit Gemvox")
        print("=" * 60)

        choice = prompt_input("Enter choice (1-7)", default="1")
        if choice == "1":
            cli_single_speaker()
        elif choice == "2":
            cli_multi_speaker()
        elif choice == "3":
            cli_voice_design()
        elif choice == "4":
            cli_browse_voices()
        elif choice == "5":
            cli_settings()
        elif choice == "6":
            import wx
            from gemvox.ui.main_window import MainWindow
            app = wx.App(False)
            frame = MainWindow()
            frame.Show()
            app.MainLoop()
            break
        elif choice == "7" or choice.lower() in ["exit", "q", "quit"]:
            print("Exiting Gemvox. Goodbye!")
            break
        else:
            print("Invalid option. Please choose between 1 and 7.")
