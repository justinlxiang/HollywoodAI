"""
Researcher Agent - Gathers relevant information using iterative web search before story creation.

This agent performs multi-turn tool calling to conduct thorough research:
1. Plans search queries based on the story concept
2. Executes multiple searches iteratively
3. Evaluates and synthesizes findings
4. Compiles a comprehensive research brief
"""

from google import genai
from google.genai import types

from ..config import MODEL_NAME, THINKING_LEVEL


# Maximum number of research iterations to prevent infinite loops
MAX_RESEARCH_ITERATIONS = 10


RESEARCHER_SYSTEM_PROMPT = """You are a thorough research assistant preparing background material for a screenwriting team.

## Your Role:
You gather relevant information that will help writers create an authentic, well-informed story. You have access to a web search tool that you should use MULTIPLE times to find comprehensive information.

## Research Process:
1. First, analyze the story request and identify 3-5 key topics to research
2. Use the google_search tool to search for each topic - search ONE topic at a time
3. After each search, evaluate what you've learned and what gaps remain
4. Continue searching until you have enough material (aim for 3-6 searches)
5. When done researching, compile your findings into a Research Brief

## Tool Usage:
You have access to: google_search(query: str)
- Use specific, targeted queries for best results
- Search for different aspects: setting, characters, genre, technical details, cultural context
- Don't repeat the same search - each query should explore a different angle

## When to Stop Searching:
Stop when you have gathered:
- Key facts about the subject matter
- Genre conventions and examples
- Relevant technical or cultural details
- Potential story elements and inspirations
- Any sensitivities to be aware of

## Final Output Format:
When you have completed your research, provide the brief in this format:

```markdown
# Research Brief

## Topic Understanding
[Explain what the story request is about and key themes]

## Key Facts & Context
- [Relevant fact 1]
- [Relevant fact 2]
- [etc.]

## Genre/Style Notes
[Conventions of the genre, tone expectations, successful examples]

## Authenticity Details
[Specific details that would make the story feel real and grounded]

## Potential Story Elements
[Interesting elements discovered that could enhance the narrative]

## Warnings/Sensitivities
[Any topics that need careful handling]

## Sources Consulted
[List the searches you performed and key sources]
```

Be concise but thorough. Focus on information that directly helps create a compelling short film.

IMPORTANT: You MUST use the google_search tool multiple times before writing your final brief. Do not skip the research phase."""


# Tool declaration for the researcher's search capability
SEARCH_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="google_search",
            description="Search the web for information relevant to the story research. Use specific, targeted queries.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The search query to execute. Be specific and targeted.",
                    ),
                },
                required=["query"],
            ),
        ),
    ]
)


class ResearcherAgent:
    """
    The Researcher agent gathers background information using iterative web search.
    
    This agent runs ONCE at the very beginning, before the first draft,
    to provide the Writer with relevant context and research.
    
    It uses multi-turn tool calling to:
    1. Plan what to search for
    2. Execute multiple searches
    3. Synthesize findings into a comprehensive brief
    """
    
    def __init__(self, client: genai.Client, context_manager=None):
        """
        Initialize the researcher agent.
        
        Args:
            client: Gemini client instance
            context_manager: Unused, kept for interface compatibility
        """
        self.name = "Researcher"
        self.system_prompt = RESEARCHER_SYSTEM_PROMPT
        self.client = client
        self.search_results: list[dict] = []  # Track all searches performed
    
    def _execute_search(self, query: str) -> str:
        """
        Execute a web search using Gemini's grounded search.
        
        Args:
            query: The search query
            
        Returns:
            Search results as text
        """
        print(f"    🔍 Searching: '{query}'")
        
        try:
            # Use Gemini with Google Search grounding for the actual search
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=f"Search and summarize key information about: {query}",
                config=types.GenerateContentConfig(
                    system_instruction="You are a search assistant. Provide a concise summary of the most relevant information found. Include specific facts, dates, names, and details that would be useful for research.",
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )
            result = response.text
            print(f"    ✓ Found {len(result)} chars of information")
            return result
            
        except Exception as e:
            error_msg = f"Search failed: {e}"
            print(f"    ✗ {error_msg}")
            return error_msg
    
    def _process_tool_calls(self, response) -> list[types.Part]:
        """
        Process function calls from the model response.
        
        Args:
            response: The model response that may contain function calls
            
        Returns:
            List of FunctionResponse parts to send back
        """
        function_responses = []
        
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.function_call:
                    fc = part.function_call
                    if fc.name == "google_search":
                        query = fc.args.get("query", "")
                        if query:
                            # Execute the search
                            result = self._execute_search(query)
                            
                            # Track this search
                            self.search_results.append({
                                "query": query,
                                "result_preview": result[:200] + "..." if len(result) > 200 else result,
                            })
                            
                            # Create function response
                            function_responses.append(
                                types.Part.from_function_response(
                                    name="google_search",
                                    response={"result": result},
                                )
                            )
        
        return function_responses
    
    def _has_function_calls(self, response) -> bool:
        """Check if the response contains function calls."""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.function_call:
                    return True
        return False
    
    def _get_text_response(self, response) -> str:
        """Extract text from the response."""
        try:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.text:
                        return part.text
        except Exception:
            return ""
    
    def call(self, input_data: dict) -> dict:
        """
        Conduct iterative web research for the story concept.
        
        This method performs multi-turn tool calling:
        1. Sends the research request to the model
        2. Model decides what to search for and calls google_search
        3. We execute the search and return results
        4. Repeat until model provides final research brief
        
        Args:
            input_data: Dict containing:
                - "message": The user's story prompt/request
                
        Returns:
            Dict with research brief
        """
        user_prompt = input_data.get("message", "")
        
        if not user_prompt:
            return {
                "response": "",
                "research": "",
                "agent": self.name,
                "draft_num": 0,
                "searches_performed": 0,
            }
        
        # Reset search tracking
        self.search_results = []
        
        # Build the initial research request
        initial_request = f"""Research the following story concept to help a screenwriting team create an authentic short film:

STORY REQUEST:
{user_prompt}

Start by identifying what aspects need research, then use the google_search tool to gather information.
Remember to search for multiple aspects:
1. The subject matter, setting, or theme
2. Genre conventions if applicable  
3. Technical or factual details that would add authenticity
4. Cultural context if relevant
5. Similar successful works for inspiration

After gathering enough information through multiple searches, compile a comprehensive Research Brief."""

        print(f"\n  [{self.name}] Starting iterative research...")
        print(f"  Story concept: {user_prompt[:200]}...")
        
        try:
            # Initialize conversation history
            contents = [initial_request]
            
            iteration = 0
            research_text = ""
            total_function_calls = 0
            
            while iteration < MAX_RESEARCH_ITERATIONS:
                iteration += 1
                print(f"\n  [{self.name}] Iteration {iteration}/{MAX_RESEARCH_ITERATIONS}")
                
                # Generate response
                response = self.client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
                        tools=[SEARCH_TOOL],
                    ),
                )
                
                # Check if model wants to call tools
                if self._has_function_calls(response):
                    # Count function calls in this iteration
                    num_calls = sum(
                        1 for candidate in response.candidates
                        for part in candidate.content.parts
                        if part.function_call
                    )
                    print(f"    Model requesting {num_calls} search(es)...")
                    
                    # Add model's response to history
                    contents.append(response.candidates[0].content)
                    
                    # Process tool calls and get results
                    function_responses = self._process_tool_calls(response)
                    
                    total_function_calls += len(function_responses)
                    print(f"    Executed {len(function_responses)} function call(s) this iteration (total: {total_function_calls})")
                    
                    if function_responses:
                        # Add function responses to history
                        contents.append(types.Content(
                            role="user",
                            parts=function_responses,
                        ))
                    
                else:
                    # Model provided final text response
                    research_text = self._get_text_response(response)
                    if research_text:
                        print(f"    ✓ Research complete after {len(self.search_results)} searches")
                        break
            
            # If we hit max iterations without a final response
            if not research_text:
                print(f"  [{self.name}] Max iterations reached, requesting final brief...")
                
                # Ask for final compilation
                contents.append(
                    "You have completed your searches. Now compile all the information you've gathered into the final Research Brief format. Do not make any more searches."
                )
                
                response = self.client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
                        # No tools - force text output
                    ),
                )
                research_text = self._get_text_response(response)
            
        except Exception as e:
            print(f"  [{self.name}] Research failed ({e}), continuing without research")
            research_text = f"[Research unavailable - error: {e}]"
        
        # Log summary
        print(f"\n  [{self.name}] RESEARCH SUMMARY:")
        print(f"  Total iterations: {iteration}")
        print(f"  Total function calls: {total_function_calls}")
        print(f"  Total searches: {len(self.search_results)}")
        for i, search in enumerate(self.search_results, 1):
            print(f"    {i}. '{search['query']}'")
        print(f"  Brief length: {len(research_text)} chars")
        
        result = {
            "response": research_text,
            "research": research_text,
            "agent": self.name,
            "draft_num": 0,
            "searches_performed": len(self.search_results),
            "search_queries": [s["query"] for s in self.search_results],
        }
        
        return result
