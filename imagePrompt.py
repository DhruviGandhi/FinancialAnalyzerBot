import streamlit as st
import ollama


def improve_prompt(user_prompt):

    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "system",
                "content": """
You are a professional AI prompt engineer.

Convert simple user prompts into highly detailed cinematic prompts for image generation.
Include:
- lighting
- camera angle
- colors
- details
- realistic style
"""
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response["message"]["content"]



st.title("🎨 AI Image Studio")


prompt = st.text_area(
    "Enter your idea"
)


if st.button("Enhance Prompt"):

    with st.spinner("Llama 3 is thinking..."):

        improved = improve_prompt(prompt)

    st.subheader("Enhanced Prompt")

    st.write(improved)