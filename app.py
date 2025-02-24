from flask import Flask, request, send_file, Response
import instaloader
import re
import os
import glob

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_reel(url):
    """Download Instagram Reel and ensure it's in MP4 format."""
    match = re.search(r"instagram\.com/reel/([^/?]+)", url)
    if not match:
        return None, "Invalid URL. Please enter a valid Instagram Reel URL."

    shortcode = match.group(1)
    loader = instaloader.Instaloader(dirname_pattern=DOWNLOAD_FOLDER, filename_pattern=shortcode, post_metadata_txt_pattern="")

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        
        # Download the reel
        loader.download_post(post, target=DOWNLOAD_FOLDER)

        # Find the downloaded .mp4 file dynamically
        reel_files = glob.glob(f"{DOWNLOAD_FOLDER}/*.mp4")

        if not reel_files:
            return None, "Reel video not found after download."

        return reel_files[0], None  # Return first matched MP4 file

    except Exception as e:
        return None, str(e)  # Return error message

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            return Response("Error: No URL provided!", mimetype="text/plain"), 400

        filepath, error = download_reel(url)

        if error:
            return generate_html(error)

        # Serve the file for direct download in browser
        response = send_file(filepath, as_attachment=True, mimetype="video/mp4")

        # Clean up downloaded files to save space
        try:
            os.remove(filepath)
        except Exception as cleanup_error:
            print(f"Error removing file: {cleanup_error}")

        return response

    return generate_html()

def generate_html(error=None):
    """Generate HTML page without using a templates folder."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Instagram Reel Downloader</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="text-center">Instagram Reel Downloader</h2>
            <form method="POST" class="mt-4 text-center">
                <input type="text" name="url" class="form-control" placeholder="Enter Instagram Reel URL" required>
                <button type="submit" class="btn btn-primary mt-3">Download</button>
            </form>
            {"<div class='alert alert-danger mt-3'>" + error + "</div>" if error else ""}
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)
