from flask import Flask, jsonify, send_file
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image
import io
from pyngrok import ngrok

app = Flask(__name__)

# Google Drive API setup
SERVICE_ACCOUNT_FILE = 'D:/aidemo/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Google Drive folder containing images
FOLDER_ID = '1bLFeeWrr9qlA33ewbApb5R1_7kRLuVjx'
from pyngrok import ngrok

ngrok.kill()
@app.route('/generate-collage', methods=['GET'])
def generate_collage():
    try:
        # Get images from Google Drive
        results = drive_service.files().list(
            q=f"'{FOLDER_ID}' in parents and mimeType contains 'image'",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        if not files:
            return jsonify({"error": "No images found in the folder"}), 404

        # Download images
        images = []
        for file in files[:9]:  # Limit to 9 images for 3x3 grid
            file_id = file['id']
            request = drive_service.files().get_media(fileId=file_id)
            image_data = io.BytesIO(request.execute())
            img = Image.open(image_data)
            images.append(img)

        # Create 3x3 collage
        cols, rows = 3, 3
        max_width = max(img.width for img in images)
        max_height = max(img.height for img in images)
        collage = Image.new("RGBA", (cols * max_width, rows * max_height), (255, 255, 255, 255))

        for i, img in enumerate(images):
            x_offset = (i % cols) * max_width
            y_offset = (i // cols) * max_height
            collage.paste(img, (x_offset, y_offset))

        # Save collage to in-memory file
        collage_bytes = io.BytesIO()
        collage.save(collage_bytes, format='PNG')
        collage_bytes.seek(0)

        return send_file(collage_bytes, mimetype='image/png', as_attachment=True, download_name='collage.png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = 5001
    public_url = ngrok.connect(port).public_url
    print(f"Public ngrok URL: {public_url}")
    app.run(port=port, debug=True)
