# Campaign Video: "We Built This Place. Let's Protect It."
# 30 seconds · 5 clips · Minimax Hailuo 2.3 (Text-to-Video)
# 
# Run this script once MINIMAX_API_KEY is set:
#   export MINIMAX_API_KEY="your-key-here"
#   python3 generate-video.py

import json, os, time, requests, subprocess

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_URL = "https://api.minimax.chat/v1"
MODEL = "hailuo-2.3"  # Text-to-Video 

# ============================================================
# STORYBOARD — 5 clips × 6 seconds = 30 seconds
# ============================================================
SCENES = [
    {
        "title": "Dawn Over the Foothills",
        "duration_sec": 6,
        "prompt": "Aerial drone shot of the Colorado Rocky Mountain foothills at dawn, golden sunlight breaking through mist over pine forests and red rock formations, cinematic 24fps, warm golden tones, emotional and majestic atmosphere, photorealistic, highly detailed",
        "narration": "Decades ago, people came here because they believed a different way was possible."
    },
    {
        "title": "The Dark Smokestack",
        "duration_sec": 6,
        "prompt": "Cinematic slow push-in shot of a large industrial cement plant with a tall smokestack emitting white smoke against a clear blue sky, set against a backdrop of beautiful Colorado mountains, contrast between nature and industry, photorealistic, 24fps, documentary style",
        "narration": "But while we built this community, a coal-fired plant ran in our backyard. 1969 standards. 55 years of emissions."
    },
    {
        "title": "Trucks on Highway 66",
        "duration_sec": 6,
        "prompt": "Large dump trucks driving in succession on a rural two-lane highway through a small Colorado mountain town, dust rising, trucks passing through a quaint downtown area with storefronts, motion blur, handheld documentary feel, 24fps, photorealistic",
        "narration": "Truck traffic jumped 17x. Our kids breathe this air. Our neighbors sit in this dust."
    },
    {
        "title": "The People / The Evidence",
        "duration_sec": 6,
        "prompt": "Montage: hands flipping through legal documents on a wooden desk with mountain view window, a person studying data on a laptop showing charts and graphs, a community meeting where citizens raise their hands, warm lighting, documentary style, 24fps, photorealistic",
        "narration": "But we did the work. The scientists measured. The watchdogs tracked. The attorneys built the case. The evidence is public."
    },
    {
        "title": "Board of Adjustment / Call to Action",
        "duration_sec": 6,
        "prompt": "Exterior shot of a classic stone government building with Colorado mountain peaks visible in background, dramatic clouds parting to reveal golden sunlight streaming down, hopeful and inspiring atmosphere, cinematic 24fps, wide angle, photorealistic",
        "narration": "The Board of Adjustment hearing is our moment. We need you to show up one more time. Because if not us, who? And if not now, when?",
        "overlay": "Expect Better for Boulder County"
    }
]

# ============================================================
# VIDEO GENERATION (Minimax Hailuo 2.3 Text-to-Video API)
# ============================================================

def generate_clip(scene, clip_num):
    """Generate a single video clip from a text prompt."""
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "prompt": scene["prompt"],
        "duration_seconds": scene["duration_sec"],
        "resolution": "1080p",  # or "720p" for faster/cheaper
        "fps": 24,
        "cfg_scale": 7.0,
        "seed": clip_num * 42  # deterministic seeds for reproducibility
    }
    
    print(f"\n--- Generating Clip {clip_num}: {scene['title']} ---")
    print(f"  Prompt: {scene['prompt'][:80]}...")
    print(f"  Narration: {scene['narration']}")
    
    # Submit the generation task
    resp = requests.post(f"{BASE_URL}/video/generate", headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code} - {resp.text}")
        return None
    
    task_id = resp.json().get("task_id")
    print(f"  Task ID: {task_id}")
    
    # Poll until complete (typically 3-10 minutes per clip)
    while True:
        status_resp = requests.get(
            f"{BASE_URL}/video/status/{task_id}",
            headers=headers
        )
        status_data = status_resp.json()
        status = status_data.get("status", "unknown")
        
        if status == "completed":
            video_url = status_data.get("video_url", "")
            print(f"  COMPLETED: {video_url}")
            return video_url
        elif status == "failed":
            print(f"  FAILED: {status_data.get('error', 'unknown error')}")
            return None
        else:
            print(f"  Status: {status} ... waiting 30s")
            time.sleep(30)


def download_clip(url, output_path):
    """Download a generated clip."""
    if not url:
        return False
    resp = requests.get(url, stream=True)
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  Downloaded to: {output_path}")
    return True


def stitch_video(clip_paths, output_path):
    """Use ffmpeg to concatenate clips with crossfade transitions."""
    # Create concat file for ffmpeg
    concat_file = "/tmp/concat_list.txt"
    with open(concat_file, "w") as f:
        for path in clip_paths:
            f.write(f"file '{path}'\n")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"\n=== FINAL VIDEO: {output_path} ===")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    if not MINIMAX_API_KEY:
        print("ERROR: Set MINIMAX_API_KEY environment variable first")
        print("  export MINIMAX_API_KEY='your-key-here'")
        exit(1)
    
    output_dir = "/opt/data/cemex-content/new-site/resources"
    os.makedirs(output_dir, exist_ok=True)
    
    clips = []
    for i, scene in enumerate(SCENES, 1):
        url = generate_clip(scene, i)
        if url:
            clip_path = os.path.join(output_dir, f"clip-{i:02d}.mp4")
            download_clip(url, clip_path)
            clips.append(clip_path)
    
    if len(clips) == len(SCENES):
        final_video = os.path.join(output_dir, "campaign-video-30s.mp4")
        stitch_video(clips, final_video)
        print(f"\nAll done! Video ready at: {final_video}")
        print(f"Embed in site as: resources/campaign-video-30s.mp4")
    else:
        print(f"\nGenerated {len(clips)}/{len(SCENES)} clips. Some may need retrying.")