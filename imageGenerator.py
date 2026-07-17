import streamlit as st
import ollama
import requests
import urllib.parse
from PIL import Image
from io import BytesIO

st.title("🎨 AI Image Generator")

prompt = st.text_area("Enter Prompt")

if st.button("Generate"):

    with st.spinner("Enhancing Prompt..."):

        response = ollama.chat(
            model="llama3",
            messages=[
                {
                    "role": "user",
                    "content": f"""
Convert this into a detailed image generation prompt:

{prompt}
"""
                }
            ]
        )

        enhanced_prompt = response["message"]["content"]

    st.subheader("Enhanced Prompt")
    st.write(enhanced_prompt)

    encoded_prompt = urllib.parse.quote(enhanced_prompt)

    image_url = (
        f"https://image.pollinations.ai/prompt/"
        f"{encoded_prompt}"
    )

    with st.spinner("Generating Image..."):

        img_response = requests.get(
            image_url,
            timeout=300
        )

        image = Image.open(
            BytesIO(img_response.content)
        )

    st.image(image)

    img_bytes = BytesIO()
    image.save(img_bytes, format="PNG")

    st.download_button(
        "Download Image",
        img_bytes.getvalue(),
        "generated_image.png",
        "image/png"
    )