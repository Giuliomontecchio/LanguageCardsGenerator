import streamlit as st
import genanki
from gtts import gTTS
from PIL import Image
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from st_clickable_images import clickable_images

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
        {'name': 'baseT'},
        {'name': 'AbaseT'},
        {'name': 'baseS'},
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
    {
    'name': 'Card 1',
    'qfmt': '{{baseS}}<br>{{image1}} {{image2}}',
    'afmt': '{{baseS}}<br>{{image1}} {{image2}} <br> {{fullT}} {{AfullT}}<hr id="answer">{{s1T}} {{As1T}}<br> {{s2T}} {{As2T}}',
    },
    {
    'name': 'Card 2',
    'qfmt': '{{baseT}} {{AbaseT}}',
    'afmt': '{{fullT}} {{AfullT}}<br>{{baseS}}<hr id="answer">{{image1}} {{image2}}<br> {{s1T}}{{As1T}}<br> {{s2T}} {{As2T}}',
    }
    ], 
    css = css)

    # generate audio
    for i, key in enumerate(['baseT','fullT', 's1T', 's2T']):
        if fields[key] == "": continue
        sound = gTTS(text=fields[key], lang=selected_language, slow=False)
        sound.save(f"sound{fields['baseT']}_{i}.mp3")

    # color the record according to the gender (after sound to avoid reading of html)
        fields['fullT'] = color_gender(fields['fullT'], selected_language)
    
    # audio can be substituted with a standard name and deleted right afterwards.

    note = genanki.Note(
            model=model_card_generator,
        fields=[
            fields['baseT'], f'[sound:sound{fields["baseT"]}_0.mp3]',
            fields['baseS'], fields['fullT'], f'[sound:sound{fields["baseT"]}_1.mp3]',
            fields['s1T'], f'[sound:sound{fields["baseT"]}_2.mp3]',
            fields['s2T'], f'[sound:sound{fields["baseT"]}_3.mp3]', '' , '' 
            ]
    )

    for ind in range(4):
        st.session_state.all_media.append(f"sound{fields['baseT']}_{ind}.mp3")

    st.session_state.deck.add_note(note)  # Modify deck in session_state

def create_deck():
    # Generate the Anki package and save it to a file
    package = genanki.Package(session_state.deck)
    package.media_files = session_state.all_media
    package.write_to_file('Mein_Deutsch.apkg')

def get_image_urls(keyword:str, subdomain:str)->list[str]:
    # Starting from a keyword, creates a list of URLs which direct to images.

    # Create a Google Images URL for the search term
    search_url = f"https://www.google.{subdomain}/search?q={keyword}&tbm=isch"
    # Send an HTTP GET request to the URL
    response = requests.get(search_url)
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
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            images.append(img)
    return images

def main():
    st.title("Anki Card Generator")
    # Initialize deck and all_media in session_state (if not already initialized)
    if 'cards' not in st.session_state:
        st.session_state.cards = []
        st.session_state.current_card = 0
        st.session_state.submitted = False  # Track submission state
    if "deck" not in st.session_state:
        deck_id = 87654321  
        deck_name = 'Mein_Deutsch'
        st.session_state.deck = genanki.Deck(deck_id, deck_name)  # Store the deck
    if "all_media" not in st.session_state:
        st.session_state.all_media = []  # Store media lis
    if 'index' not in st.session_state: # index to go up for each added card?
        st.session_state.index = 0
    if 'images_to_add' not in st.session_state:
        st.session_state.images_to_add = []
    if 'urls' not in st.session_state:
        st.session_state.urls = []
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = "de"

    if not st.session_state.submitted:

        # Define language options with flag emojis
        language_options = ["de", "es", "fr"]

        # Create the selectbox
        selected_language = st.selectbox(
            "Choose a language",
            language_options,
            index=0 
        )

        st.session_state.selected_language = selected_language

        user_input = st.text_area("Paste your text here (use '|' as field delimiter, one line per card):")

        if st.button("Submit"):
            if user_input:
                st.session_state.cards = create_list_of_cards(user_input)
                st.session_state.current_card = 0
                st.session_state.submitted = True  # Hide inputs after submission
                st.rerun()
    else:
        if st.session_state.urls:
            if "clicked" not in st.session_state:  # Ensure `clicked` is only computed once
                st.session_state.image_clicked = clickable_images(
                    st.session_state.urls, 
                    div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"}, 
                    key="image_viewer"
                )

            if st.button("Add images"):
                images_to_save = load_images(st.session_state.images_to_add)
                for i,image in enumerate(images_to_save):
                    image.save(f"image{st.session_state.index}_{i}.png")
                st.success("Images saved successfully!")
                st.session_state.urls = []
                del st.session_state["image_clicked"]
                st.rerun()

            if st.session_state.image_clicked>-1:
                st.subheader("Selected images")
                st.session_state.images_to_add.append(st.session_state.urls[st.session_state.image_clicked])
                st.session_state.images_to_add = st.session_state.images_to_add[-2:] 
                st.image(st.session_state.images_to_add)

        if st.session_state.cards:
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
                st.session_state.urls = get_image_urls(fields['baseT'], st.session_state.selected_language)
                st.rerun()

            if col5.button("Add Card"):
                create_note(fields, st.session_state.selected_language)
                st.success("Card added!")
            
        for key, value in fields.items():
            new_value = st.text_input(f"{key}", value=value)
            fields[key] = new_value

        if st.button("Add Deck"):
            create_deck()
            st.success("Deck added!")  # Show success message inside col2middle

if __name__ == "__main__":
    main()