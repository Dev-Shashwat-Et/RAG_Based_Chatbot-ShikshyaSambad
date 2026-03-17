import markdown
from django.shortcuts import render
# This connects to the bot_engine.py file you placed in the chat folder
from .bot_engine import ask_study_abroad_bot


def chat_home(request):
    """
    Main view for the ShikshyaSambad AI Assistant.
    Handles user queries, AI generation, and Markdown-to-HTML conversion.
    """
    response = ""
    query = ""

    if request.method == "POST":
        # Get the query from the name="user_query" input in your HTML
        query = request.POST.get("user_query", "").strip()

        if query:
            # 1. Get raw text from the AI (contains pipes | and stars *)
            raw_answer = ask_study_abroad_bot(query)

            # 2. Convert raw AI text into valid HTML
            # We use 'extra' specifically to handle the tables you saw in your screenshots.
            # We use 'sane_lists' to ensure * turns into real <ul><li> bullets.
            # We use 'nl2br' so that the AI's line breaks aren't ignored by the browser.
            response = markdown.markdown(
                raw_answer.strip(),  # strip() ensures no leading spaces break the table
                extensions=[
                    'extra',          # Handles tables and attributes
                    'sane_lists',     # Better bullet point handling
                    'nl2br',          # Converts newlines to <br>
                    'fenced_code',    # Handles code blocks if the AI uses them
                    'tables'          # Explicitly enables table formatting
                ]
            )

    # Return the data to index.html
    return render(request, "chat/index.html", {
        "response": response,
        "query": query
    })
