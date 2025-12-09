"""
Test embedded webview functionality
"""

import webview
from pathlib import Path

def test_webview():
    """Test if webview works"""
    
    # Create a simple HTML test
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Webview</title>
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
            p { font-size: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Webview Çalışıyor!</h1>
            <p>HTML içeriği uygulama içinde görüntüleniyor 🎉</p>
            <p>Bu pencereyi kapatıp Interactive Graph'ı deneyebilirsiniz.</p>
        </div>
    </body>
    </html>
    """
    
    # Save test HTML
    test_file = Path("test_webview.html")
    test_file.write_text(html_content, encoding='utf-8')
    
    print("🌐 Opening test webview...")
    print("✅ If you see a colorful page, webview is working!")
    
    # Create webview window
    webview.create_window(
        title='Webview Test',
        url=str(test_file.absolute()),
        width=800,
        height=600,
        resizable=True
    )
    
    webview.start(debug=False)
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_webview()
