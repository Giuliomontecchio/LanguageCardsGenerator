from io import BytesIO
import streamlit as st
import genanki
from gtts import gTTS
from PIL import Image
import requests
from bs4 import BeautifulSoup
from st_clickable_images import clickable_images
import os


# Parser function
def create_list_of_cards(src_text: str, mode: str = "lexicon") -> list[dict]:
    """
    Creates a list of dictionaries corresponding to fields from a given text.

    Args:
        src_text (str): The text to parse
        mode (str): The mode - "lexicon", "pronunciation", or "grammar"

    Returns:
        list[dict]: A list of dictionaries representing cards based on the mode
    """
    list_of_cards = []

    if mode == "lexicon":
        # Original lexicon mode
        header = ["baseT", "baseS", "fullT", "s1T", "s1S", "s2T", "s2S"]
        lines = src_text.strip().splitlines()
        for line in lines:
            if line.strip():  # Check if the line is not empty
                parts = line.split("|")
                record = {
                    header[i]: parts[i].strip() if i < len(parts) else ""
                    for i in range(len(header))
                }
                list_of_cards.append(record)

    elif mode == "pronunciation":
        # Pronunciation mode - each line is a word/sentence
        lines = src_text.strip().splitlines()
        for line in lines:
            if line.strip():
                record = {"word": line.strip()}
                list_of_cards.append(record)

    elif mode == "grammar":
        # Grammar mode - fields separated by " | "
        lines = src_text.strip().splitlines()
        for line in lines:
            if line.strip():
                parts = line.strip().split(" | ")
                if len(parts) >= 2:
                    record = {
                        "Front": parts[0].strip(),
                        "Back": parts[1].strip(),
                        "Rule": parts[2].strip() if len(parts) > 2 else "",
                    }
                    list_of_cards.append(record)

    return list_of_cards


def color_gender(field, selected_language):
    if selected_language == "de":
        if field.startswith("die "):
            field = f'<span style="color: rgb(255, 88, 111);">{field}</span>'
        elif field.startswith("das "):
            field = f'<span style="color: rgb(88, 255, 101);">{field}</span>'
        elif field.startswith("der "):
            field = f'<span style="color: rgb(88, 141, 255);">{field}</span>'
    return field


def create_note(fields, selected_language, mode="lexicon"):
    """Create an Anki note based on the mode."""

    # Common CSS style
    css = """.card{
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
    }"""

    model_card_generator = None

    if mode == "lexicon":
        # Original lexicon model
        model_card_generator = genanki.Model(
            1284830180,
            "Language (and reversed card) card generator",
            fields=[
                {"name": "baseS"},
                {"name": "baseT"},
                {"name": "AbaseT"},
                {"name": "fullT"},
                {"name": "AfullT"},
                {"name": "s1T"},
                {"name": "As1T"},
                {"name": "s2T"},
                {"name": "As2T"},
                {"name": "image1"},
                {"name": "image2"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{baseS}}<br>{{image1}} {{image2}}",
                    "afmt": "{{baseS}}<br>{{image1}} {{image2}} <br> {{fullT}} {{AfullT}}"
                    '<hr id="answer">{{s1T}} {{As1T}}<br> {{s2T}} {{As2T}}',
                },
                {
                    "name": "Card 2",
                    "qfmt": "{{baseT}} {{AbaseT}}",
                    "afmt": "{{fullT}} {{AfullT}}<br>{{baseS}}"
                    '<hr id="answer">{{image1}} {{image2}}<br> {{s1T}}{{As1T}}<br> {{s2T}} {{As2T}}',
                },
            ],
            css=css,
        )

        fields_note = [fields["baseS"]]
        # generate audio
        for i, key in enumerate(["baseT", "fullT", "s1T", "s2T"]):
            if fields[key] == "":
                fields_note.extend([fields[key], ""])
                continue
            sound = gTTS(text=fields[key], lang=selected_language, slow=False)
            sound.save(f"sound{st.session_state.index}_{i}.mp3")
            st.session_state.all_media.append(f"sound{st.session_state.index}_{i}.mp3")
            if key == "fullT":
                fields["fullT"] = color_gender(fields["fullT"], selected_language)
            fields_note.extend(
                [fields[key], f"[sound:sound{st.session_state.index}_{i}.mp3]"]
            )

        # Add images dynamically
        images = [
            f'<img src="{img_name}">' for img_name in st.session_state.image_filename
        ]
        while len(images) < 2:  # Ensure 2 image placeholders
            images.append("")
        fields_note.extend(images)  # Add images to the fields

        # Extend the all media file
        for img_name in st.session_state.image_filename:
            st.session_state.all_media.append(img_name)

    elif mode == "pronunciation":
        # Pronunciation model (from AusspracheDeutsch.py)
        model_card_generator = genanki.Model(
            1081735104,
            "Simple Model with Media",
            fields=[
                {"name": "Question"},
                {"name": "MyMedia"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}",
                    "afmt": '{{FrontSide}}<hr id="answer">{{MyMedia}}',
                },
            ],
            css=css,
        )

        word = fields["word"]
        sound = gTTS(text=word, tld="com", lang=selected_language, slow=False)
        sound.save(f"sound_{word}_{st.session_state.index}.mp3")
        st.session_state.all_media.append(f"sound_{word}_{st.session_state.index}.mp3")

        fields_note = [word, f"[sound:sound_{word}_{st.session_state.index}.mp3]"]

    elif mode == "grammar":
        # Grammar model (unified model that handles both with/without rules)
        model_card_generator = genanki.Model(
            1091735125,
            "Simple Model with Media",
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
                {"name": "MyMedia"},
                {"name": "explanation"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}",
                    "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}<br>{{MyMedia}}<br>{{explanation}}',
                },
            ],
            css=css,
        )

        sound = gTTS(text=fields["Back"], lang=selected_language, slow=False)
        sound.save(f"sound_grammar_{st.session_state.index}.mp3")
        st.session_state.all_media.append(f"sound_grammar_{st.session_state.index}.mp3")

        fields_note = [
            fields["Front"],
            fields["Back"],
            f"[sound:sound_grammar_{st.session_state.index}.mp3]",
            fields.get("Rule", ""),  # Empty string if no rule
        ]

    # Create the note
    note = genanki.Note(model=model_card_generator, fields=fields_note)
    st.session_state.deck.add_note(note)  # Modify deck in session_state
    st.session_state.index += 1

    # Reset image-related session state for lexicon mode
    if mode == "lexicon":
        st.session_state.image_filename = []
        st.session_state.image_urls_to_add = []


def create_deck():
    # Create the Anki package
    package = genanki.Package(st.session_state.deck)
    package.media_files = st.session_state.all_media

    # Write package to in-memory buffer instead of file
    output = BytesIO()
    package.write_to_file(
        output
    )  # This works because genanki supports file-like objects

    # Move the cursor to the beginning of the buffer
    output.seek(0)

    # Save in session state for later use (e.g., download)
    st.session_state.apkg_data = output.read()
    st.session_state.file_name = f"{st.session_state.deck.name}.apkg"


def get_image_urls(keyword: str, subdomain: str) -> list[str]:
    # Starting from a keyword, creates a list of URLs which direct to images.

    # Create a Google Images URL for the search term
    search_url = f"https://www.google.{subdomain}/search?q={keyword}&tbm=isch"
    # Send an HTTP GET request to the URL
    response = requests.get(search_url, timeout=10)
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, "html.parser")
    # Find image links in the page source
    list_of_tags = soup.find_all("img")
    list_of_urls = []
    for tag in list_of_tags:
        list_of_urls.append(tag.get("src"))
    # On google image, first one is google logo
    list_of_urls.pop(0)
    return list_of_urls


def load_images(urls):
    """Download and return images from URLs."""
    images = []
    for url in urls:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            images.append(img)
    return images


def reset_app():
    st.session_state.reset = True


def main():
    if st.session_state.get("reset"):
        # Clean local files
        files_to_delete = st.session_state.all_media + [st.session_state.file_name]

        for path in files_to_delete:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    st.warning(f"Could not delete {path}: {e}")

        # Clean session states
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.rerun()

    st.set_page_config(page_title="Anki Card Generator")
    # Initialize deck and all_media in session_state (if not already initialized)
    if "card_mode" not in st.session_state:
        st.session_state.card_mode = "lexicon"
    if "cards" not in st.session_state:
        st.session_state.cards = []
        st.session_state.current_card = 0
        st.session_state.submitted = False  # Track submission state
    if "all_media" not in st.session_state:
        st.session_state.all_media = []  # Store media lis
    if "index" not in st.session_state:  # index to go up for each added card?
        st.session_state.index = 0
    if "image_urls_to_add" not in st.session_state:
        st.session_state.image_urls_to_add = []
    if "image_filename" not in st.session_state:
        st.session_state.image_filename = []
    if "image_viewer_urls" not in st.session_state:
        st.session_state.image_viewer_urls = []

    if not st.session_state.submitted:
        # Define language options
        language_options = ["de", "es", "fr"]

        # Create the selectbox for language
        selected_language = st.selectbox("Choose a language", language_options, index=0)
        st.session_state.selected_language = selected_language

        # Create the selectbox for card mode
        mode_options = ["lexicon", "pronunciation", "grammar"]
        mode_descriptions = {
            "lexicon": "Lexicon cards (use '|' as field delimiter)",
            "pronunciation": "Pronunciation cards (one word/sentence per line)",
            "grammar": "Grammar cards (Front | Back | Rule - rule is optional)",
        }

        selected_mode = st.selectbox(
            "Choose card type",
            mode_options,
            format_func=lambda x: mode_descriptions[x],
            index=0,
        )
        st.session_state.card_mode = selected_mode

        # Dynamic text area label based on mode
        if selected_mode == "lexicon":
            text_area_label = (
                "Paste your text here (use '|' as field delimiter, one line per card):"
            )
            text_area_help = "Format: baseT|baseS|fullT|s1T|s1S|s2T|s2S"
        elif selected_mode == "pronunciation":
            text_area_label = "Enter words/sentences (one per line):"
            text_area_help = "Each line should contain a single word or sentence to practice pronunciation"
        else:  # grammar
            text_area_label = "Enter grammar exercises (Front | Back | Rule):"
            text_area_help = "Format: Question | Answer | Rule (rule is optional)"

        user_input = st.text_area(text_area_label, help=text_area_help)

        if st.button("Submit"):
            if user_input:
                st.session_state.cards = create_list_of_cards(user_input, selected_mode)
                st.session_state.current_card = 0
                st.session_state.submitted = True  # Hide inputs after submission
                if (
                    "deck" not in st.session_state
                    and "selected_language" in st.session_state
                ):
                    # Different deck info based on mode
                    if selected_mode == "lexicon":
                        deck_info = {
                            "de": (87654321, "Deutsch"),
                            "es": (87654322, "Espanol"),
                            "fr": (87654323, "Francais"),
                        }
                    elif selected_mode == "pronunciation":
                        deck_info = {
                            "de": (100234568, "DeutschAussprache"),
                            "es": (100234569, "EspanolPronunciacion"),
                            "fr": (100234570, "FrancaisPrononciation"),
                        }
                    else:  # grammar
                        deck_info = {
                            "de": (1234567, "Grammar_Deutsch"),
                            "es": (1234568, "Grammar_Espanol"),
                            "fr": (1234569, "Grammar_Francais"),
                        }

                    lang = st.session_state.selected_language
                    deck_id, deck_name = deck_info.get(
                        lang, list(deck_info.values())[0]
                    )
                    st.session_state.deck = genanki.Deck(deck_id, deck_name)

                # For pronunciation and grammar modes, process all cards automatically
                if selected_mode in ["pronunciation", "grammar"]:
                    progress_bar = st.progress(0)
                    st.info(f"Processing {len(st.session_state.cards)} cards...")

                    for i, card in enumerate(st.session_state.cards):
                        create_note(card, selected_language, selected_mode)
                        progress_bar.progress((i + 1) / len(st.session_state.cards))

                    create_deck()
                    st.success("All cards processed successfully!")
                    progress_bar.empty()
            st.rerun()

    else:
        # Check if we're in lexicon mode for the full card review interface
        if st.session_state.card_mode == "lexicon":
            # Lexicon mode - full interface with image support and card review
            show_image_interface = True

            if show_image_interface and st.session_state.image_viewer_urls:
                col_cancel, col_add = st.columns(2)

                with col_cancel:
                    if st.button("Cancel"):
                        st.session_state.image_viewer_urls = []
                        st.session_state.image_urls_to_add = []
                        if "image_clicked" in st.session_state:
                            del st.session_state["image_clicked"]
                        st.rerun()

                with col_add:
                    if st.button("Add images"):
                        images_to_save = load_images(st.session_state.image_urls_to_add)
                        st.session_state.image_filename = []
                        for i, image in enumerate(images_to_save):
                            st.session_state.image_filename.append(
                                f"image{st.session_state.index}_{i}.png"
                            )
                            image.save(f"image{st.session_state.index}_{i}.png")
                        st.success("Images saved successfully!")
                        st.session_state.image_viewer_urls = []
                        del st.session_state["image_clicked"]
                        st.rerun()

                if (
                    "clicked" not in st.session_state
                ):  # Ensure `clicked` is only computed once
                    st.session_state.image_clicked = clickable_images(
                        st.session_state.image_viewer_urls,
                        div_style={
                            "display": "flex",
                            "justify-content": "center",
                            "flex-wrap": "wrap",
                            "gap": "2px",  # Space between images
                            "padding": "1px",
                        },
                        img_style={
                            "margin": "5px",
                            "max-width": "none",
                            "max-height": "none",
                            "width": "auto",
                            "height": "auto",
                            "object-fit": "contain",
                        },
                        key="image_viewer",
                    )

                if st.session_state.image_clicked > -1:
                    st.subheader("Selected images")
                    st.session_state.image_urls_to_add.append(
                        st.session_state.image_viewer_urls[
                            st.session_state.image_clicked
                        ]
                    )
                    st.session_state.image_urls_to_add = (
                        st.session_state.image_urls_to_add[-2:]
                    )
                    st.image(st.session_state.image_urls_to_add)

            if st.session_state.cards and not (
                show_image_interface and st.session_state.image_viewer_urls
            ):
                current_card = st.session_state.current_card
                fields = st.session_state.cards[current_card]

                # Lexicon mode UI
                col1, col2, col3, col4, col5 = st.columns(5)

                if col1.button("Previous") and current_card > 0:
                    st.session_state.current_card -= 1

                if (
                    col3.button("Next")
                    and current_card < len(st.session_state.cards) - 1
                ):
                    st.session_state.current_card += 1

                current_card = st.session_state.current_card
                fields = st.session_state.cards[current_card]

                with col2:
                    st.write(f"Card {current_card + 1}/{len(st.session_state.cards)}")

                if col4.button("Image"):
                    st.session_state.image_viewer_urls = get_image_urls(
                        fields["baseT"], st.session_state.selected_language
                    )
                    st.rerun()

                if col5.button("Add Card"):
                    create_note(
                        fields,
                        st.session_state.selected_language,
                        st.session_state.card_mode,
                    )
                    if current_card < len(st.session_state.cards) - 1:
                        st.session_state.current_card += 1
                    st.rerun()

                # Show editable fields for lexicon cards
                for key, value in fields.items():
                    new_value = st.text_input(f"{key}", value=value)
                    fields[key] = new_value

                if st.button("Add Deck"):
                    create_deck()

        # For all modes: show download button if deck is ready
        if "apkg_data" in st.session_state:
            st.download_button(
                label="Download Anki Deck",
                data=st.session_state.apkg_data,
                file_name=st.session_state.file_name,
                mime="application/octet-stream",
                on_click="ignore",
            )
            if st.button("Reset"):
                reset_app()
                st.rerun()


if __name__ == "__main__":
    main()
