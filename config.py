"""
Central Configuration File for End-to-End Automation.
Controls Loop Counts, Target URLs, Timeouts, and CSS/XPath Selectors.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# ==============================================================================
# 1. BASE DIRECTORIES & FILE PATHS
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
SCREENSHOTS_DIR = LOGS_DIR / "screenshots"
DOWNLOADS_DIR = BASE_DIR / "downloads"
EXTENSIONS_DIR = BASE_DIR / "extensions"
USER_DATA_DIR = BASE_DIR / "browser_profile"
CUSTOM_ASSETS_DIR = BASE_DIR / "custom_assets"
SCENES_DIR = DOWNLOADS_DIR / "scenes"

# Ensure all essential directories exist
for directory in [LOGS_DIR, SCREENSHOTS_DIR, DOWNLOADS_DIR, EXTENSIONS_DIR, USER_DATA_DIR, CUSTOM_ASSETS_DIR, SCENES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
for sub in ["videos", "images", "music"]:
    (CUSTOM_ASSETS_DIR / sub).mkdir(parents=True, exist_ok=True)

# Path to unpacked uBlock Origin Chromium extension
UBLOCK_PATH = EXTENSIONS_DIR / "ublock_origin"

# ==============================================================================
# 2. PIPELINE SETTINGS
# ==============================================================================
# How many full cycles (Gemini -> Google Flow -> TikTok) to execute in one run
LOOP_COUNT = int(os.getenv("LOOP_COUNT", "1"))


# Maximum retries per step if an error occurs
MAX_RETRIES_PER_STEP = 3

# Headed mode so you can visually monitor actions and handle initial manual logins
HEADLESS = False

# Delay in milliseconds between Playwright actions for human-like speed
SLOW_MO = 50

# Default navigation / element timeout in milliseconds
BROWSER_TIMEOUT_MS = 60000
VIEWPORT = {"width": 1440, "height": 900}

# Telegram Notification Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ==============================================================================
# 3. TARGET PLATFORM URLS & SERVICES
# ==============================================================================
GEMINI_URL = "https://gemini.google.com/app"
FLOW_URL = os.getenv("FLOW_URL", "https://labs.google/flow")
TIKTOK_UPLOAD_URL = "https://www.tiktok.com/creator-center/upload?from=webapp"

# Short Video Maker REST API (Kokoro TTS + Whisper + Pexels + Remotion)
SHORT_VIDEO_MAKER_URL = os.getenv("SHORT_VIDEO_MAKER_URL", "http://localhost:3123")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Target Website & Marketing Configurations
TARGET_WEBSITE_NAME = os.getenv("TARGET_WEBSITE_NAME", "WebResume.live")
TARGET_WEBSITE_URL = os.getenv("TARGET_WEBSITE_URL", "https://webresume.live")
TARGET_WEBSITE_FEATURES = os.getenv(
    "TARGET_WEBSITE_FEATURES",
    "148+ interactive modern resume templates, AI-generated cover letters and resumes, 7-day free trial, interactive personal website link"
)

# Short Video Maker Video Styling Defaults
SHORT_VIDEO_VOICE = os.getenv("SHORT_VIDEO_VOICE", "af_heart")  # af_heart, af_bella, am_adam, am_michael, etc.
SHORT_VIDEO_MUSIC = os.getenv("SHORT_VIDEO_MUSIC", "chill")      # chill, happy, exciting, dark, hopeful, etc.
SHORT_VIDEO_ORIENTATION = os.getenv("SHORT_VIDEO_ORIENTATION", "portrait") # portrait (9:16) or landscape (16:9)
SHORT_VIDEO_CAPTION_POS = os.getenv("SHORT_VIDEO_CAPTION_POS", "bottom")   # bottom, center, top
SHORT_VIDEO_CAPTION_BG = os.getenv("SHORT_VIDEO_CAPTION_BG", "blue")       # blue, black, yellow, etc.

# ==============================================================================
# 4. GEMINI PROMPT TEMPLATES
# ==============================================================================
# 5 to 6-Scene Storytelling Template with Strict Malaysian Demographic Targeting
MALAYSIAN_STORY_PROMPT_TEMPLATE = (
    f"Act as an Elite Video Director, Storyteller, and TikTok Viral Marketing Strategist targeting the Malaysian market.\n"
    f"Write a high-converting, viral 5 to 6-scene TikTok/Reels video story promoting '{TARGET_WEBSITE_NAME}' ({TARGET_WEBSITE_URL}).\n"
    f"Product Features: {TARGET_WEBSITE_FEATURES}.\n\n"
    f"=== CRITICAL DEMOGRAPHIC & ETHNICITY RULES (MALAYSIA FOCUS) ===\n"
    f"1. ALL characters, actors, job applicants, and professionals in the visual search terms and prompts MUST explicitly feature MALAYSIAN / Southeast Asian ethnicity (e.g. 'young Malaysian professional woman', 'Malaysian tech engineer in Kuala Lumpur', 'Southeast Asian job seeker', 'Malaysian graduate in modern office').\n"
    f"2. All visual settings must reflect modern Malaysian urban workspaces (e.g. 'Kuala Lumpur corporate office', 'Bangsar modern coworking space', 'high-tech Malaysian laptop setup').\n\n"
    f"=== 5 TO 6 SCENE COHESIVE STORY STRUCTURE ===\n"
    f"• Scene 1 [The Hook]: Intense pain point of sending outdated paper resumes in Malaysia.\n"
    f"• Scene 2 [The Rejection]: Malaysian recruiters discarding boring PDF resumes in 6 seconds.\n"
    f"• Scene 3 [The Solution]: Introducing {TARGET_WEBSITE_NAME} — transforming boring CVs into interactive, dynamic website portfolios.\n"
    f"• Scene 4 [The Feature Showcase]: Showing 148+ live interactive templates and instant AI cover letters.\n"
    f"• Scene 5 [The Breakthrough]: Confident Malaysian professional landing dream job interviews.\n"
    f"• Scene 6 [The Call to Action]: 7-day free trial, interactive website link in bio.\n\n"
    f"=== STRICT OUTPUT RULES ===\n"
    f"Return ONLY valid JSON in this exact structure without markdown or explanation:\n"
    f'{{\n'
    f'  "caption": "Viral TikTok caption tailored for Malaysia with hashtags like #kerjamalaysia #jobsearchmy #kualalumpur #career #resume #tech",\n'
    f'  "scenes": [\n'
    f'    {{"scene_id": 1, "text": "<12-18 words spoken narration>", "searchTerms": ["Malaysian professional", "Kuala Lumpur office", "job interview"], "asset": "A_young_Malaysian_woman_wearin.mp4"}},\n'
    f'    {{"scene_id": 2, "text": "<12-18 words spoken narration>", "searchTerms": ["frustrated Malaysian worker", "paper resume desk", "office interview"], "asset": "Continuing_the_same_woman_now.mp4"}},\n'
    f'    {{"scene_id": 3, "text": "<12-18 words spoken narration>", "searchTerms": ["modern laptop website", "coding Kuala Lumpur", "interactive portfolio"], "asset": "Laptop_displaying_resume_templates_202608242030.mp4"}},\n'
    f'    {{"scene_id": 4, "text": "<12-18 words spoken narration>", "searchTerms": ["modern resume templates", "website design showcase", "interactive CV"], "asset": "065-terminal.png"}},\n'
    f'    {{"scene_id": 5, "text": "<12-18 words spoken narration>", "searchTerms": ["happy Malaysian professional", "successful job offer", "working remotely"], "asset": "güzel_bir_resume_yap_sevinsin.mp4"}},\n'
    f'    {{"scene_id": 6, "text": "<12-18 words spoken narration>", "searchTerms": ["Malaysian career growth", "success technology", "link in bio"], "asset": "148-classic-1.png"}}\n'
    f'  ]\n'
    f'}}'
)

# Multi-scene script template specifically for Short Video Maker (Custom Assets + Kokoro + Whisper)
SHORT_VIDEO_PROMPT_TEMPLATE = MALAYSIAN_STORY_PROMPT_TEMPLATE

# Legacy single-prompt template for Google Flow RPA
GEMINI_PROMPT_TEMPLATE = (
    f"Act as a viral TikTok strategist. Generate 1 dynamic video generation prompt "
    f"for a text-to-video AI model, and 1 catchy TikTok caption with hashtags for "
    f"a platform called {TARGET_WEBSITE_NAME}. The platform's features are: {TARGET_WEBSITE_FEATURES}. "
    f"Return ONLY valid JSON in this exact structure: "
    '{"prompt": "<video_prompt_here>", "caption": "<tiktok_caption_here>"}'
)

# ==============================================================================
# 5. UI SELECTORS & LOCATORS (EASY TO UPDATE IF WEBSITES CHANGE)
# ==============================================================================
SELECTORS = {
    # --------------------------------------------------------------------------
    # GEMINI WEB (https://gemini.google.com)
    # --------------------------------------------------------------------------
    "gemini": {
        # Check if user is logged into Google / Gemini
        "logged_in_indicators": [
            "a[aria-label*='Google Account']",
            "button[aria-label*='Google Account']",
            "img[src*='googleusercontent']",
            "div[class*='user-avatar']",
            "button[aria-label*='Account']",
            "bard-avatar-button",
        ],
        "login_button_indicators": [
            "a:has-text('Sign in')",
            "a:has-text('Oturum açın')",
            "button:has-text('Sign in')",
            "button:has-text('Oturum Aç')",
        ],
        # The prompt input container / textarea
        "prompt_input": (
            "rich-textarea p, "
            "div[contenteditable='true'][role='textbox'], "
            "div[aria-label*='Enter a prompt'], "
            "textarea[placeholder*='Enter a prompt'], "
            "div.ql-editor"
        ),
        # Send button
        "send_button": (
            "button[aria-label*='Send message' i], "
            "button[aria-label*='Mesaj gönder' i], "
            "button[aria-label*='Gönder' i], "
            "button[mattooltip*='Send' i], "
            "button.send-button, "
            "button.send-button-container, "
            "button:has(mat-icon:has-text('send')), "
            "button:has(svg.send-icon)"
        ),

        # Response containers (targets actual markdown response, bypassing thinking blocks)
        "response_container": (
            "model-response message-content .markdown, "
            "message-content .markdown, "
            "div.markdown, "
            "model-response .model-response-text, "
            "message-content, "
            "div.model-response-text"
        ),

        # Stop generating indicator (present only while streaming/typing)
        "generating_indicator": (
            "button[aria-label*='Stop response' i], "
            "button[aria-label*='Stop generating' i], "
            "button[aria-label*='Yanıtı durdur' i], "
            "button[aria-label*='Durdur' i], "
            "div.sparkle-generating"
        ),
        # Completion Action Bar Indicators (appear only when response is 100% finished)
        "completion_indicators": (
            "button[aria-label*='Good response' i], "
            "button[aria-label*='İyi yanıt' i], "
            "button[aria-label*='Copy' i], "
            "button[aria-label*='Kopyala' i], "
            "button[aria-label*='Share' i], "
            "button[aria-label*='Paylaş' i], "
            "button[aria-label*='Modify response' i], "
            "button[mattooltip*='Copy' i], "
            "div.response-actions, "
            "div.message-actions"
        ),
    },


    # --------------------------------------------------------------------------
    # GOOGLE FLOW / AI VIDEO GENERATOR
    # --------------------------------------------------------------------------
    "flow": {
        "logged_in_indicators": [
            "a[aria-label*='Google Account' i]",
            "button[aria-label*='Google Account' i]",
            "img[src*='googleusercontent']",
            "button[aria-label*='Account' i]",
            "img[alt*='avatar' i]",
            "img[alt*='profile' i]",
            "div[class*='user-profile']",
            "div[class*='user-avatar']",
            "button[aria-haspopup='menu']",
            "a[href*='/logout']"
        ],
        "login_button_indicators": [
            "button:has-text('Sign in')",
            "a:has-text('Sign in')",
            "button:has-text('Oturum aç')",
            "a:has-text('Oturum aç')"
        ],

        # Button to open workspace/create new project from dashboard
        "new_project_button": (
            "button:has-text('New project'), "
            "button:has-text('New Project'), "
            "button:has-text('Create'), "
            "button:has-text('New video'), "
            "button:has-text('Yeni proje'), "
            "button:has-text('Yeni Proje'), "
            "button:has-text('+'), "
            "a[href*='/project/new'], "
            "a[href*='/create'], "
            "[data-testid*='new-project'], "
            "[aria-label*='New project' i], "
            "[aria-label*='Create' i]"
        ),
        # Main video description prompt input box
        "prompt_input": (
            "textarea[placeholder*='Ne oluşturmak istiyorsunuz' i], "
            "textarea[placeholder*='Describe' i], "
            "textarea[placeholder*='prompt' i], "
            "textarea[placeholder*='video' i], "
            "div[contenteditable='true'][aria-label*='prompt' i], "
            "div[contenteditable='true'][placeholder*='Ne oluşturmak' i], "
            "div[contenteditable='true'][data-placeholder*='Describe' i], "
            "textarea:visible, "
            "div[contenteditable='true']:visible"
        ),
        "generate_button": (
            "button:has-text('arrow_forward Oluştur'), "
            "button:has-text('Oluştur'), "
            "button:has-text('Generate'), "
            "button:has-text('Create'), "
            "button[aria-label*='Oluştur' i], "
            "button[aria-label*='Generate' i]"
        ),
        "more_options_button": (
            "button:has-text('more_vert Diğer'), "
            "button:has-text('Diğer'), "
            "button:has-text('more_vert'), "
            "[aria-label*='Diğer' i], "
            "[aria-label*='More' i]"
        ),
        "download_menuitem": (
            "[role='menuitem']:has-text('download Projeyi indir'), "
            "[role='menuitem']:has-text('Projeyi indir'), "
            "[role='menuitem']:has-text('download'), "
            "button:has-text('Projeyi indir'), "
            "a[download]"
        ),
    },




    # --------------------------------------------------------------------------
    # TIKTOK CREATOR CENTER (https://www.tiktok.com/creator-center/upload)
    # --------------------------------------------------------------------------
    "tiktok": {
        "logged_in_indicators": [
            "input[type='file']",
            "button:has-text('Select video')",
            "button:has-text('Select files')",
            "button:has-text('Dosya seçin')",
            "div:has-text('Select video to upload')",
            "div:has-text('Yüklenecek videoyu seçin')",
            "[data-e2e*='upload']",
            "[data-e2e='profile-icon']",
            "img[alt*='avatar']",
            "img[alt*='profile']",
            "div[class*='avatar']",
            "div[class*='user-avatar']",
            "a[href*='/@']",
            "[aria-label*='Profile']",
            "[aria-label*='Hesap']"
        ],
        "login_button_indicators": [
            "button:has-text('Log in')",
            "button:has-text('Giriş yap')",
            "a:has-text('Log in')",
            "a:has-text('Giriş Yap')",
            "#header-login-button",
        ],
        "file_input": "input[type='file'][accept*='video']",
        "caption_input": (
            "div[contenteditable='true'][role='combobox'], "
            "div[data-placeholder*='caption'], "
            "div.DraftEditor-editorContainer, "
            "div[class*='editor-container']"
        ),
        "post_button": (
            "button:has-text('Post'), "
            "button:has-text('Yayınla'), "
            "button[data-e2e='post_video_button']"
        ),
        "upload_complete_indicator": (
            "div:has-text('Uploaded'), "
            "div:has-text('Yüklendi'), "
            "div[class*='preview-wrapper'] video, "
            "div:has-text('Change video')"
        ),
    }
}
