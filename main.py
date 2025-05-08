from io import BytesIO
import streamlit as st
import genanki
from gtts import gTTS
from PIL import Image
import requests
from bs4 import BeautifulSoup
from st_clickable_images import clickable_images
import tempfile
import os

# Parser function
def create_list_of_cards(src_text: str) -> list[dict]:
    """
Creates a list of dictionaries corresponding to fields from a given text.

Args:
    src_text (str): The text to parse, with each line representing a record
        and each field separated by a '|' character.

Returns:
    list[dict]: A list of dictionaries, where each dictionary represents a card
        with fields 'baseT', 'baseS', 'fullT', 's1T', 's1S', 's2T', and 's2S'.
"""
    list_of_cards = []
    header = ["baseT", "baseS", "fullT", "s1T", "s1S", "s2T", "s2S"]
    lines = src_text.strip().splitlines()
    for line in lines:
        if line.strip():  # Check if the line is not empty
            parts = line.split("|")
            record = {header[i]: parts[i].strip() if i < len(parts) else "" for i in range(len(header))}
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

def create_note(fields, selected_language):

    # Style and types of cards
    css = """.card{
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
    }"""

    model_card_generator = genanki.Model(
    1284830180,
    'Language (and reversed card) card generator',
    fields=[
        {'name': 'baseS'},
        {'name': 'baseT'},
        {'name': 'AbaseT'},
        {'name': 'fullT'},
        {'name': 'AfullT'},
        {'name': 's1T'},
        {'name': 'As1T'},
        {'name': 's2T'}, 
        {'name': 'As2T'},
        {'name': 'image1'},
        {'name': 'image2'},
        ],
    templates=[
    {'name': 'Card 1',
    'qfmt': '{{baseS}}<br>{{image1}} {{image2}}',
    'afmt': '{{baseS}}<br>{{image1}} {{image2}} <br> {{fullT}} {{AfullT}}'
    '<hr id="answer">{{s1T}} {{As1T}}<br> {{s2T}} {{As2T}}',
    },
    {'name': 'Card 2',
    'qfmt': '{{baseT}} {{AbaseT}}',
    'afmt': '{{fullT}} {{AfullT}}<br>{{baseS}}'
    '<hr id="answer">{{image1}} {{image2}}<br> {{s1T}}{{As1T}}<br> {{s2T}} {{As2T}}',
    }
    ],
    css = css)

    fields_note = [fields['baseS']]
    # generate audio
    for i, key in enumerate(['baseT','fullT', 's1T', 's2T']):
        if fields[key] == "":
            fields_note.extend([fields[key], ''])
            continue
        sound = gTTS(text=fields[key], lang=selected_language, slow=False)
        sound.save(f"sound{st.session_state.index}_{i}.mp3")
        st.session_state.all_media.append(f"sound{st.session_state.index}_{i}.mp3")
        if key == 'fullT':
            fields['fullT'] = color_gender(fields['fullT'], selected_language)
        fields_note.extend([fields[key], f'[sound:sound{st.session_state.index}_{i}.mp3]'])

    # Add images dynamically
    images = [f'<img src="{img_name}">' for img_name in st.session_state.image_filename]
    while len(images) < 2:  # Ensure 2 image placeholders
        images.append('')

    fields_note.extend(images)  # Add images to the fields

    # Create the note
    note = genanki.Note(model=model_card_generator, fields=fields_note)

    # Extend the all media file
    for img_name in st.session_state.image_filename:
        st.session_state.all_media.append(img_name)

    st.session_state.deck.add_note(note)  # Modify deck in session_state
    st.session_state.index += 1
    st.session_state.image_filename = []
    st.session_state.image_urls_to_add = []

def create_deck():
    # Generate the Anki package and save it to a file
    package = genanki.Package(st.session_state.deck)
    package.media_files = st.session_state.all_media

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".apkg")
    package.write_to_file(temp_file.name)
    temp_file.close()  # Ensure file is saved

    return temp_file.name

def get_image_urls(keyword:str, subdomain:str)->list[str]:
    # Starting from a keyword, creates a list of URLs which direct to images.

    # Create a Google Images URL for the search term
    search_url = f"https://www.google.{subdomain}/search?q={keyword}&tbm=isch"
    # Send an HTTP GET request to the URL
    response = requests.get(search_url, timeout=10)
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')
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
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.set_page_config(page_title="Anki Card Generator")
    # Initialize deck and all_media in session_state (if not already initialized)
    if 'cards' not in st.session_state:
        st.session_state.cards = []
        st.session_state.current_card = 0
        st.session_state.submitted = False  # Track submission state
    if "all_media" not in st.session_state:
        st.session_state.all_media = []  # Store media lis
    if 'index' not in st.session_state: # index to go up for each added card?
        st.session_state.index = 0
    if 'image_urls_to_add' not in st.session_state:
        st.session_state.image_urls_to_add = []
    if 'image_filename' not in st.session_state:
        st.session_state.image_filename = []
    if 'image_viewer_urls' not in st.session_state:
        st.session_state.image_viewer_urls = []

    if not st.session_state.submitted:
        # Define language options
        language_options = ["de", "es", "fr"]

        # Create the selectbox
        selected_language = st.selectbox(
            "Choose a language",
            language_options,
            index = 0
        )

        st.session_state.selected_language = selected_language

        user_input = st.text_area("Paste your text here (use '|' as field delimiter, one line per card):")

        if st.button("Submit"):
            if user_input:
                st.session_state.cards = create_list_of_cards(user_input)
                st.session_state.current_card = 0
                st.session_state.submitted = True  # Hide inputs after submission
                if 'deck' not in st.session_state and 'selected_language' in st.session_state:
                    deck_info = {
                        "de": (87654321, "Deutsch"),
                        "es": (87654322, "Espanol"),
                        "fr": (87654323, "Francais")
                        }
                    lang = st.session_state.selected_language
                    deck_id, deck_name = deck_info.get(lang, (87654321, "Deutsch"))
                    st.session_state.deck = genanki.Deck(deck_id, deck_name)
            st.rerun()

    else:
        if st.session_state.image_viewer_urls:

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
                        st.session_state.image_filename.append(f"image{st.session_state.index}_{i}.png")
                        image.save(f"image{st.session_state.index}_{i}.png")
                    st.success("Images saved successfully!")
                    st.session_state.image_viewer_urls = []
                    del st.session_state["image_clicked"]
                    st.rerun()
                
            if "clicked" not in st.session_state:  # Ensure `clicked` is only computed once
                st.session_state.image_clicked = clickable_images(
                    st.session_state.image_viewer_urls,
                    div_style={
                        "display": "flex",
                        "justify-content": "center",
                        "flex-wrap": "wrap",
                        "gap": "2px",  # Space between images
                        "padding": "1px"
                    },
                    img_style={
                        "margin": "5px", 
                        "max-width": "none", 
                        "max-height": "none", 
                        "width": "auto", 
                        "height": "auto", 
                        "object-fit": "contain"
                    },
                    key="image_viewer"
                )

            if st.session_state.image_clicked>-1:
                st.subheader("Selected images")
                st.session_state.image_urls_to_add.append(st.session_state.image_viewer_urls[st.session_state.image_clicked])
                st.session_state.image_urls_to_add = st.session_state.image_urls_to_add[-2:]
                st.image(st.session_state.image_urls_to_add)

        if st.session_state.cards and not st.session_state.image_viewer_urls:
            current_card = st.session_state.current_card
            fields = st.session_state.cards[current_card]
            
            col1, col2, col3, col4, col5 = st.columns(5)

            if col1.button("Previous") and current_card > 0:
                st.session_state.current_card -= 1

            if col3.button("Next") and current_card < len(st.session_state.cards) - 1:
                st.session_state.current_card += 1
            
            current_card = st.session_state.current_card
            fields = st.session_state.cards[current_card]

            with col2:
                st.write(f"Card {current_card + 1}/{len(st.session_state.cards)}")
            
            if col4.button("Image"):
                st.session_state.image_viewer_urls = get_image_urls(fields['baseT'], st.session_state.selected_language)
                st.rerun()

            if col5.button("Add Card"):
                create_note(fields, st.session_state.selected_language)
                if current_card < len(st.session_state.cards) - 1:
                    st.session_state.current_card += 1
                st.rerun()

            for key, value in fields.items():
                new_value = st.text_input(f"{key}", value=value)
                fields[key] = new_value

            if st.button("Add Deck"):
                deck_path = create_deck()
                st.success("Deck added!")

                download_name = f"{st.session_state.deck.name}.apkg"
            
                with open(deck_path, "rb") as file:
                    st.download_button(
                        label="Download Deck (.apkg)",
                        data=file,
                        file_name=download_name,  # Using the same name as the generated file
                        mime="application/octet-stream",
                        on_click=reset_app
                    )

if __name__ == "__main__":
    main()