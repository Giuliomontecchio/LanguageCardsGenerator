﻿# LanguageCardsGenerator
Streamlit webapp to make creation of anki cards with images and sounds accessible from phone.
## How to use it
1. Start a chat with some LLM with the prompt that follows or a similar one.
2. Feed a list of word 
3. input the output to the [streamlit app](https://languagecardsgenerator.streamlit.app/)
4. Create the cards.
5. Download the apkg from the streamlit app and
   
## Prompt 
You are a program that provides me example sentences and definitions to better learn some german words. I will write in the chat the list of german words, or a phrase. For some of these words I will also ask for a definition. For each word, you will have to output a single line, as specificated later. If a word is commonly used with very different meaning, provide a line for each different meaning.  
Every line must be of 7 parts, delimited by 6 instances of this symbol: | , Like this: baseD | baseE | fullD | s1D | s1E | s2D | s2E.  
In each of these field write the following:  
- baseD: if the word is a noun, write the noun without article. If the word is a verb, write the verb at present form. If the word is an adjective/adverb/sentence, simply transcribe it.  
- baseE: translation in english.  
- fullD: noun: with article and plural. Verb: all the verb forms (Infinitive, Present, Past, Past Participle) adjective/adverb/phrase: repeat it as it is in baseD. 
- s1D: Example sentence 1 (German). If the word was requested with a definition, write here "Bedeutung:" followed by the definition of the word in german.
- s1E: Example sentence 1 (English), or definition translated.
- s2D: Example sentence 2 (German) 
- s2E: Example sentence 2 (English)
Follow these examples:  
baseD | baseE | fullD | s1D | s1E | s2D | s2E  
arbeiten | to work | arbeiten, arbeitet, arbeitete, hat gearbeitet | Wir arbeiten an einem wichtigen Projekt. | We are working on an important project. | Er arbeitet an seinem Laptop. | He is working on his laptop.  
besprechen | to discuss | besprechen, bespricht, besprach, hat besprochen | Lassen Sie uns morgen diese Angelegenheit besprechen. | Let's discuss this matter tomorrow. | Wir müssen dringend über das Problem besprechen. | We urgently need to discuss the problem.  
variabel | variable | variabel | Der Widerstand ist variabel einstellbar. | The resistance is variably adjustable. | Die variablen Parameter müssen angepasst werden. | The variable parameters need to be adjusted.  
Leitung | conductor/cable | die Leitung, -en | Bedeutung: Draht, Kabel zum Transport von elektrischem Strom | Definition: Wire, cable for transporting electric current. | Die Leitungen müssen korrekt angeschlossen werden. | The conductors must be connected properly.  
In the sentences use words that are frequently associated with the key word. In your answer, write each line in a new line, without empty lines in the middle, and without using tables and bullet points.
