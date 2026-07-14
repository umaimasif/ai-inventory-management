# AI Architecture

## Vision

This system should behave like an AI Business Manager instead of a simple inventory application.

The system must consist of multiple specialized AI agents.

Every agent has one responsibility.

Agents communicate through shared business data.

No agent should perform the work of another agent.

---

# Agent 1 — Inventory Agent

Responsibilities

- Monitor stock levels
- Detect low inventory
- Detect overstock
- Detect dead stock
- Detect products nearing expiry
- Monitor supplier inventory if available

Outputs

- Restock recommendations
- Overstock warnings
- Inventory alerts

---

# Agent 2 — Sales Analysis Agent

Responsibilities

Analyze

- Daily sales
- Weekly sales
- Monthly sales
- Yearly trends

Identify

- Best sellers
- Worst sellers
- Fast growing products
- Declining products

Outputs

Business insights.

---

# Agent 3 — Customer Intelligence Agent

Responsibilities

Track

- Purchase history
- Spending
- Visit frequency
- Favorite products
- Favorite categories

Generate

Customer segments

Examples

VIP

Regular

Inactive

New Customer

---

# Agent 4 — Recommendation Agent

Uses outputs from

Inventory Agent

Sales Agent

Customer Agent

Creates recommendations

Examples

Increase Red Shampoo order.

Stop ordering White Shampoo.

Move Bread beside Butter.

Bundle Tea + Sugar.

Offer discount on old inventory.

Every recommendation must explain WHY.

---

# Agent 5 — Forecast Agent

Predict

Next week demand

Next month demand

Seasonal demand

Holiday demand

Estimate inventory needed.

Confidence score should be included.

Cold Start Rule

When historical data is insufficient (less than ~60 days), do NOT use ML forecasting.

Start with simple rules:
- reorder_point = avg_daily_sales × lead_time + safety_stock
- Use moving average for short-term demand.

Switch to Scikit-learn model only after enough sales history exists.

Always label forecast confidence (low / medium / high). Never fake certainty.

---

# Agent 6 — Notification Agent

Responsible for communication.

Every morning

Generate business summary.

Send

Email

WhatsApp

SMS

Future integrations.

Urgent alerts

Low stock

Sales spikes

Inventory anomalies

Expiry alerts

Anomaly Definitions (concrete rules)

- Sales spike: today_sales > mean + 2 × stddev
- Sales drop: today_sales < mean − 2 × stddev
- Inventory loss: physical_count < system_count (from Stock Audits)
- Expiry alert: batch expiry_date within configurable threshold (e.g. 7 days)

---

# Agent 7 — Manager Assistant

Acts as business consultant.

Accepts natural language questions.

Examples

"What should I order?"

"Why are sales down?"

"What products should I discount?"

Uses outputs from all agents.

Never invent business facts.

Always explain reasoning.

Grounding Rule (prevent hallucination)

The LLM must never generate numbers from itself.

Flow:
1. LLM converts question into a query intent.
2. Backend runs the real query against the database.
3. LLM only phrases the real returned data.

System prompt must enforce: "Answer only from provided data. If data is missing, say 'I don't have that.'"

Every answer + source rows must be stored in Agent Logs.