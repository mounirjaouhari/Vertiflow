import subprocess
import re
from flask import Flask, request

app = Flask(__name__)

def force_strict_json(raw_str):
    """
    Uses regex to wrap unquoted keys in double quotes.
    Example: { timestamp: ISODate(...) } -> { "timestamp": "ISODate(...)" }
    """
    # 1. Quote the keys: finds word characters followed by a colon
    # Changes { key: value } to { "key": value }
    quoted_keys = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*):', r'\1"\2"\3:', raw_str)
    
    # 2. Handle ISODate and ObjectIDs (common Mongo output that isn't valid JSON)
    # This wraps ISODate('...') in quotes so it becomes a valid JSON string
    quoted_vals = re.sub(r'(ISODate|ObjectId)\((.*?)\)', r'"\1(\2)"', quoted_keys)
    
    return quoted_vals

@app.route('/', methods=['POST'])
@app.route('/<dbname>', methods=['POST'])
def run_query(dbname=""):
    # Use -u in Docker to make sure this prints immediately!
    query = request.data.decode('utf-8').strip()
    print(f"--- EXECUTING ---", flush=True)
    print(f"Query: {query}", flush=True)
    
    try:
        # We call the actual Mongo Shell installed in the container
        process = subprocess.run(
            ['mongosh', f"mongodb://mongodb:27017/{dbname}", '--quiet', '--eval', query],
            capture_output=True, 
            text=True
        )
        output = process.stdout.strip()
        
        # Apply the brute-force quoting
        cleaned_output = force_strict_json(output)
        
        if process.returncode == 0:
            return cleaned_output, 200, {'Content-Type': 'application/json'}
        else:
            return f"Mongo Shell Error: {process.stderr}\n", 400
            
    except Exception as e:
        return f"System Error: {str(e)}\n", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
