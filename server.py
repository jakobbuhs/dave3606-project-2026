import json
import html
from flask import Flask, Response, request
from time import perf_counter
import gzip

from database import Database

app = Flask(__name__)




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
    
    
    return Response(compressed_page, content_type="text/html; charset=" + encoding_type, headers={"Content-Encoding": "gzip"})


@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    #Automatically close the file when done
    with open("templates/set.html") as f:
        template = f.read()

    return Response(template)


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    result = {"set_id": set_id}
    json_result = json.dumps(result, indent=4)
    return Response(json_result, content_type="application/json")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
