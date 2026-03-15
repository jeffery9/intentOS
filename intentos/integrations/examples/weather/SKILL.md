---
name: weather_skill
description: Query global weather information and forecasts. This skill should be used when users want to check current weather conditions or get weather forecasts for specific locations.
license: MIT
---

# Weather Skill

This skill provides global weather query functionality.

## About This Skill

This skill enables Claude to provide accurate weather information by:
1. Querying current weather conditions for any city
2. Providing weather forecasts for upcoming days
3. Offering weather-related recommendations

## When to Use This Skill

Use this skill when users ask about:
- Current weather conditions ("What's the weather in Beijing?")
- Weather forecasts ("Will it rain tomorrow in Shanghai?")
- Weather-related planning ("Should I bring an umbrella today?")

## Resources

This skill uses the following resources:

### Scripts

- `scripts/get_weather.py` - Python script to fetch weather data from API

### References

- `references/api_docs.md` - Weather API documentation
- `references/cities.json` - List of supported cities

## Usage Examples

```
User: What's the weather in Beijing today?
Assistant: [Uses weather skill to fetch and display current conditions]

User: Will it be sunny in Shanghai this weekend?
Assistant: [Uses weather skill to get weekend forecast]
```

## Configuration

To use this skill, configure your weather API key:

```bash
export WEATHER_API_KEY=your_api_key_here
```

## Notes

- Weather data is refreshed every 30 minutes
- Forecasts are available up to 7 days in advance
- All temperatures are in Celsius by default
