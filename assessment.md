# Python Interview Task

## Scenario

You are asked to build a Python web API that analyzes plain text transcripts and returns a summary along with a list of next actions. Your implementation should clearly demonstrate good architectural practices.

## Provided Adapter (do not implement)

- **OpenAI Adapter**: Sends the transcript text to OpenAI's API along with a predefined, hardcoded prompt. This adapter returns a DTO.
- The transcript, system prompt, and user prompt are provided.

A file defining the interface (ports) for this adapter will be provided.

## Requirements (Point 1)

### Analyze Transcript

- Create an HTTP endpoint (e.g., using FastAPI or Flask) that accepts GET requests containing a plain text transcript.
- Perform basic input validation (when the transcript is empty)
- Invoke the provided OpenAI adapter to analyze the transcript.
- Store the analysis result in memory (an external DB is not required).
- Return a response containing:
  - A unique ID.
  - A summary of the transcript.
  - A suggested list of next steps or actions based on the transcript analysis.

### Get a Transcript by ID

- Create an HTTP endpoint to get transcript analysis by ID.

### Additional Requirements

- Adhere strictly to the interfaces defined in the provided ports file.

## Optional Advanced Requirements (Point 2)

- Build an additional endpoint to support concurrent analysis of multiple transcripts within a single request:
  - Implement asynchronous processing (e.g., using asyncio).
  - Handle multiple transcript analyses simultaneously without blocking the main API thread.

## Success Criteria

- Code readability, modularity, and adherence to best practices.
- Functional correctness of the API.
- Swagger
- Clear error handling and appropriate HTTP response statuses.
- Testability of the code (clear separation of concerns, ease of unit testing).
- (Optional) Effective asynchronous processing implementation.

## Hints

- You will find a test running openai adapter. This will be the documentation to build the prompt to analyze the transcript
- The provided OpenAI adapter utilizes structured output, allowing you to specify a system prompt, a user prompt, and a DTO. The adapter then returns a model instance populated according to the DTO's defined structure.
- Create a DTO that contains the requested fields.
- Hexagonal (or clean) architecture consists of distinct layers. Consider creating a separate model layer for the LLM responses. Pay attention to avoiding layer coupling.
