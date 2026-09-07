import os
import sys


def render_document(doc_path, topic):
    print(f"Preparing manual for '{topic}', please wait...")

    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except ImportError:
        print(
            "Error: The 'rich' library is required for advanced rendering. "
            "Run 'pip install rich' first."
        )
        sys.exit(1)

    with open(doc_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    console = Console()
    # this removes color
    # console = Console(color_system=None)
    md = Markdown(md_text)

    # Possible locations of less.exe
    less_paths = [
        r"C:\Program Files\Git\usr\bin\less.exe",
        r"C:\sw\PortableGit\usr\bin\less.exe",
    ]

    # Find the first less.exe that exists
    for less_path in less_paths:
        if os.path.exists(less_path):
            import ctypes

            buf = ctypes.create_unicode_buffer(512)

            ctypes.windll.kernel32.GetShortPathNameW(
                less_path,
                buf,
                512
            )

            short_less_path = buf.value

            # Tell Rich which pager to use
            os.environ["PAGER"] = f"{short_less_path} -R"
            # os.environ["PAGER"] = f'"{less_path}" -R'
            # os.environ["PAGER"] = f"{short_less_path} -F -X"

            break

    # Display the document using Rich's pager
    with console.pager(styles=True):  # from True
        console.print(
            f"\n--- Reading: {doc_path} ---\n",
            style="bold blue"
        )

        console.print(md)

        console.print(
            f"\n--- End of {topic} ---\n",
            style="bold blue"
        )
