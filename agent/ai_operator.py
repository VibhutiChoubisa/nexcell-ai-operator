import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from agent.tools import search_leads, get_insights, create_task


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


# ---------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are an AI Operator for a fictional CRM system.

You help users search CRM data, provide CRM insights,
and prepare CRM actions.

AVAILABLE TOOLS:

1. search_leads(query)
   READ-ONLY.
   Searches leads by name, company, email, interest, or status.

2. get_insights()
   READ-ONLY.
   Returns computed CRM statistics.

3. create_task(title, due, related_to)
   WRITE OPERATION.
   Represents a request to create a CRM task.

IMPORTANT TOOL RULES:

- Never invent CRM information.
- Use search_leads when information about a specific lead is needed.
- Use get_insights when the user asks for CRM statistics.
- If the user asks to CREATE a task, you MUST call create_task
  with the appropriate arguments.
- Do NOT ask the user for confirmation yourself.
- The application, not the model, handles confirmation.
- The application will intercept create_task before anything
  is written to the CRM.
- Never claim that a task was created unless the application
  confirms that the write operation actually happened.
- Unsupported operations must be clearly explained.

IMPORTANT:

For a request such as:

"Create a task to call Aisha Khan tomorrow."

You should:

1. Search for Aisha Khan if necessary.
2. Once the lead is identified, call create_task.
3. Do not write a natural-language confirmation question.
4. The application will present the confirmation UI.
"""


# ---------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------

search_leads_declaration = {
    "name": "search_leads",
    "description": (
        "Search the CRM leads by name, company, email, "
        "interest, or status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The search term to use when searching "
                    "the CRM leads."
                ),
            }
        },
        "required": ["query"],
    },
}


get_insights_declaration = {
    "name": "get_insights",
    "description": (
        "Return computed CRM statistics including total "
        "leads, lead status counts, total tasks, and "
        "pending tasks."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}


create_task_declaration = {
    "name": "create_task",
    "description": (
        "Prepare a request to create a CRM task. "
        "This is a WRITE operation. The application MUST "
        "request explicit user confirmation before executing it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the task.",
            },
            "due": {
                "type": "string",
                "description": "The requested due date.",
            },
            "related_to": {
                "type": "string",
                "description": (
                    "The CRM lead ID associated with the task."
                ),
            },
        },
        "required": [
            "title",
            "due",
        ],
    },
}


tools = types.Tool(
    function_declarations=[
        search_leads_declaration,
        get_insights_declaration,
        create_task_declaration,
    ]
)


config = types.GenerateContentConfig(
    tools=[tools]
)


# ---------------------------------------------------------
# AI OPERATOR
# ---------------------------------------------------------

def ask_gemini(
    user_message: str,
) -> str | dict[str, Any]:

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"""
{SYSTEM_PROMPT}

User request:
{user_message}
"""
                )
            ],
        )
    ]

    # -----------------------------------------------------
    # GEMINI CALL
    # -----------------------------------------------------

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=contents,
        config=config,
    )

    # -----------------------------------------------------
    # PROCESS TOOL CALLS
    # -----------------------------------------------------

    for part in response.candidates[0].content.parts:

        if not part.function_call:
            continue

        function_call = part.function_call

        tool_name = function_call.name
        arguments = dict(function_call.args)

        print(f"Gemini requested tool: {tool_name}")
        print(f"Arguments: {arguments}")

        # -------------------------------------------------
        # SEARCH LEADS
        # -------------------------------------------------

        if tool_name == "search_leads":

            result = search_leads(
                arguments["query"]
            )

            contents.append(
                response.candidates[0].content
            )

            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=tool_name,
                            response={
                                "result": result
                            },
                        )
                    ],
                )
            )

            # Ask Gemini what to do next.
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=contents,
                config=config,
            )

            # Process the next response.
            for next_part in response.candidates[0].content.parts:

                if next_part.function_call:

                    next_call = next_part.function_call

                    next_tool = next_call.name
                    next_arguments = dict(next_call.args)

                    print(
                        f"Gemini requested tool: "
                        f"{next_tool}"
                    )

                    print(
                        f"Arguments: "
                        f"{next_arguments}"
                    )

                    # -------------------------------------
                    # CREATE TASK
                    # -------------------------------------

                    if next_tool == "create_task":

                        return {
                            "type": "confirmation_required",
                            "action": "create_task",
                            "arguments": {
                                "title": next_arguments.get(
                                    "title"
                                ),
                                "due": next_arguments.get(
                                    "due"
                                ),
                                "related_to": next_arguments.get(
                                    "related_to"
                                ),
                            },
                        }

                    # -------------------------------------
                    # OTHER READ TOOL
                    # -------------------------------------

                    if next_tool == "get_insights":

                        result = get_insights()

                        contents.append(
                            response.candidates[0].content
                        )

                        contents.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name=next_tool,
                                        response={
                                            "result": result
                                        },
                                    )
                                ],
                            )
                        )

                        final_response = (
                            client.models.generate_content(
                                model="gemini-3.5-flash-lite",
                                contents=contents,
                                config=config,
                            )
                        )

                        return final_response.text

            return response.text

        # -------------------------------------------------
        # GET INSIGHTS
        # -------------------------------------------------

        elif tool_name == "get_insights":

            result = get_insights()

            contents.append(
                response.candidates[0].content
            )

            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=tool_name,
                            response={
                                "result": result
                            },
                        )
                    ],
                )
            )

            final_response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=contents,
                config=config,
            )

            return final_response.text

        # -------------------------------------------------
        # CREATE TASK
        # -------------------------------------------------

        elif tool_name == "create_task":

            # CRITICAL:
            # Do NOT execute create_task here.
            #
            # Return a structured action request to Streamlit.

            return {
                "type": "confirmation_required",
                "action": "create_task",
                "arguments": {
                    "title": arguments.get(
                        "title"
                    ),
                    "due": arguments.get(
                        "due"
                    ),
                    "related_to": arguments.get(
                        "related_to"
                    ),
                },
            }

        else:

            return (
                f"Unsupported tool requested: {tool_name}"
            )

    # -----------------------------------------------------
    # NORMAL TEXT RESPONSE
    # -----------------------------------------------------

    return response.text


# ---------------------------------------------------------
# EXECUTE CONFIRMED ACTION
# ---------------------------------------------------------

def execute_confirmed_action(
    action: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:

    """
    Execute a write operation only after explicit
    confirmation from the user interface.
    """

    if action == "create_task":

        return create_task(
            title=arguments["title"],
            due=arguments["due"],
            related_to=arguments.get(
                "related_to"
            ),
        )

    return {
        "error": f"Unsupported action: {action}"
    }


# ---------------------------------------------------------
# LOCAL TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    result = ask_gemini(
        "Create a task to call Aisha Khan tomorrow."
    )

    print("\nAI Operator:")
    print(result)