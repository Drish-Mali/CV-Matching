from langdetect import detect



def lang_identiy(textual_content):
    """
    identify the language of the textual content and translate the content to english
    textual_content: str
    return:
    translated_content: str
    """
    language = detect(textual_content)
    return language


if __name__ == "__main__":
    text = "hola soy drish"
    language = lang_identiy(text)
    print(language)