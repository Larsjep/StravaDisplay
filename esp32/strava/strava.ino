#include <TFT_eSPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <time.h>

// Configuration - Update these with your credentials
#include "secret.h"

// Strava API configuration
const char* STRAVA_API_BASE = "https://www.strava.com/api/v3";
const unsigned long REFRESH_INTERVAL = 900000; // 15 minutes in milliseconds

// Global objects
TFT_eSPI tft = TFT_eSPI();
WiFiClientSecure client;

// Data structure for weekly stats
struct WeeklyStats {
  float totalDistance;    // in meters
  unsigned long totalTime; // in seconds
  int runCount;
  bool valid;
};

WeeklyStats currentStats = {0, 0, 0, false};
unsigned long lastFetchTime = 0;

void setup() {
  Serial.begin(115200);

  // Initialize display
  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_BLACK);

  // Show connecting message
  displayStatus("Connecting to WiFi...");
  delay(5000);

  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.println("IP address: " + WiFi.localIP().toString());

    displayStatus("WiFi Connected!");
    delay(1000);

    // Synchronize time with NTP server
    displayStatus("Syncing time...");
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");

    // Wait for time to be set
    int timeAttempts = 0;
    while (time(nullptr) < 100000 && timeAttempts < 20) {
      delay(500);
      Serial.print(".");
      timeAttempts++;
    }
    Serial.println("\nTime synchronized!");

    // Configure secure client (disable certificate validation for simplicity)
    client.setInsecure();

    // Fetch initial data
    displayStatus("Fetching Strava data...");
    fetchWeeklyStats();
    displayWeeklyStats();
  } else {
    Serial.println("\nWiFi connection failed!");
    displayStatus("WiFi Failed!");
  }
}

void loop() {
  // Check if it's time to refresh
  if (WiFi.status() == WL_CONNECTED &&
      millis() - lastFetchTime >= REFRESH_INTERVAL) {
    Serial.println("Refreshing data...");
    fetchWeeklyStats();
    displayWeeklyStats();
  }

  delay(1000); // Check every second
}

void displayStatus(String message) {
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(message, 120, 120);
}

void fetchWeeklyStats() {
  HTTPClient http;

  // Get current time from NTP
  time_t now = time(nullptr);
  struct tm timeinfo;
  localtime_r(&now, &timeinfo);

  // Calculate timestamp for start of current week (Monday 00:00)
  // tm_wday: 0=Sunday, 1=Monday, ..., 6=Saturday
  int daysSinceMonday = (timeinfo.tm_wday + 6) % 7; // Convert to days since Monday
  time_t weekStart = now - (daysSinceMonday * 24 * 3600) - (timeinfo.tm_hour * 3600) - (timeinfo.tm_min * 60) - timeinfo.tm_sec;

  // Build URL with query parameters
  String url = String(STRAVA_API_BASE) + "/athlete/activities?after=" + String(weekStart);

  Serial.println("Fetching from: " + url);

  http.begin(client, url);
  http.addHeader("Authorization", "Bearer " + String(STRAVA_TOKEN));

  int httpCode = http.GET();
  tft.drawString(std::to_string(httpCode).c_str(), 120, 140);

  if (httpCode == 200) {
    String payload = http.getString();
    Serial.println("Response received, parsing...");
    parseActivities(payload);
    lastFetchTime = millis();
  } else {
    Serial.printf("HTTP error: %d\n", httpCode);
    if (httpCode > 0) {
      Serial.println("Response: " + http.getString());
    }
    currentStats.valid = false;
  }

  http.end();
}

void parseActivities(String json) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, json);
  tft.drawString(std::to_string(int(error.code())).c_str(), 120, 160);
  
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    currentStats.valid = false;
    return;
  }

  // Reset stats
  currentStats.totalDistance = 0;
  currentStats.totalTime = 0;
  currentStats.runCount = 0;

  // Sum up all running activities
  JsonArray activities = doc.as<JsonArray>();
  for (JsonObject activity : activities) {
    String type = activity["type"];
    if (type == "Run") {
      currentStats.totalDistance += activity["distance"].as<float>();
      currentStats.totalTime += activity["moving_time"].as<unsigned long>();
      currentStats.runCount++;
    }
  }

  currentStats.valid = true;

  Serial.printf("Stats: %.2f km, %lu min, %d runs\n",
                currentStats.totalDistance / 1000.0,
                currentStats.totalTime / 60,
                currentStats.runCount);
}

void displayWeeklyStats() {
  tft.fillScreen(TFT_BLACK);

  if (!currentStats.valid) {
    tft.setTextColor(TFT_RED);
    tft.setTextSize(2);
    tft.setTextDatum(MC_DATUM);
    tft.drawString("Error loading", 120, 100);
    tft.drawString("data", 120, 130);
    return;
  }

  // Title
  tft.setTextColor(TFT_ORANGE);
  tft.setTextSize(2);
  tft.setTextDatum(TC_DATUM);
  tft.drawString("THIS WEEK", 120, 30);

  // Distance
  tft.setTextColor(TFT_CYAN);
  tft.setTextSize(3);
  tft.setTextDatum(MC_DATUM);
  float distanceKm = currentStats.totalDistance / 1000.0;
  tft.drawString(String(distanceKm, 1) + " km", 120, 90);

  // Time
  tft.setTextColor(TFT_GREEN);
  tft.setTextSize(2);
  unsigned long hours = currentStats.totalTime / 3600;
  unsigned long minutes = (currentStats.totalTime % 3600) / 60;
  String timeStr = String(hours) + "h " + String(minutes) + "m";
  tft.drawString(timeStr, 120, 130);

  // Run count
  tft.setTextColor(TFT_YELLOW);
  tft.setTextSize(2);
  String runsStr = String(currentStats.runCount) + " runs";
  tft.drawString(runsStr, 120, 160);

  // Last updated
  tft.setTextColor(TFT_DARKGREY);
  tft.setTextSize(1);
  tft.setTextDatum(BC_DATUM);
  tft.drawString("Updated: " + String(millis() / 60000) + "m ago", 120, 220);
}
