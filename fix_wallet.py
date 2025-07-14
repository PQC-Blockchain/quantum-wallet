import re

# Read the production wallet file
with open('quantum_web_wallet_production.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add autocomplete="off" to all input fields
content = re.sub(r'<input([^>]*?)>', lambda m: '<input' + m.group(1) + ' autocomplete="off" data-lpignore="true" data-form-type="other">' if 'autocomplete' not in m.group(1) else m.group(0), content)

# 2. Replace "2FA" with "Google Authenticator" in all text
replacements = {
    '2FA Code': 'Google Authenticator Code',
    '2FA code': 'Google Authenticator code',
    'Enter 2FA': 'Enter Google Authenticator',
    'Setup 2FA': 'Setup Google Authenticator',
    'Enable 2FA': 'Enable Google Authenticator',
    'Two-Factor Authentication': 'Google Authenticator',
    '2FA': 'Google Authenticator'
}

for old, new in replacements.items():
    content = content.replace(old, new)

# 3. Replace 6-digit input fields with individual blocks
# Find and replace the 2FA input pattern
six_digit_pattern = r'<input[^>]*?id="([^"]*?2FA[^"]*?)"[^>]*?placeholder="000000"[^>]*?>'

def replace_with_blocks(match):
    input_id = match.group(1)
    container_id = input_id.replace('2FA', 'CodeContainer')
    
    return f'''<div class="code-input-container" id="{container_id}">
                    <input type="text" class="code-input" maxlength="1" data-index="0" autocomplete="off" data-lpignore="true">
                    <input type="text" class="code-input" maxlength="1" data-index="1" autocomplete="off" data-lpignore="true">
                    <input type="text" class="code-input" maxlength="1" data-index="2" autocomplete="off" data-lpignore="true">
                    <input type="text" class="code-input" maxlength="1" data-index="3" autocomplete="off" data-lpignore="true">
                    <input type="text" class="code-input" maxlength="1" data-index="4" autocomplete="off" data-lpignore="true">
                    <input type="text" class="code-input" maxlength="1" data-index="5" autocomplete="off" data-lpignore="true">
                </div>
                <input type="hidden" id="{input_id}" />'''

content = re.sub(six_digit_pattern, replace_with_blocks, content)

# Add the CSS for code input blocks if not present
if '.code-input-container' not in content:
    css_addition = '''
        /* 6-digit code input style */
        .code-input-container {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 20px;
        }
        
        .code-input {
            width: 45px;
            height: 55px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            color: #00ff88;
            transition: all 0.3s;
            /* Disable autocomplete */
            autocomplete: off;
            -webkit-autocomplete: off;
        }
        
        .code-input:focus {
            outline: none;
            border-color: #00ff88;
            background: rgba(0, 255, 136, 0.1);
            box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.2);
        }
        
        .code-input:disabled {
            background: rgba(255, 255, 255, 0.02);
            border-color: rgba(255, 255, 255, 0.1);
            color: #666;
        }
    '''
    content = content.replace('</style>', css_addition + '\n    </style>')

# Add the JavaScript for handling code inputs if not present
if 'initializeCodeInputs' not in content:
    js_addition = '''
        // Initialize 6-digit code inputs
        function initializeCodeInputs() {
            const containers = document.querySelectorAll('.code-input-container');
            
            containers.forEach(container => {
                const inputs = container.querySelectorAll('.code-input');
                const hiddenInput = document.getElementById(container.id.replace('CodeContainer', '2FA'));
                
                inputs.forEach((input, index) => {
                    input.addEventListener('input', (e) => {
                        const value = e.target.value;
                        
                        if (value.length === 1) {
                            // Move to next input
                            if (index < inputs.length - 1) {
                                inputs[index + 1].focus();
                            }
                            
                            // Update hidden input
                            const code = Array.from(inputs).map(i => i.value).join('');
                            if (hiddenInput) hiddenInput.value = code;
                        }
                    });
                    
                    input.addEventListener('keydown', (e) => {
                        if (e.key === 'Backspace' && !e.target.value && index > 0) {
                            inputs[index - 1].focus();
                        }
                    });
                    
                    // Handle paste
                    input.addEventListener('paste', (e) => {
                        e.preventDefault();
                        const pastedData = e.clipboardData.getData('text').replace(/\\D/g, '').slice(0, 6);
                        
                        for (let i = 0; i < pastedData.length && i < inputs.length; i++) {
                            inputs[i].value = pastedData[i];
                        }
                        
                        // Update hidden input
                        if (hiddenInput) hiddenInput.value = pastedData;
                    });
                });
            });
        }
        
        // Call on page load
        document.addEventListener('DOMContentLoaded', () => {
            initializeCodeInputs();
        });
    '''
    
    # Find a good place to insert the JS (before closing script tag)
    content = re.sub(r'(</script>\s*</body>)', js_addition + '\n    \\1', content)

# Save the fixed file
with open('quantum_web_wallet_fixed.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed wallet saved as quantum_web_wallet_fixed.html")
print("Changes made:")
print("1. Added autocomplete='off' to all input fields")
print("2. Replaced all '2FA' text with 'Google Authenticator'")
print("3. Replaced 6-digit inputs with individual code blocks")