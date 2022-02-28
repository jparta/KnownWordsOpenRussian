# KnownWords

Fetches Russian words from `api.openrussian.org`, and allows the user to select which ones to save.

# Dependencies

    pip install -r requirements.txt

# Features & todo

* API paging
  * ✔️ Fetching all words for proficiency level
  * ✔️ Using asynchronous requests
  * Store API's indices for words so that they can be ordered
* Menu
  * Close application
  * New session
  * Jump to word index x
  * Jump forward / backward in word list by y
  * Only show words which are not already in savefile?
  * Close menu