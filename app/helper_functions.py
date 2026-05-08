def split_text_by_words(text, max_chars=20):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # If current line is empty, start it with the word
        if current_line == "":
            current_line = word

        # If adding the next word still fits, add it
        elif len(current_line) + 1 + len(word) <= max_chars:
            current_line += " " + word

        # Otherwise, save current line and start a new one
        else:
            lines.append(current_line)
            current_line = word

    # Add last line
    if current_line:
        lines.append(current_line)

    return lines