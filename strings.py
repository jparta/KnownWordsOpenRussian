def instructions(words, supercls, info):
    return f"""Welcome to Known Words inquirer.
This application uses the openrussian.org API to find words you might want to learn.

After selecting your level of proficiency, words will appear on the screen.
Please press {words.SAVE_WORD_KEY.name.upper()} if you want to save the word, and {words.DISCARD_WORD_KEY.name.upper()} otherwise.
The words you selected will be shown at the end.

You may, at any time, press {supercls.MENU_KEY.name.upper()} to enter the menu, 
where you can, for example, start a new session.

Press {info.PROCEED_KEY.name.upper()} to proceed."""


def language_proficiency_prompt_long(words):
    return f"""Please indicate the proficiency level (CEFR) you want to target.
Change level with {words.PREVIOUS_KEY.name.upper()} and {words.NEXT_KEY.name.upper()}.
To select a level, press {words.SELECT_KEY.name.upper()}."""


def language_proficiency_prompt_short(words):
    return f"Change level with {words.PREVIOUS_KEY.name.upper()} and {words.NEXT_KEY.name.upper()}"


def word_decision_prompt(words, num_left):
    return f"""Press {words.SAVE_WORD_KEY.name.upper()} to save, {words.DISCARD_WORD_KEY.name.upper()} to discard.
{num_left} word{'' if num_left == 1 else 's'} left"""


def save_wordset_prompt(save, num_words, head):
    head_formatted = '\n'.join(['\t'+word for word in head])
    return f"""Press {save.SAVE_WORDSET_KEY.__str__().upper()} to save {num_words} words, {save.DISCARD_WORDSET_KEY.__str__().upper()} to discard.
The first {len(head)} words:\n\n{head_formatted}"""
