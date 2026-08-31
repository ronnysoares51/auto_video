# 🎨 Custom Assets for Your Website / Niche Videos

Place your custom branding, screen recordings, website screenshots, and audio assets in this folder to make your AI videos 100% original and branded for your website!

---

## 📁 Folder Structure

* **`videos/`**: Drop your `.mp4` / `.mov` / `.webm` video clips here (e.g., website UI screen recordings, animated feature demos, product walkthroughs).
* **`images/`**: Drop your `.png` / `.jpg` screenshots, website mockups, and logos here. The video maker will automatically convert them into video scenes matching your narration length.
* **`music/`**: Drop your `.mp3` background music tracks here.

---

## 💡 How the AI Video Maker Uses Your Assets

1. **Exact File Matching:**
   In your scene script, specify `"asset": "my_website_demo.mp4"` or `"asset": "dashboard_screenshot.png"`.

2. **Automatic Keyword Matching:**
   If you have a file named `resume_builder.mp4`, and Gemini or your script generates the search term `["resume", "builder"]`, the video maker will automatically pick your local asset instead of generic stock footage!

3. **Fallback to Pexels:**
   If no matching custom asset is found, it seamlessly falls back to Pexels stock video footage.
