from online_search import OnlineSearchManager
from config_manager import ConfigManager

def test_pagination():
    cm = ConfigManager()
    osm = OnlineSearchManager(cm)
    
    query = "Python"
    print(f"Searching for '{query}' on Anna's Archive...")
    
    print("Fetching Page 1...")
    p1 = osm.search_annas_archive(query, page=1)
    print(f"Page 1 results: {len(p1)}")
    if p1:
        print(f"First item P1: {p1[0]['title']}")
        
    print("\nFetching Page 2...")
    p2 = osm.search_annas_archive(query, page=2)
    print(f"Page 2 results: {len(p2)}")
    if p2:
        print(f"First item P2: {p2[0]['title']}")
        
    if not p1 or not p2:
        print("\nSearch failed to return results for one of the pages.")
        return

    # Check if results are different
    ids1 = {x['id'] for x in p1}
    ids2 = {x['id'] for x in p2}
    
    overlap = ids1.intersection(ids2)
    print(f"\nOverlap count: {len(overlap)}")
    
    if len(overlap) < len(p1) * 0.5: # Allow some overlap but they should be mostly different
        print("SUCCESS: Pages seem different.")
    else:
        print("WARNING: Pages seem very similar. Pagination might not be working.")

if __name__ == "__main__":
    test_pagination()
