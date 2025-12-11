import openai

async def handle(page_info, payload, deadline_ts):
    instruction = page_info.get("instruction", "") or page_info.get("html", "")
    
    if not instruction:
        return {"worker": "llm", "error": "no instruction found"}

    # Call GPT model
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts answers from instructions."},
            {"role": "user", "content": instruction}
        ]
    )

    answer = response["choices"][0]["message"]["content"].strip()

    return {"worker": "llm", "answer": answer}
