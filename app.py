from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import re

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        url = request.form.get('url')
        
        if not url:
            return render_template('index.html', error_bn="দয়া করে একটি লিংক দিন!", error_en="Please provide a valid link!")
        
        ydl_opts = {
            'no_color': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'socket_timeout': 15,
        }
        
        try:
            if action == 'preview':
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Title')
                    thumbnail = info.get('thumbnail', '')
                    uploader = info.get('uploader', info.get('channel', 'Unknown Creator'))
                    view_count = info.get('view_count', 0)
                    
                    channel_thumb = info.get('channel_thumbnail', '')
                    if not channel_thumb:
                        thumbnails = info.get('thumbnails', [])
                        if thumbnails:
                            channel_thumb = thumbnails[-1].get('url', thumbnail)
                        else:
                            channel_thumb = thumbnail
                    
                    if view_count > 1000000:
                        views_formatted = f"{view_count / 1000000:.1f}M"
                    elif view_count > 1000:
                        views_formatted = f"{view_count / 1000:.1f}K"
                    else:
                        views_formatted = str(view_count)

                return render_template('index.html', preview=True, title=title, thumbnail=thumbnail, 
                                     uploader=uploader, views=views_formatted, channel_thumb=channel_thumb, url=url)
            
            elif action == 'download':
                download_opts = {
                    'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                    'format': 'best',
                    'no_color': True,
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                }
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    file_basename = os.path.basename(filename)
                return render_template('index.html', success_bn="ডাউনলোড সফল হয়েছে!", success_en="Download successful!", filename=file_basename)
                
        except Exception as e:
            clean_error = re.sub(r'\x1b\[[0-9;]*m', '', str(e))
            if "Video unavailable" in clean_error or "not available" in clean_error:
                err_bn = "ভিডিওটি পাওয়া যায়নি বা এটি প্রাইভেট।"
                err_en = "Video unavailable or private."
            elif "Sign in" in clean_error or "bot" in clean_error:
                err_bn = "ইউটিউব বট হিসেবে শনাক্ত করেছে। কিছুক্ষণ পর চেষ্টা করুন।"
                err_en = "YouTube detected bot activity. Try again later."
            else:
                err_bn = "ডাউনলোড ব্যর্থ হয়েছে! লিংক চেক করুন।"
                err_en = "Download failed! Check your link."
            return render_template('index.html', error_bn=err_bn, error_en=err_en)
            
    return render_template('index.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)