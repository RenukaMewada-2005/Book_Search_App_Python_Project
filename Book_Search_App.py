import requests
import json
import os

#Custom Exceptions
class APIError(Exception):
    """Raised when the API call fails (HTTP error, network issues, or bad response)"""
    pass

class FileLoadError(Exception):
    """Raised when reading from or writing to the library file fails"""
    pass


class Book:
    """Represents a single book with key metadata"""
    
    def __init__(self, title, author, publisher=None, isbn=None):
        self.title = title
        self.author = author
        self.publisher = publisher
        self.isbn = isbn

    def display_info(self):
        """Generates a formatted string for console display"""
        info_lines = [f"Title: {self.title}", f"Author: {self.author}"]
        if self.publisher:
            info_lines.append(f"Publisher: {self.publisher}")
        if self.isbn:
            info_lines.append(f"ISBN: {self.isbn}")
        return "\n".join(info_lines)

    def to_dict(self):
        """Converts the Book object to a dictionary for JSON serialization"""
        return self.__dict__

    def __repr__(self):
        return f"<Book title='{self.title[:30]}...' author='{self.author}'>"

#API Interaction
class APIClient:
    """Handles external API calls for book searching"""
    
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def search_books(self, query: str) -> list[dict]:
        """
        Executes the book search. Returns a list of simplified book data dicts.
        Raises APIError on communication failure
        """
        params = {'q': query, 'maxResults': 8} 
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5) 
            response.raise_for_status() 
            
            data = response.json()
            if not data.get('items'):
                return []
            
            parsed_books = []
            for item in data['items']:
                volume_info = item.get('volumeInfo', {})
                authors_list = volume_info.get('authors', ['Unknown Author'])
                
                # Simplified ISBN extraction
                identifiers = volume_info.get('industryIdentifiers', [])
                isbn = next((i['identifier'] for i in identifiers if i.get('type') == 'ISBN_13'), 
                            identifiers[0].get('identifier') if identifiers else None)

                book_data = {
                    'title': volume_info.get('title', 'N/A Title'),
                    'author': ', '.join(authors_list),
                    'publisher': volume_info.get('publisher'),
                    'isbn': isbn
                }
                parsed_books.append(book_data)
                
            return parsed_books
            
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code if 'response' in locals() else 'Unknown'
            raise APIError(f"HTTP Error {status_code}: The API request failed. (Details: {e})") from e
        except requests.exceptions.Timeout as e:
            raise APIError(f"API connection timed out after 5 seconds.") from e
        except requests.exceptions.RequestException as e:
            raise APIError(f"A network issue occurred during API call: {e}") from e
        except Exception as e:
            raise APIError(f"Failed to process API response: {type(e).__name__}: {e}") from e

#File Management
class FileManager:
    """Handles loading and saving the local library data to a JSON file"""

    DEFAULT_FILE = 'my_library.json'

    def __init__(self, file_path=DEFAULT_FILE):
        self.file_path = file_path

    def load_library(self) -> list[dict]:
        """Loads data from the JSON file. Returns [] if missing."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    print("Warning: Library file content was not a list. Re-initializing.")
                    return []
                return data
        except FileNotFoundError:
            print(f"No library file found at '{self.file_path}'. Starting fresh.")
            return []
        except json.JSONDecodeError as e:
            raise FileLoadError(f"Library file is corrupted (JSON Error).") from e
        except IOError as e:
            raise FileLoadError(f"Critical IO error while reading file: {e}") from e

    def save_library(self, library_data: list[dict]):
        """Writes the library data to the JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(library_data, f, indent=4)
        except IOError as e:
            raise FileLoadError(f"Failed to write library to disk: {e}") from e
        except Exception as e:
            raise FileLoadError(f"Unexpected error during saving: {e}") from e

# Main Application
class BookSearchApp:
    """The main application class that ties everything together"""

    def __init__(self):
        self.api_client = APIClient()
        self.file_manager = FileManager()
        self.my_library: list[Book] = []
        self._load_initial_library()

    def _load_initial_library(self):
        """Initial load of the library from disk"""
        try:
            saved_data = self.file_manager.load_library()
            self.my_library = [Book(**data) for data in saved_data]
            print(f"Startup: Successfully loaded {len(self.my_library)} book(s) from local library.")
        except FileLoadError as e:
            print(f"CRITICAL FILE ERROR: Cannot load library: {e}")
            self.my_library = [] 

    def _display_results(self, results: list[Book]):
        """Prints formatted search results."""
        print("\n--- Search Results ---")
        if not results:
            print("No books found matching your query.")
            return
        for i, book in enumerate(results):
            print(f"[{i + 1}]\n{book.display_info().strip()}\n----------------------")

    def handle_search(self):
        """Handles user search input, API call, and result processing/saving."""
        query = input("Enter search keyword (title/author): ").strip()
        if not query:
            print("Search query cannot be empty. Returning to menu.")
            return
        
        try:
            print(f"\nSearching API for '{query}'...")
            search_results_data = self.api_client.search_books(query)
            
            if not search_results_data:
                print("Search finished. No books found.")
                return
            
            temp_results = [Book(**data) for data in search_results_data]
            self._display_results(temp_results)
            self._handle_save_selection(temp_results)
            
        except APIError as e:
            print(f"\nAPI SEARCH FAILED: {e}")

    def _handle_save_selection(self, results: list[Book]):
        """Allows user to save a book from search results to their library."""
        while True:
            selection = input("Enter book number to save, or 'n' to cancel: ").lower().strip()
            if selection == 'n': return

            try:
                index = int(selection) - 1
                if 0 <= index < len(results):
                    book_to_save = results[index]
                    self.my_library.append(book_to_save)
                    
                    library_data_to_save = [b.to_dict() for b in self.my_library]
                    self.file_manager.save_library(library_data_to_save)
                    
                    print(f"\nSUCCESS: '{book_to_save.title}' added and library saved.")
                    return
                else:
                    print("Invalid selection number. Must be one of the options listed.")
            
            except ValueError:
                print("Invalid input. Please enter a number or 'n'.")
            except FileLoadError as e:
                print(f"FATAL SAVE ERROR: Could not save the library after adding the book. {e}")
                return 

    def handle_view_library(self):
        """Displays all books in the user's local library."""
        print("\n--- Your Saved Library ---")
        if not self.my_library:
            print("Your library is currently empty. Try searching for some books!")
        else:
            for i, book in enumerate(self.my_library):
                print(f"[{i+1}] {book.title} by {book.author}")

    def main_menu(self):
        """Displays the main menu options."""
        print("\n==================================")
        print("📖 Book Search & Library App")
        print("==================================")
        print("1. Search Books (via External API)")
        print("2. View My Saved Library (File)")
        print("3. Exit Application")
        return input("Enter your choice : ").strip()

    def run(self):
        """Main application loop."""
        while True:
            choice = self.main_menu()
            
            if choice == '1':
                self.handle_search()
            elif choice == '2':
                self.handle_view_library()
            elif choice == '3':
                print("Exiting application. Thanks for using the Book Search App!")
                break
            else:
                print(f"'{choice}' is not a valid choice. Please select 1, 2, or 3.")

#Entry point
if __name__ == '__main__':
    app = BookSearchApp()
    app.run()