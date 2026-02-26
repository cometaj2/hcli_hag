class Formatting:
    SEPARATOR = "----"
    NEWLINES = "\n\n"
    SECTION_TEMPLATE = "{separator}{name}:{newlines}{content}{newlines}"

    @classmethod
    def format(cls, name, content):
        return cls.SECTION_TEMPLATE.format(
            separator=cls.SEPARATOR,
            name=name,
            content=content,
            newlines=cls.NEWLINES
        )

# Format a single row with fixed-width columns.
def format_row(user, repo):

    # Fixed column widths
    user_width = 10
#    repo_width = 19

    # Format fixed columns
    user_formatted = user[:user_width].ljust(user_width)
#    repo_formatted = repo[:repo_width].ljust(repo_width)

    # Output the row with full title (no truncation or trailing dots)
#    return f"{user_formatted}  {repo_formatted}"
    return f"{user_formatted}  {repo}"

# Format multiple context rows with a header.
# The title column is not constrained and has no trailing dots.
def format_rows(contexts):

    # Create header
    header = format_row("USER", "GIT REPO")

    # Format each row
    rows = [header]
    for ctx in contexts:
        row = format_row(
            ctx.get("user", ""),
            ctx.get("repo", ""),
        )
        rows.append(row)

    # Join rows with newlines
    return "\n".join(rows)
