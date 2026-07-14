"""Multi-agent AI layer (Phase 5).

Seven single-responsibility agents that collaborate through the deterministic
service layer:

- InventoryAgent        — stock health (low / out / dead / overstock)
- SalesAgent            — sales trends and best/worst sellers
- CustomerAgent         — customer segmentation (VIP / regular / new / inactive)
- ForecastAgent         — reorder shortlist from demand forecasting
- RecommendationAgent   — synthesizes the above into reasoned recommendations
- NotificationAgent     — morning report + smart alerts
- ManagerAssistant      — grounded natural-language Q&A

Every fact is computed from the database. The LLM (optional, via GROQ_API_KEY)
only phrases already-computed facts — it never invents numbers (see core.llm).
"""
