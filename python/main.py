#!/usr/bin/env python3
"""
Strava Weekly Running Distance Fetcher

This script connects to the Strava API to fetch your running activities
and calculate your total running distance for the current week.

Setup Instructions:
1. Go to https://www.strava.com/settings/api and create an application
2. Note your Client ID and Client Secret
3. Set the environment variables or update the config below
4. Run this script - it will guide you through OAuth authentication
"""

import os
import json
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse
import requests

# Configuration
CONFIG = {
    "client_id": os.environ.get("STRAVA_CLIENT_ID", "YOUR_CLIENT_ID"),
    "client_secret": os.environ.get("STRAVA_CLIENT_SECRET", "YOUR_CLIENT_SECRET"),
    "redirect_uri": "http://localhost:8000/callback",
    "token_file": Path.home() / ".strava_tokens.json",
}

# Strava API endpoints
STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"


def save_tokens(tokens: dict) -> None:
    """Save OAuth tokens to a local file."""
    with open(CONFIG["token_file"], "w") as f:
        json.dump(tokens, f)
    print(f"✓ Tokens saved to {CONFIG['token_file']}")


def load_tokens() -> dict | None:
    """Load OAuth tokens from local file if they exist."""
    if CONFIG["token_file"].exists():
        with open(CONFIG["token_file"], "r") as f:
            return json.load(f)
    return None


def get_authorization_url() -> str:
    """Generate the Strava OAuth authorization URL."""
    params = {
        "client_id": CONFIG["client_id"],
        "redirect_uri": CONFIG["redirect_uri"],
        "response_type": "code",
        "scope": "activity:read_all",
    }
    return f"{STRAVA_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    response = requests.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": CONFIG["client_id"],
            "client_secret": CONFIG["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> dict:
    """Refresh the access token using the refresh token."""
    response = requests.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": CONFIG["client_id"],
            "client_secret": CONFIG["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    return response.json()


def get_valid_access_token() -> str:
    """Get a valid access token, refreshing if necessary."""
    tokens = load_tokens()

    if not tokens:
        # Need to do initial OAuth flow
        print("\n" + "=" * 60)
        print("STRAVA AUTHENTICATION REQUIRED")
        print("=" * 60)
        print("\nStep 1: Visit this URL to authorize the application:\n")
        auth_url = get_authorization_url()
        print(auth_url)
        print("\nStep 2: After authorizing, you'll be redirected to a URL like:")
        print("  http://localhost:8000/callback?code=XXXXXX&scope=...")
        print("\nStep 3: Copy the 'code' parameter from that URL and paste it below.\n")

        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            print("(Browser should open automatically)")
        except Exception:
            pass

        code = input("Enter the authorization code: ").strip()
        tokens = exchange_code_for_tokens(code)
        save_tokens(tokens)

    # Check if token is expired
    if tokens.get("expires_at", 0) < time.time():
        print("Access token expired, refreshing...")
        tokens = refresh_access_token(tokens["refresh_token"])
        save_tokens(tokens)

    return tokens["access_token"]


def get_activities(access_token: str, after: int, before: int) -> list:
    """Fetch activities from Strava API within a date range."""
    activities = []
    page = 1
    per_page = 100

    while True:
        response = requests.get(
            f"{STRAVA_API_BASE}/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "after": after,
                "before": before,
                "page": page,
                "per_page": per_page,
            },
        )
        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        activities.extend(batch)
        page += 1

        # Strava rate limits: 100 requests per 15 minutes
        if page > 10:  # Safety limit
            break

    return activities


def get_week_boundaries() -> tuple[datetime, datetime]:
    """Get the start and end of the current week (Monday to Sunday)."""
    today = datetime.now() - timedelta(days=2*7)
    # Monday of current week
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    # End of Sunday
    end_of_week = start_of_week + timedelta(days=7) - timedelta(seconds=1)
    return start_of_week, end_of_week


def meters_to_km(meters: float) -> float:
    """Convert meters to kilometers."""
    return meters / 1000


def meters_to_miles(meters: float) -> float:
    """Convert meters to miles."""
    return meters / 1609.344


def seconds_to_hms(seconds: int) -> str:
    """Convert seconds to hours:minutes:seconds format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def calculate_pace(distance_meters: float, time_seconds: int) -> str:
    """Calculate pace in min/km."""
    if distance_meters == 0:
        return "N/A"
    pace_seconds_per_km = time_seconds / (distance_meters / 1000)
    minutes = int(pace_seconds_per_km // 60)
    seconds = int(pace_seconds_per_km % 60)
    return f"{minutes}:{seconds:02d} /km"


def fetch_weekly_running_stats():
    """Main function to fetch and display weekly running statistics."""
    print("\n🏃 Strava Weekly Running Distance Fetcher")
    print("=" * 50)

    # Check configuration
    if CONFIG["client_id"] == "YOUR_CLIENT_ID":
        print("\n⚠️  Configuration Required!")
        print("\nPlease set up your Strava API credentials:")
        print("1. Go to https://www.strava.com/settings/api")
        print("2. Create an application (use any name/website)")
        print("3. Set environment variables:")
        print("   export STRAVA_CLIENT_ID='your_client_id'")
        print("   export STRAVA_CLIENT_SECRET='your_client_secret'")
        print("\nOr edit this script and replace YOUR_CLIENT_ID and YOUR_CLIENT_SECRET")
        return

    try:
        # Get access token
        access_token = get_valid_access_token()

        # Get week boundaries
        start_of_week, end_of_week = get_week_boundaries()
        print(f"\n📅 Week: {start_of_week.strftime('%B %d')} - {end_of_week.strftime('%B %d, %Y')}")

        # Fetch activities
        print("\n🔄 Fetching activities from Strava...")
        activities = get_activities(
            access_token,
            after=int(start_of_week.timestamp()),
            before=int(end_of_week.timestamp()),
        )

        # Filter for runs only
        runs = [a for a in activities if a.get("type") == "Run"]

        if not runs:
            print("\n📊 No running activities found this week.")
            print("   Time to lace up those shoes! 👟")
            return

        # Calculate statistics
        total_distance_m = sum(run.get("distance", 0) for run in runs)
        total_time_s = sum(run.get("moving_time", 0) for run in runs)
        total_elevation_m = sum(run.get("total_elevation_gain", 0) for run in runs)

        # Display results
        print("\n" + "=" * 50)
        print("📊 WEEKLY RUNNING SUMMARY")
        print("=" * 50)

        print(f"\n🏃 Total Runs: {len(runs)}")
        print(f"📏 Total Distance: {meters_to_km(total_distance_m):.2f} km ({meters_to_miles(total_distance_m):.2f} mi)")
        print(f"⏱️  Total Time: {seconds_to_hms(total_time_s)}")
        print(f"⛰️  Total Elevation: {total_elevation_m:.0f} m ({total_elevation_m * 3.281:.0f} ft)")
        print(f"⚡ Average Pace: {calculate_pace(total_distance_m, total_time_s)}")

        # Individual runs breakdown
        print("\n" + "-" * 50)
        print("INDIVIDUAL RUNS:")
        print("-" * 50)

        for run in sorted(runs, key=lambda x: x["start_date"]):
            run_date = datetime.fromisoformat(run["start_date"].replace("Z", "+00:00"))
            distance_km = meters_to_km(run.get("distance", 0))
            duration = seconds_to_hms(run.get("moving_time", 0))
            pace = calculate_pace(run.get("distance", 0), run.get("moving_time", 0))
            name = run.get("name", "Untitled Run")

            print(f"\n  📌 {name}")
            print(f"     Date: {run_date.strftime('%A, %B %d at %I:%M %p')}")
            print(f"     Distance: {distance_km:.2f} km | Time: {duration} | Pace: {pace}")

        print("\n" + "=" * 50)
        print("Keep running! 🎉")
        print("=" * 50 + "\n")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        if e.response.status_code == 401:
            print("   Token may be invalid. Delete ~/.strava_tokens.json and try again.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    fetch_weekly_running_stats()