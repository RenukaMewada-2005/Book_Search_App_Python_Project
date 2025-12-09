# Overview :- 
This is a Python console application designed to help users search for books using an external API and manage a personal local library.
 It demonstrates best practices in Python development, including Object-Oriented Programming (OOP), robust error handling, 
and file persistence using JSON.

# Features :-
*External Search : Query the Google Books API using keywords (title, author) and retrieve relevant results.
*Local Persistence: Save selected books from the search results to a local library file (my_library.json).
* Library Management : View all books currently saved in the local library.
 Robust Error Handling : Custom exceptions and specific handlers for API errors (timeouts, HTTP failures) and file errors (corrupted JSON, IO issues).
* Clear OOP Structure : Organized into dedicated classes for Book Data, API Interaction, File Management, and the main Application loop.

# Key Python Classes :-
Class  Responsibility :-
*Book :-  Data model for a single book instance. Handles formatting (e.g., `display_info`). 
*APIClient :-  Manages external communication with the Google Books API using the `requests` library.
*FileManager :-  Handles  saving and loading the library data to/from the disk using the `json` module. 
*BookSearchApp :-  The main application logic, handling user input and coordinating between other classes. 
