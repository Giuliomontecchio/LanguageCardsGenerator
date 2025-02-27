import streamlit as st
import genanki

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

st.title("Anki Card Generator")

if 'cards' not in st.session_state:
    st.session_state.cards = []
    st.session_state.current_card = 0

user_input = st.text_area("Paste your text here (use '|' as field delimiter, one line per card):")

if st.button("Submit"):
    if user_input:
        st.session_state.cards = create_list_of_cards(user_input)
        st.session_state.current_card = 0
        st.success("Cards have been parsed successfully!")
        user_input = ""


if st.session_state.cards:
    current_card = st.session_state.current_card
    fields = st.session_state.cards[current_card]

    st.write(f"Card {current_card + 1}/{len(st.session_state.cards)}")

    for key, value in fields.items():
        new_value = st.text_input(f"{key}", value=value)
        fields[key] = new_value

    col1, col2 = st.columns(2)
    if col1.button("Previous") and current_card > 0:
        st.session_state.current_card -= 1

    if col2.button("Next") and current_card < len(st.session_state.cards) - 1:
        st.session_state.current_card += 1

    st.session_state.cards[current_card] = fields
    # File upload for images
    img1 = st.file_uploader("Upload Image 1", type=["png", "jpg", "jpeg"], key="img1_upload")
    img2 = st.file_uploader("Upload Image 2", type=["png", "jpg", "jpeg"], key="img2_upload")




