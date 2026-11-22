# Pydantic and Structured Output (Sprint 1)
Pydantic lets you define typed schemas in Python. In LangChain, a PydanticOutputParser turns a model response into a validated object and generates format instructions that are injected into the prompt. Field constraints such as `ge=0, le=100` reject invalid scores. The Assessor Agent returns an object with `score`, `feedback_points` and `pass_status`, so downstream code never has to parse free text.
When parsing fails, the application should fall back gracefully instead of crashing, for example by returning a structured "Unable to verify" message.
