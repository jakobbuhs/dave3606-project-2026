import json
import html
from collections import OrderedDict
import struct
from flask import Flask, Response, request
from time import perf_counter
import gzip

from database import Database

app = Flask(__name__)

CACHE_MAX_SIZE = 100
set_cache = OrderedDict()




@app.route("/")
def index():
    #Automatically close the file when done
    with open("templates/index.html") as f:
        template = f.read()

    return Response(template)

#Helper method for checking if the given encoding is legal
def is_valid_encoding(encoding):
    #List of allowed encodings. This program will only support UTF-16 and UTF-8. The default encoding is UTF-8
    legal_encoding_types = ["utf-8", "utf-16"]
    return encoding in legal_encoding_types

#Helper metthod for encoding content with correct utf
def encode_to_utf(content, utfType):
    match utfType:
        case "utf-8":
            return content.encode("utf-8")
        case "utf-16":
            return content.encode("utf-16")
        case _:
            return content.encode("utf-8")

def get_sets(db, encoding):
    #Automatically close the file when done
    with open("templates/sets.html") as f:
        template = f.read()
    start_time = perf_counter()

    try:
        #Perform query and save to local variable
        query_result = db.execute_and_fetch_all("select id, name from lego_set order by id")
        #Create a list
        rows = []

        #Append results in list
        for row in  query_result:
            html_safe_id = html.escape(row[0])
            html_safe_name = html.escape(row[1])
            #Append to list instead of string concatination
        
            rows.append(f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n')
        print(f"Time to render all sets: {perf_counter() - start_time}")
        
        #Make list into a string
        row_result = "".join(rows)
        #Return the string instead of row
        page_html = template.replace("{ROWS}", row_result)


        #Create placeholder for charset, alike rows. 
        if encoding == "utf-8":
            charset = '<meta charset="UTF-8">'
        else:
            charset = ""  # Fjern taggen

        page_html = page_html.replace("{CHARSET}", charset)

        #Print statement for debugging
        print(encoding)
        
        return page_html

    finally:
        #Close the db to prevent resource waste
        db.close()

   

@app.route("/sets")
def sets():
    #Retrieve encoding type from request
    encoding_type = request.args.get("encoding")

    #Validate encoding type
    utf_validation = is_valid_encoding(encoding_type)

    #Check if encoding type is legal. If not use default
    if not utf_validation:
        encoding_type = "utf-8"


    #Create database object
    db = Database()
    
    page_html = get_sets(db, encoding_type)

    #Encode page with given UTF
    encoded_page = encode_to_utf(page_html, encoding_type)

    #Compress page with GZIP
    compressed_page = gzip.compress(encoded_page)
    
    
    return Response(compressed_page, content_type="text/html; charset=" + encoding_type, headers={"Content-Encoding": "gzip", "Cache-Control": "max-age=60"})

def get_set(db, set_id):
    #Fetch given set from its id
    result = db.execute_and_fetch_all("select * from lego_set where id = %s", vars=(set_id,))
    row = result[0]

    #build data from given set
    data = {
        "id": row[0],
        "name": row[1],
        "year": row[2],
        "category": row[3],
        "bricks":[],
    }
    
    #Fetch bricks in given set from lego inventory
    bricks_result = db.execute_and_fetch_all(
    "select lego_brick.name, lego_inventory.color_id, lego_inventory.count "
    "from lego_inventory join lego_brick "
    "on lego_inventory.brick_type_id = lego_brick.brick_type_id "
    "and lego_inventory.color_id = lego_brick.color_id "
    "where set_id = %s",
    vars=(set_id,)

)   
    #Append brick to data
    for brick in bricks_result:
        data["bricks"].append({"name": brick[0], "color_id": brick[1], "count": brick[2]})

    return data


def get_set_binary(db, set_id):
    data = get_set(db, set_id)
    buf = bytearray()

    # Magic bytes to identify the file format
    buf.extend(b"LEGO")

    # Encode set id as: length (2 bytes) + utf-8 bytes
    id_bytes = data["id"].encode("utf-8")
    buf.extend(struct.pack(">H", len(id_bytes)))
    buf.extend(id_bytes)

    # Encode set name as: length (2 bytes) + utf-8 bytes
    name_bytes = data["name"].encode("utf-8")
    buf.extend(struct.pack(">H", len(name_bytes)))
    buf.extend(name_bytes)

    # Year as 2 bytes (0 if None)
    year = data["year"] if data["year"] is not None else 0
    buf.extend(struct.pack(">H", year))

    # Encode category as: length (2 bytes) + utf-8 bytes
    category = data["category"] or ""
    cat_bytes = category.encode("utf-8")
    buf.extend(struct.pack(">H", len(cat_bytes)))
    buf.extend(cat_bytes)

    # Number of bricks as 4 bytes
    bricks = data["bricks"]
    buf.extend(struct.pack(">I", len(bricks)))

    # Each brick: name_length (2 bytes) + name + color_id (4 bytes) + count (4 bytes)
    for brick in bricks:
        brick_name_bytes = brick["name"].encode("utf-8")
        buf.extend(struct.pack(">H", len(brick_name_bytes)))
        buf.extend(brick_name_bytes)
        buf.extend(struct.pack(">i", brick["color_id"]))
        buf.extend(struct.pack(">i", brick["count"]))

    return bytes(buf)


@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    #Automatically close the file when done
    with open("templates/set.html") as f:
        template = f.read()

    return Response(template)


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    if set_id is None:
        return Response("Missing id parameter", status=400)
    start_time = perf_counter()

    # Check cache first
    if set_id in set_cache:
        # Move to end (most recently used)
        set_cache.move_to_end(set_id)
        json_result = json.dumps(set_cache[set_id], indent=4)
        print(f"Cache HIT for {set_id}: {perf_counter() - start_time:.4f}s")
        return Response(json_result, content_type="application/json")

    # Cache miss — query the database
    db = Database()
    try:
        data = get_set(db, set_id)
    finally:
        db.close()
    json_result = json.dumps(data, indent=4)

    # Parse result and store in cache
    data = json.loads(json_result)
    set_cache[set_id] = data
    if len(set_cache) > CACHE_MAX_SIZE:
        set_cache.popitem(last=False)  # Evict least recently used

    print(f"Cache MISS for {set_id}: {perf_counter() - start_time:.4f}s")
    return Response(json_result, content_type="application/json")


@app.route("/api/set/binary")
def apiSetBinary():
    set_id = request.args.get("id")
    if set_id is None:
        return Response("Missing id parameter", status=400)
    db = Database()
    try:
        binary_data = get_set_binary(db, set_id)
    finally:
        db.close()
    return Response(binary_data, content_type="application/octet-stream")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
