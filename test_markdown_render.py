"""Test Markdown rendering in chat display"""
import re

test_text = '''## Cable Current Ratings

Based on the IS10101 standard, here are the current ratings:

| Cable Size | Current Rating | Voltage Drop |
|------------|----------------|--------------|
| 1.5mm²     | 15A            | 2.5%         |
| 2.5mm²     | 20A            | 2.0%         |
| 4.0mm²     | 27A            | 1.8%         |

### Key Points:
- **Installation method** affects ratings
- *Temperature* derating applies above 30°C
- Use `Table 4D1A` for reference

**Important:** Always verify with latest standards.
'''

def parse_inline(text):
    result = []
    pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)'
    last_end = 0
    for match in re.finditer(pattern, text):
        if match.start() > last_end:
            result.append((text[last_end:match.start()], None))
        full_match = match.group(0)
        if full_match.startswith('**'):
            result.append((match.group(2), 'bold'))
        elif full_match.startswith('`'):
            result.append((match.group(4), 'code'))
        elif full_match.startswith('*'):
            result.append((match.group(3), 'italic'))
        last_end = match.end()
    if last_end < len(text):
        result.append((text[last_end:], None))
    return result if result else [(text, None)]

print("=" * 60)
print("MARKDOWN RENDERING TEST")
print("=" * 60)
print()

# Parse test
lines = test_text.split('\n')
for line in lines:
    if line.startswith('## '):
        print(f'🔵 [H2 - Blue Bold] {line[3:]}')
    elif line.startswith('### '):
        print(f'🟢 [H3 - Teal Bold] {line[4:]}')
    elif '|' in line and line.strip().startswith('|'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if all(set(c).issubset({'-', ':'}) for c in cells if c):
            print('   [TABLE-SEPARATOR - skipped]')
        else:
            # Check if header (first row before separator)
            formatted_row = "  │ " + " │ ".join(f"{c:^15}" for c in cells) + " │"
            print(f'📊 [TABLE] {formatted_row}')
    elif line.startswith('- '):
        content = line[2:]
        parts = parse_inline(content)
        formatted = ''
        for text, tag in parts:
            if tag == 'bold':
                formatted += f'🟡[BOLD]{text}[/BOLD]'
            elif tag == 'italic':
                formatted += f'[ITALIC]{text}[/ITALIC]'
            elif tag == 'code':
                formatted += f'🔴[CODE]{text}[/CODE]'
            else:
                formatted += text
        print(f'🟣 [BULLET] • {formatted}')
    elif line.strip():
        parts = parse_inline(line)
        formatted = ''
        for text, tag in parts:
            if tag == 'bold':
                formatted += f'🟡[BOLD]{text}[/BOLD]'
            elif tag == 'italic':
                formatted += f'[ITALIC]{text}[/ITALIC]'
            elif tag == 'code':
                formatted += f'🔴[CODE]{text}[/CODE]'
            else:
                formatted += text
        print(f'   [TEXT] {formatted}')
    else:
        print()

print()
print("=" * 60)
print("✅ Markdown parsing test complete!")
print()
print("Legend:")
print("  🔵 H2 Headers - Rendered in blue, large bold font")
print("  🟢 H3 Headers - Rendered in teal, medium bold font")
print("  📊 Tables - Rendered with borders and aligned columns")
print("  🟣 Bullets - Rendered with purple bullet points")
print("  🟡 Bold text - Rendered in yellow/gold")
print("  🔴 Code - Rendered in red with monospace font")
print("=" * 60)
