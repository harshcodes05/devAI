from google import genai


client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents="Explain what a Python function is in one sentence.",
)

print("RESPONSE:")
print(response.text)