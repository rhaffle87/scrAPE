import io
import logging

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

from captcha.captcha_solvers.base import CaptchaSolverProvider

LOGGER = logging.getLogger(__name__)

class FreeAudioCaptchaProvider(CaptchaSolverProvider):
    """
    A completely free, local CAPTCHA solver that uses Google's free Speech-to-Text API 
    via the SpeechRecognition library to transcribe audio challenges.
    """
    def __init__(self):
        self._is_available = sr is not None and AudioSegment is not None

    def is_available(self) -> bool:
        return self._is_available

    def solve_audio(self, audio_bytes: bytes, file_ext: str = "mp3") -> str | None:
        """Transcribes the audio bytes and returns the text."""
        if not self.is_available():
            LOGGER.error("SpeechRecognition or pydub is not installed.")
            return None

        try:
            audio_io = io.BytesIO(audio_bytes)
            
            # Convert to WAV in memory since SpeechRecognition needs WAV/AIFF/FLAC
            if file_ext.lower() != "wav":
                sound = AudioSegment.from_file(audio_io, format=file_ext.lower().replace(".", ""))  # type: ignore
                wav_io = io.BytesIO()
                sound.export(wav_io, format="wav")
                wav_io.seek(0)
                audio_io = wav_io

            recognizer = sr.Recognizer()  # type: ignore
            with sr.AudioFile(audio_io) as source:  # type: ignore
                audio_data = recognizer.record(source)
            
            # Google's STT API (free tier)
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:  # type: ignore
            LOGGER.warning("FreeAudioCaptchaProvider: Google STT could not understand audio")
            return None
        except sr.RequestError as e:  # type: ignore
            LOGGER.warning(f"FreeAudioCaptchaProvider: STT Request Error: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"FreeAudioCaptchaProvider error: {e}")
            return None

    def solve_turnstile(self, website_url: str, website_key: str, timeout: int = 60, proxy: str | None = None, user_agent: str | None = None) -> str | None:
        """Not supported via Audio. Handled directly by browser clicker."""
        return None

    def solve_recaptcha(self, website_url: str, website_key: str, timeout: int = 60, proxy: str | None = None, user_agent: str | None = None) -> str | None:
        """Not supported via token. Audio is solved locally in the browser."""
        return None

    def solve_hcaptcha(self, website_url: str, website_key: str, timeout: int = 60, proxy: str | None = None, user_agent: str | None = None) -> str | None:
        """Not supported via token. Audio is solved locally in the browser."""
        return None
