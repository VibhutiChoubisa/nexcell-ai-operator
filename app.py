import streamlit as st

from agent.ai_operator import (
    ask_gemini,
    execute_confirmed_action,
)


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="ConneX AI Operator",
    page_icon="🤖",
    layout="centered",
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🤖 ConneX AI Operator")
st.caption(
    "Ask questions or safely run tasks across your CRM."
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None


# ---------------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------------------------------------------------
# CONFIRMATION UI
# ---------------------------------------------------------

if st.session_state.pending_action is not None:

    action = st.session_state.pending_action
    arguments = action["arguments"]

    st.warning("⚠️ Confirmation required")

    st.markdown(
        f"**Task:** {arguments.get('title')}"
    )

    st.markdown(
        f"**Due:** {arguments.get('due')}"
    )

    st.markdown(
        f"**Related lead:** "
        f"{arguments.get('related_to') or 'None'}"
    )

    st.write("Do you want to create this task?")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Confirm",
            key="confirm_task",
            use_container_width=True,
        ):

            result = execute_confirmed_action(
                action["action"],
                action["arguments"],
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "✅ **Task created successfully.**\n\n"
                        f"- **Task ID:** {result['id']}\n"
                        f"- **Title:** {result['title']}\n"
                        f"- **Due:** {result['due']}\n"
                        f"- **Related lead:** "
                        f"{result.get('related_to') or 'None'}"
                    ),
                }
            )

            st.session_state.pending_action = None

            st.rerun()

    with col2:

        if st.button(
            "❌ Cancel",
            key="cancel_task",
            use_container_width=True,
        ):

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "❌ **Action cancelled.** "
                        "No changes were made to the CRM."
                    ),
                }
            )

            st.session_state.pending_action = None

            st.rerun()


# ---------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------

user_message = st.chat_input(
    "Ask something about your CRM..."
)


if user_message:

    # Add user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_message)

    # -----------------------------------------------------
    # CALL AI OPERATOR
    # -----------------------------------------------------

    result = ask_gemini(user_message)

    # -----------------------------------------------------
    # HANDLE CONFIRMATION REQUEST
    # -----------------------------------------------------

    if isinstance(result, dict) and result.get(
        "type"
    ) == "confirmation_required":

        # Store pending write action.
        st.session_state.pending_action = result

        assistant_message = (
            "I found the requested information and "
            "prepared the task. Please review the "
            "details below and confirm if you want "
            "me to create it."
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": assistant_message,
            }
        )

    # -----------------------------------------------------
    # HANDLE NORMAL AI RESPONSE
    # -----------------------------------------------------

    else:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": str(result),
            }
        )

    st.rerun()
