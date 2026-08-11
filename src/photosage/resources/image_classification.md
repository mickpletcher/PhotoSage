# Image Classification Prompt

Classify image content for a photo organization tool.

Return JSON only. Do not include markdown, explanations, or filename suggestions.

Identify the main subject, useful secondary subjects, visible activity, environment, document type, cautious location clues, factual tags, and a concise description.

Do not rename files. Do not identify private people. Do not guess names. Do not extract sensitive private details from documents.

Required keys: `primary_subject`, `secondary_subject`, `activity`, `environment`, `location_guess`, `confidence`, `tags`, and `description`.
