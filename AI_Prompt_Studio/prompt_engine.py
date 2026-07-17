import ollama


def generate_prompt(category, idea):

    system = """
You are a professional AI prompt engineer.

Convert simple ideas into detailed prompts
for AI image generation.

Always include:

- Subject details
- Environment
- Lighting
- Camera angle
- Colors
- Style
- Quality

Return only final prompt.
"""


    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role":"system",
                "content":system
            },
            {
                "role":"user",
                "content":
                f"""
Category:
{category}

Idea:
{idea}
"""
            }
        ]
    )


    return response["message"]["content"]