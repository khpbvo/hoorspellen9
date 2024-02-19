def execute_search(db_file, field1, searchword1, field2, searchword2, offset=0, limit=10):
    print(f"Debug: Preparing to execute search query with parameters - Field1: {field1}, Searchword1: {searchword1}, Field2: {field2}, Searchword2: {searchword2}, Offset: {offset}, Limit: {limit}")
    # Assuming the rest of the function setup goes here...

    # Right before executing the query
    print(f"Debug: Executing query: SELECT id, {field1}, {field2} FROM hoorspelen WHERE {field1} LIKE ? AND {field2} LIKE ? ORDER BY {field1} ASC LIMIT ? OFFSET ?")

    # After fetching the results
    print(f"Debug: Query executed. Number of results fetched: {len(results)}")
import pdb; pdb.set_trace()