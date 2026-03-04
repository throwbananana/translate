from online_search import OnlineSearchManager
from config_manager import ConfigManager

def test_search():
    print("Initializing ConfigManager and OnlineSearchManager...")
    cm = ConfigManager()
    osm = OnlineSearchManager(cm)
    
    query = "python"
    print(f"Attempting to search Anna's Archive for '{query}'...")
    
    try:
        # This calls the method that previously crashed
        results = osm.search_annas_archive(query)
        
        print(f"Search finished. Found {len(results)} results.")
        if results:
            print("First result title:", results[0].get('title'))
            print("First result URL:", results[0].get('url'))
        else:
            print("No results found, but no crash occurred.")
            
    except Exception as e:
        print(f"!!! CRASH DETECTED !!!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search()
