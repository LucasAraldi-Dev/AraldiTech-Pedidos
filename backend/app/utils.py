import base64

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as file:
        encoded_content = base64.b64encode(file.read()).decode('utf-8')
    return encoded_content