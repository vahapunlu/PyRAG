"""
Test webview in separate process (like GUI will do)
"""

import subprocess
import sys
from pathlib import Path

def test_subprocess_webview():
    """Test webview in separate process"""
    
    # Create test HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Subprocess Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 48px; margin-bottom: 20px; }
            p { font-size: 20px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Subprocess Webview Çalışıyor!</h1>
            <p>Separate process'te HTML görüntüleniyor 🎉</p>
            <p>Bu pencere GUI'yi bloke etmiyor!</p>
            <p style="margin-top: 30px; opacity: 0.8;">Bu pencereyi kapatabilirsiniz</p>
        </div>
    </body>
    </html>
    """
    
    test_file = Path("test_subprocess_webview.html")
    test_file.write_text(html_content, encoding='utf-8')
    
    print("🚀 Launching webview in separate process...")
    print("✅ Main script will continue (non-blocking)")
    
    # Launch webview in separate process
    launcher_code = f"""
import webview
from pathlib import Path

webview.create_window(
    title='Subprocess Webview Test',
    url=r'{test_file.absolute()}',
    width=800,
    height=600,
    resizable=True
)
webview.start(debug=False)
"""
    
    # Start subprocess (non-blocking)
    process = subprocess.Popen(
        [sys.executable, '-c', launcher_code],
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )
    
    print(f"✅ Webview launched in process {process.pid}")
    print("✅ Main script continues running...")
    print("💡 Check if webview window appeared!")
    print("💡 Close the webview window when done")
    
    # Wait for process to finish
    print("\n⏳ Waiting for webview to close...")
    process.wait()
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_subprocess_webview()
