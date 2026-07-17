import streamlit as st
import json
import os
import pyperclip

from prompt_engine import generate_prompt


st.set_page_config(
    page_title="AI Prompt Studio",
    page_icon="🎨",
    layout="wide"
)


st.title("🎨 AI Prompt Studio")


# --------------------
# Load History
# --------------------

if os.path.exists("history.json"):

    with open("history.json","r") as f:
        history=json.load(f)

else:

    history=[]



# Sidebar

st.sidebar.title("📜 Prompt History")


for item in reversed(history):

    st.sidebar.write(
        item
    )

    st.sidebar.divider()



# Main UI


category = st.selectbox(
    "Select Category",
    [
        "Product Advertisement",
        "Movie Scene",
        "Game Character",
        "Architecture",
        "Food Photography",
        "Fantasy Art"
    ]
)



idea = st.text_area(
    "Enter your idea",
    height=120
)



if st.button("✨ Generate Prompt"):


    if idea.strip()=="":
        st.warning(
            "Please enter idea"
        )


    else:


        with st.spinner(
            "Llama3 is thinking..."
        ):


            result = generate_prompt(
                category,
                idea
            )


        st.session_state.prompt=result


        history.append(result)


        with open(
            "history.json",
            "w"
        ) as f:

            json.dump(
                history,
                f,
                indent=4
            )




if "prompt" in st.session_state:


    st.subheader(
        "Generated Prompt"
    )


    st.code(
        st.session_state.prompt
    )



    if st.button(
        "📋 Copy Prompt"
    ):

        pyperclip.copy(
            st.session_state.prompt
        )

        st.success(
            "Copied!"
        )
