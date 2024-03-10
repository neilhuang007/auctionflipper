import base64
import nbtlib
import logging
import subprocess
import json
from io import BytesIO

def decode_data(string):
    try:
        # Decode the base64 string
        data = base64.b64decode(string)
        # Parse the NBT data
        nbt_file = nbtlib.File.load(BytesIO(data), gzipped=True)
        # Convert the NBT file to a dictionary
        json_data = dict(nbt_file)
        return json_data
    except Exception as error:
        logging.error(f"Error decoding data: {error}")
        if "PartialReadError" in str(error):
            logging.error("The NBT data may be corrupted or incorrectly formatted.")
        return None
def get_item_networth(item):
    # Convert the Python dictionary to a JSON string
    item_json = json.dumps(item)

    # Call the Node.js script with the NBT data as a command line argument
    subprocess.run(['node', 'Evaluator.js', item_json])

    # Read the networth from the output file
    with open('output.json', 'r') as file:
        networth = json.load(file)

    return networth

item_bytes = 'H4sIAAAAAAAAAI1U3W4aRxQ+GJIAsVRVbZRWSqKJmrSmtglrMHh9EQkv2EEhdsQ6rnKFBvawO2J2h+zMOslL5A160174PfwofZCqZxawHFWqysUy853v/Mw530wVoAIFUQWAwgZsiKBwvwB3PJUlplCFouFhBUqYTCOwvwLcf5dMUuRzPpFYKELllQjwWPJQk/XvKtwLhF5I/pmchirFMqE/wpPrq84J8pT5U8IO2fVV0HT26e9gq9l0a/CI7D0e8zC3TbedRiM3bjtOowbPyOqbFJPQREv7vjW7W9ut2pK2v1+DLWJ5qTDMi3gyXQVqPV8Rn6+YtIBf18zbKf/NrFvuC+IeqSTTrGsMn86Zv0AM/iP4DjkMEoNSihBXdfBtp9P+umLHbdbbNWrOS4L7nxaYCstmg8GAgB0idY5Fqg2jg4s54Rcr2D0RPDHstZASU3YBewQNxQyJiFze8neHShmRhF9BGZ3gAlq09Kf8kjpqY6ytfsTTRYJa30CdCx4vRCp0TF4APxFCB3+vMhYolijDIgrCOItEGDFMVBZG8DMx+iQXqtJml3iJkhnFMo1MqxiZmjETITwmHi55MSZGM5UQLjQTBuOnlI0G2u5OhBTm8yHrkeQCqdKAUVl4fSVHg5NX58wbDrzXULMCiei4VIqeZ5LyRdywgBqibfudnUazUXeJBVX6BPnY6/AdTeINTzjzlDZ2Ts1Wg/LW81O2/vr9TzvlEX7IRIo2ztTjJAEVTzTz59R/1iSsDp3/zXdci36MhEQmEvieNucRshtaHu4H6r09X3fUZ713pyf9s1Pm/3Y26pWhdMpjhIdEOOYivdUT/yN9oQrf9D+ZlJNSUzHJDOoyfBtkNGSVjLWtYJziB9j0uudd7+zNkX/ouEV4OOEafcPNkaI2vMWUpkKXHqkTT8tQjlUgZgJTKM0oZ9k+EPDAG71/ez7ujfrd3pAqG+f1VWHz9jyLUJIkNwpzpwibMyvmsc7FTFCpCPfkUp+0K9IzotfiWzpU9Fqfy30Vb+7IyuFyLc0VQdIloAQ08yVhM7QXZTzPL4rlADUwy6j8Z52D9ox3nL1dN2g1d1u81abVHt91ndbMdfnB5GCvQRmsEMdG5N53S1AxIkZtKC09g19+iV/+AbABd5ePiH0b/wF4s7i3SgUAAA\u003d\u003d'
decoded_item = decode_data(item_bytes)
get_item_networth(decoded_item)
print(get_item_networth(decoded_item))