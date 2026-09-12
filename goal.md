# Smart Career Agent MCP Server

## The Scenario
A specialized MCP (Model Context Protocol) server that acts as a bridge between an LLM assistant and a local job-matching engine. The system is entirely driven by user chat interactions, allowing the user to command web crawlers, parse their CV, or manually describe their profile to find the best job matches.

**Recommended Tech Stack:** 
Structure this as a Python monorepo managed with `uv`. Use a lightweight database (SQLite or PostgreSQL) for the job postings. Route the CV extraction tasks through a local Vision-Language Model (like Qwen-VL) served via vLLM to handle complex PDF layouts and extract structured skills.

---

## Core Workflows & MCP Tools

### 1. On-Demand Job Crawling
The user can command the assistant to scrape specific recruitment websites to populate or update the local database.

*   **User Flow:** The user types, *"Go crawl [URL] for AI Engineer roles."*
*   **System Action:** The MCP server fetches the URL, parses the job descriptions (Title, Company, Requirements, Tech Stack), and saves them to the database.

#### Tool Schema: `trigger_crawler`
```json
{
  "name": "trigger_crawler",
  "description": "Scrapes a given job board URL for a specific job category and saves the postings to the database.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "target_url": {
        "type": "string",
        "description": "The URL of the recruitment page to crawl."
      },
      "job_category": {
        "type": "string",
        "description": "The category or keyword of the jobs to look for (e.g., 'AI Engineer')."
      }
    },
    "required": ["target_url", "job_category"]
  }
}
```

---

### 2. CV-Driven Job Matching
The user provides a CV file and asks for job matches based on its contents.

*   **User Flow:** The user types, *"Here is my new CV file (path/to/cv.pdf). Find me the best remote matches."*
*   **System Action:** The server uses the local VLM pipeline to extract structured data (skills, experience) from the file, and then queries the database for the top overlapping jobs.

#### Tool Schema: `match_jobs_from_cv`
```json
{
  "name": "match_jobs_from_cv",
  "description": "Parses a candidate's CV file to extract their technical profile, then searches the job database for the best matches.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "The local file path to the user's CV (PDF or text file)."
      },
      "preferences": {
        "type": "string",
        "description": "Additional user preferences from the chat prompt (e.g., 'remote only')."
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of matches to return.",
        "default": 5
      }
    },
    "required": ["file_path"]
  }
}
```

---

### 3. Prompt-Driven Job Matching
The user skips the file upload and manually describes their skills and preferences in the chat.

*   **User Flow:** The user types, *"I have 2 years of experience with Python and PyTorch. What are the best local roles for me?"*
*   **System Action:** The server takes the explicitly stated skills and preferences and queries the job database directly.

#### Tool Schema: `match_jobs_from_prompt`
```json
{
  "name": "match_jobs_from_prompt",
  "description": "Searches the job database for positions that match a list of skills and preferences provided manually by the user in the chat.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "skills": {
        "type": "array",
        "items": { "type": "string" },
        "description": "A list of technical skills mentioned by the user (e.g., ['Python', 'PyTorch'])."
      },
      "preferences": {
        "type": "string",
        "description": "Specific preferences provided by the user (e.g., 'remote only', 'startup')."
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of matches to return.",
        "default": 5
      }
    },
    "required": ["skills", "preferences"]
  }
}
```