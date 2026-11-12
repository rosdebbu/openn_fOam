"""
Sector V Kolkata Internship Early-Warning Pipeline & Alert Tracker
Author: OpenZess Automation Team for Debjit Das (RA2411056010276)
Purpose: Scans for newly posted tech/software internships in Kolkata (Sector V / Salt Lake),
         tracks applicant counts (< 25 applicants = Early Applicant), and sends instant
         desktop notifications so you can be among the first applicants.
"""

import sys
import os
import re
import json
import time
import argparse
import subprocess
import requests
from bs4 import BeautifulSoup
from datetime import datetime

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

DEFAULT_KEYWORDS = [
    "software intern",
    "web development intern",
    "python intern",
    "frontend intern",
    "backend intern",
    "full stack intern",
    "internship Sector V",
    "data science intern",
    "machine learning intern",
    "trainee software engineer"
]

SEEN_JOBS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "seen_jobs.json")
OUTPUT_HTML_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "internship_tracker.html")
OUTPUT_JSON_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "latest_internships.json")

def send_windows_notification(title, message, url=None):
    """Fires a native Windows PowerShell toast or balloon notification."""
    try:
        ps_code = f"""
        [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = "{title.replace('"', '`"')}"
        $notify.BalloonTipText = "{message.replace('"', '`"')}"
        $notify.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
        $notify.Visible = $True
        $notify.ShowBalloonTip(10000)
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_code], capture_output=True, timeout=5)
    except Exception as e:
        print(f"[Warning] Could not trigger native toast: {e}")

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_jobs(seen_ids):
    os.makedirs(os.path.dirname(SEEN_JOBS_FILE), exist_ok=True)
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ids), f, indent=2)

def fetch_job_details(job_id, session):
    """Extracts applicant count and precise posted time from the job detail card."""
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = session.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            num_applicants_el = soup.find("span", class_="num-applicants__caption")
            posted_on_el = soup.find("span", class_="posted-time-ago__text")
            criteria_items = soup.find_all("li", class_="description__job-criteria-item")

            job_type = "Internship"
            for item in criteria_items:
                header = item.find("h3")
                val = item.find("span")
                if header and "employment type" in header.text.lower() and val:
                    job_type = val.text.strip()

            applicants_str = num_applicants_el.text.strip() if num_applicants_el else "Unknown"
            posted_str = posted_on_el.text.strip() if posted_on_el else "Recently"

            # Parse integer count if available
            m = re.search(r"(\d+)", applicants_str)
            applicant_count = int(m.group(1)) if m else None

            is_early = False
            if "first" in applicants_str.lower() or "be among" in applicants_str.lower():
                is_early = True
            elif applicant_count is not None and applicant_count <= 25:
                is_early = True
            elif "minute" in posted_str.lower() or "hour" in posted_str.lower():
                is_early = True

            return {
                "applicants_text": applicants_str,
                "applicant_count": applicant_count,
                "posted_text": posted_str,
                "job_type": job_type,
                "is_early": is_early
            }
    except Exception:
        pass
    return {
        "applicants_text": "N/A",
        "applicant_count": None,
        "posted_text": "Recently",
        "job_type": "Internship",
        "is_early": True
    }

def scan_internships(keywords=None, time_window="r604800", check_details=True, max_cards_per_kw=10):
    """
    Scans LinkedIn guest job listings for Kolkata / Sector V internships.
    time_window:
      'r86400'  -> Past 24 hours
      'r259200' -> Past 3 days
      'r604800' -> Past week
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    session = requests.Session()
    headers = {"User-Agent": USER_AGENT}
    discovered = []
    seen_ids = set()

    print(f"\n🔍 [Pipeline] Initiating scan for Sector V / Kolkata Tech Internships...")
    print(f"⏱️  Time Window Filter: {time_window} | Total Query Topics: {len(keywords)}")

    for kw in keywords:
        loc = "Kolkata, West Bengal, India"
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
            f"keywords={requests.utils.quote(kw)}&location={requests.utils.quote(loc)}&"
            f"f_TPR={time_window}&f_E=1&start=0"
        )
        try:
            resp = session.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("li")
            card_count = 0

            for card in cards:
                if card_count >= max_cards_per_kw:
                    break
                link_el = card.find("a", class_="base-card__full-link")
                if not link_el or "href" not in link_el.attrs:
                    continue

                raw_url = link_el["href"].split("?")[0]
                m = re.search(r"-(\d+)$", raw_url)
                job_id = m.group(1) if m else raw_url

                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title_el = card.find("h3", class_="base-search-card__title")
                comp_el = card.find("h4", class_="base-search-card__subtitle")
                loc_el = card.find("span", class_="job-search-card__location")
                time_el = card.find("time")

                title = title_el.text.strip() if title_el else "Intern"
                company = comp_el.text.strip() if comp_el else "Unknown Company"
                location = loc_el.text.strip() if loc_el else "Kolkata, WB"
                time_posted = time_el.text.strip() if time_el else "Recently"

                # Check if located in Sector V / Salt Lake / New Town
                is_sector_v = any(k in f"{title} {company} {location}".lower() for k in ["sector v", "sector 5", "salt lake", "saltlake", "new town", "newtown"])

                details = {"applicants_text": "N/A", "is_early": True, "posted_text": time_posted}
                if check_details:
                    details = fetch_job_details(job_id, session)

                discovered.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "is_sector_v": is_sector_v,
                    "time_posted": details.get("posted_text", time_posted),
                    "applicants": details.get("applicants_text", "N/A"),
                    "is_early": details.get("is_early", True),
                    "url": raw_url,
                    "scanned_at": datetime.now().isoformat()
                })
                card_count += 1
                time.sleep(0.3)

        except Exception as e:
            print(f"[!] Query '{kw}' error: {e}")

    # Prioritize: Sector V first, then early applicants (< 25 applicants / fresh hours), then date
    def sort_key(item):
        s_score = 0 if item["is_sector_v"] else 1
        e_score = 0 if item["is_early"] else 1
        return (s_score, e_score)

    discovered.sort(key=sort_key)
    return discovered

def generate_html_dashboard(jobs):
    """Generates a responsive live HTML dashboard."""
    os.makedirs(os.path.dirname(OUTPUT_HTML_FILE), exist_ok=True)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sector V Kolkata Internship Early Applicant Tracker</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }}
  h1 {{ font-size: 22px; margin: 0; color: #38bdf8; }}
  .badge-pulse {{ display: inline-block; background: #22c55e; color: #000; font-weight: 700; padding: 4px 10px; border-radius: 9999px; font-size: 12px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s, border-color 0.2s; }}
  .card:hover {{ border-color: #38bdf8; transform: translateY(-2px); }}
  .card.sector-v {{ border-left: 5px solid #38bdf8; }}
  .card.early-applicant {{ box-shadow: 0 0 15px rgba(34, 197, 94, 0.15); }}
  .role {{ font-size: 17px; font-weight: 600; color: #f1f5f9; margin-bottom: 6px; }}
  .company {{ font-size: 14px; color: #94a3b8; font-weight: 500; margin-bottom: 12px; }}
  .tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
  .tag {{ font-size: 11px; padding: 3px 8px; border-radius: 6px; background: #334155; color: #cbd5e1; }}
  .tag.early {{ background: #065f46; color: #34d399; font-weight: 600; }}
  .tag.sector5 {{ background: #1e3a8a; color: #93c5fd; font-weight: 600; }}
  .apply-btn {{ display: block; text-align: center; background: #2563eb; color: #fff; text-decoration: none; padding: 10px 16px; border-radius: 8px; font-weight: 600; font-size: 14px; transition: background 0.2s; }}
  .apply-btn:hover {{ background: #1d4ed8; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>🚀 Kolkata / Sector V Winter Internship Pipeline</h1>
      <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 0 0;">Prepared for Debjit Das (RA2411056010276) | Real-time early applicant tracker</p>
    </div>
    <div style="text-align: right;">
      <span class="badge-pulse">LIVE TRACKER</span>
      <div style="color: #64748b; font-size: 12px; margin-top: 4px;">Last scanned: {datetime.now().strftime('%d %b %Y, %I:%M %p')}</div>
    </div>
  </header>

  <div class="grid">
"""
    for job in jobs:
        sector_class = "sector-v" if job["is_sector_v"] else ""
        early_class = "early-applicant" if job["is_early"] else ""
        tag_sector = '<span class="tag sector5">📍 Sector V / Salt Lake</span>' if job["is_sector_v"] else f'<span class="tag">📍 {job["location"]}</span>'
        tag_early = f'<span class="tag early">🔥 {job["applicants"]}</span>' if job["is_early"] else f'<span class="tag">👥 {job["applicants"]}</span>'
        tag_time = f'<span class="tag">🕒 {job["time_posted"]}</span>'

        html += f"""
    <div class="card {sector_class} {early_class}">
      <div>
        <div class="role">{job["title"]}</div>
        <div class="company">{job["company"]}</div>
        <div class="tags">
          {tag_early}
          {tag_sector}
          {tag_time}
        </div>
      </div>
      <a href="{job["url"]}" target="_blank" class="apply-btn">⚡ Apply First (Direct Link) &rarr;</a>
    </div>
"""
    html += """
  </div>
</div>
</body>
</html>
"""
    with open(OUTPUT_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

def run_pipeline(watch=False, interval_min=15, time_window="r604800"):
    seen_ids = load_seen_jobs()
    print(f"[*] Previously indexed postings: {len(seen_ids)}")

    while True:
        jobs = scan_internships(time_window=time_window)
        new_jobs = []

        for job in jobs:
            if job["id"] not in seen_ids:
                new_jobs.append(job)
                seen_ids.add(job["id"])

        save_seen_jobs(seen_ids)

        # Save latest JSON and HTML
        os.makedirs(os.path.dirname(OUTPUT_JSON_FILE), exist_ok=True)
        with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)
        generate_html_dashboard(jobs)

        print("\n" + "="*80)
        print(f"📊 SCAN RESULTS: Found {len(jobs)} active internships ({len(new_jobs)} brand-new since last run)")
        print("="*80)

        for idx, job in enumerate(jobs[:10], 1):
            badge = "🔥 [EARLY APPLICANT]" if job["is_early"] else "   [OPEN]"
            sec = "📍 [SECTOR V]" if job["is_sector_v"] else f"📍 [{job['location']}]"
            print(f"{idx:02d}. {badge} {job['title']} @ {job['company']}")
            print(f"    {sec} | Posted: {job['time_posted']} | Applicants: {job['applicants']}")
            print(f"    Direct URL: {job['url']}\n")

        # Desktop alert for new early applicant jobs
        if new_jobs:
            early_new = [j for j in new_jobs if j["is_early"]]
            target_list = early_new if early_new else new_jobs
            top_job = target_list[0]
            alert_title = f"🚨 New Internship Alert: {top_job['company']}"
            alert_msg = f"{top_job['title']} ({top_job['location']})\nApplicants: {top_job['applicants']} | Posted: {top_job['time_posted']}"
            send_windows_notification(alert_title, alert_msg, top_job["url"])
            print(f"🔔 [Notification Sent] {alert_title}")

        print(f"🌐 Dashboard updated: {OUTPUT_HTML_FILE}")

        if not watch:
            break

        print(f"\n⏳ Sleeping for {interval_min} minutes before next check (Press Ctrl+C to stop)...")
        time.sleep(interval_min * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sector V Kolkata Internship Early Applicant Pipeline")
    parser.add_argument("--watch", action="store_true", help="Run continuously in background polling mode")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in minutes (default: 15)")
    parser.add_argument("--window", type=str, default="r604800", choices=["r86400", "r259200", "r604800"],
                        help="Time window: r86400 (past 24h), r259200 (past 3 days), r604800 (past week)")
    args = parser.parse_args()

    run_pipeline(watch=args.watch, interval_min=args.interval, time_window=args.window)

