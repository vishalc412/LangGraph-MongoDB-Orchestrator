"""
Prompt templates for MongoDB AI Agent.

This module contains all prompts used by the agent, including:
- System prompts defining agent behavior
- Query generation prompts with few-shot examples
- Response formatting prompts

Design Principles:
- Clear, specific instructions
- Few-shot learning examples
- Chain-of-thought reasoning
- Output format specifications

Author: AI Agent Development Team
"""

from typing import Any, Dict, List

# ============================================================================
# System Prompt - Defines Agent Behavior and Capabilities
# ============================================================================

SYSTEM_PROMPT = """You are a MongoDB expert AI assistant specialized in converting natural language questions into MongoDB queries.

Your capabilities:
- Convert natural language to MongoDB find() queries
- Convert natural language to MongoDB aggregation pipelines
- Handle complex queries with grouping, filtering, sorting, and calculations
- Provide clear explanations of queries and results

Your responsibilities:
- Generate accurate MongoDB queries based on user questions
- Explain what the query does in simple terms
- Format results in a user-friendly manner
- Handle edge cases gracefully

Guidelines:
- Always use valid MongoDB syntax
- Prefer aggregation pipelines for complex operations
- Include necessary stages like $match, $group, $sort, $project, $limit
- Use appropriate operators: $gte, $lte, $in, $regex, etc.
- Consider performance (use $match early in pipelines)
- Return clear, concise explanations

Remember: Your goal is to make MongoDB accessible to everyone, regardless of their technical expertise."""

# ============================================================================
# Query Generation Prompt - Converts Natural Language to MongoDB Queries
# ============================================================================

QUERY_GENERATION_PROMPT = """You are tasked with converting a natural language question into a MongoDB query.

**Collection Schema:**
{schema_info}

**User Question:**
{user_question}

**Previous Conversation Context:**
{conversation_history}

**Task:**
Generate a MongoDB query to answer the user's question. Follow these steps:

1. **Analyze the Question:**
   - Identify what data is requested
   - Determine if it's a simple find or requires aggregation
   - Identify any filters, groupings, sorting, or calculations needed

2. **Choose Query Type:**
   - Use "find" for simple lookups
   - Use "aggregate" for: grouping, calculations (avg, sum, count), complex filtering, sorting with grouping

3. **Generate Query:**
   - For find: Create a filter document
   - For aggregate: Create a pipeline array with stages

4. **Output Format:**
   Return a JSON object with:
   ```json
   {{
     "query_type": "find" or "aggregate",
     "collection": "collection_name",
     "query": {{...}} or [...],
     "explanation": "Brief explanation of what this query does"
   }}
   ```

**Examples:**

Example 1 - Simple Find:
Question: "Find movies released in 2020"
Output:
```json
{{
  "query_type": "find",
  "collection": "movies",
  "query": {{"year": 2020}},
  "explanation": "Finds all movies where the year field equals 2020"
}}
```

Example 2 - Find with Comparison:
Question: "What movies have a rating above 8.5?"
Output:
```json
{{
  "query_type": "find",
  "collection": "movies",
  "query": {{"imdb.rating": {{"$gte": 8.5}}}},
  "explanation": "Finds all movies where the IMDB rating is greater than or equal to 8.5"
}}
```

Example 3 - Aggregation with Grouping:
Question: "How many movies were released each year after 2015?"
Output:
```json
{{
  "query_type": "aggregate",
  "collection": "movies",
  "query": [
    {{"$match": {{"year": {{"$gte": 2015}}}}}},
    {{"$group": {{"_id": "$year", "count": {{"$sum": 1}}}}}},
    {{"$sort": {{"_id": -1}}}}
  ],
  "explanation": "Groups movies by year (filtering for 2015 and later), counts movies per year, and sorts by year descending"
}}
```

Example 4 - Aggregation with Average:
Question: "What's the average rating of movies by genre?"
Output:
```json
{{
  "query_type": "aggregate",
  "collection": "movies",
  "query": [
    {{"$unwind": "$genres"}},
    {{"$group": {{
      "_id": "$genres",
      "avg_rating": {{"$avg": "$imdb.rating"}},
      "count": {{"$sum": 1}}
    }}}},
    {{"$sort": {{"avg_rating": -1}}}}
  ],
  "explanation": "Unwinds the genres array, groups by genre, calculates average rating and count for each genre, then sorts by average rating descending"
}}
```

Example 5 - Top N with Limit:
Question: "Show me the top 5 highest-rated movies from 2020"
Output:
```json
{{
  "query_type": "aggregate",
  "collection": "movies",
  "query": [
    {{"$match": {{"year": 2020}}}},
    {{"$sort": {{"imdb.rating": -1}}}},
    {{"$limit": 5}},
    {{"$project": {{
      "title": 1,
      "year": 1,
      "imdb.rating": 1
    }}}}
  ],
  "explanation": "Filters for 2020 movies, sorts by rating (highest first), limits to top 5, and projects only relevant fields"
}}
```

Example 6 - Multiple Conditions:
Question: "Find action movies from 2018 to 2022 with rating above 7"
Output:
```json
{{
  "query_type": "aggregate",
  "collection": "movies",
  "query": [
    {{"$match": {{
      "genres": "Action",
      "year": {{"$gte": 2018, "$lte": 2022}},
      "imdb.rating": {{"$gt": 7}}
    }}}},
    {{"$sort": {{"imdb.rating": -1}}}}
  ],
  "explanation": "Filters for Action genre movies released between 2018-2022 with rating above 7, sorted by rating"
}}
```

**Important Notes:**
- Always output valid JSON only, no additional text
- Use the exact collection name from the schema
- Use actual field names from the schema
- For nested fields use dot notation (e.g., "imdb.rating")
- Include $match early in aggregation pipelines for performance
- Use appropriate comparison operators: $gt, $gte, $lt, $lte, $eq, $ne, $in
- For text search, consider using $regex with appropriate flags

Now, generate the MongoDB query for the user's question above."""

# ============================================================================
# Response Formatting Prompt - Formats Results for User
# ============================================================================

RESPONSE_FORMATTING_PROMPT = """You are tasked with presenting MongoDB query results to a user in a clear, conversational manner.

**Original User Question:**
{user_question}

**MongoDB Query That Was Executed:**
{query_display}

**Query Results:**
{query_results}

**Task:**
Create a clear, conversational response that:
1. Directly answers the user's question
2. Presents the results in an easy-to-understand format
3. Provides context and insights when relevant
4. Mentions any limitations (e.g., if results were truncated)

**Guidelines:**
- Use natural language, avoid technical jargon
- Format numbers clearly (e.g., "8.5 rating" not "8.500000")
- Present lists in a readable way (bullet points or numbered)
- If no results found, explain this clearly and suggest alternatives
- If many results, summarize key findings
- Be concise but complete

**Examples:**

Example 1 - Simple Results:
Question: "Find movies released in 2020"
Results: [{"title": "Tenet", "year": 2020}, {"title": "Soul", "year": 2020}]
Response:
"I found 2 movies released in 2020:
1. Tenet
2. Soul"

Example 2 - Aggregation Results:
Question: "What's the average rating of movies by genre?"
Results: [{"_id": "Drama", "avg_rating": 7.2, "count": 150}, {"_id": "Action", "avg_rating": 6.8, "count": 120}]
Response:
"Here's the average rating by genre:
- Drama: 7.2 (based on 150 movies)
- Action: 6.8 (based on 120 movies)"

Example 3 - No Results:
Question: "Find movies from the year 3000"
Results: []
Response:
"I didn't find any movies from the year 3000 in the database. The database contains movies up to 2024. Would you like to search for movies from a different year?"

Example 4 - Truncated Results:
Question: "Show me all action movies"
Results: [... 100 movies ...] (showing 100 of 500)
Response:
"I found 500 action movies in total. Here are the first 100:
[list of movies]

Would you like me to filter these results further (by year, rating, etc.)?"

**Important:**
- Be helpful and friendly
- Focus on answering the user's actual question
- Don't just dump raw data - interpret and present it
- If the results are complex, summarize key insights

Now, create a response for the user based on the query results above."""

# ============================================================================
# Prompt Builder Functions
# ============================================================================


def create_query_generation_prompt(
    user_question: str,
    schema_info: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
) -> str:
    """
    Create a query generation prompt with context.

    Args:
        user_question: User's natural language question
        schema_info: Database schema information
        conversation_history: Recent conversation messages

    Returns:
        Formatted prompt string
    """
    # Format schema info
    schema_str = f"""
Collection: {schema_info.get('collection', 'unknown')}
Fields: {', '.join(schema_info.get('fields', []))}
Sample Data: {schema_info.get('sample_values', {})}
Document Count: {schema_info.get('document_count', 0)}
"""

    # Format conversation history
    history_str = ""
    if conversation_history:
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"
    else:
        history_str = "No previous conversation"

    # Build full prompt
    prompt = QUERY_GENERATION_PROMPT.format(
        schema_info=schema_str.strip(),
        user_question=user_question,
        conversation_history=history_str.strip(),
    )

    return prompt


def create_response_formatting_prompt(
    user_question: str, query_display: str, query_results: str
) -> str:
    """
    Create a response formatting prompt.

    Args:
        user_question: Original user question
        query_display: Formatted MongoDB query
        query_results: Formatted query results

    Returns:
        Formatted prompt string
    """
    prompt = RESPONSE_FORMATTING_PROMPT.format(
        user_question=user_question,
        query_display=query_display,
        query_results=query_results,
    )

    return prompt
