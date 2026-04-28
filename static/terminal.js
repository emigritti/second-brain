document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('query-input');
    const output = document.getElementById('output');
    
    if (!input) return;
    
    input.focus();
    
    input.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter' && input.value.trim() !== '') {
            const query = input.value.trim();
            input.value = '';
            
            // Append user query
            output.innerHTML += `\n<div style="color: #ffffff;">> ${query}</div>\n`;
            
            // Add loading indicator
            const loadingId = 'loading-' + Date.now();
            output.innerHTML += `<div id="${loadingId}">PROCESSING...</div>\n`;
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                
                // Remove loading
                document.getElementById(loadingId).remove();
                
                // Typewriter effect for answer
                await typeText(data.answer, output);
                
                // Show sources if any
                if (data.sources && data.sources.length > 0) {
                    output.innerHTML += `\n<br><div>[SOURCES]: `;
                    data.sources.forEach(slug => {
                        output.innerHTML += `<a href="/doc/${slug}" class="source-link" target="_blank">${slug}</a> `;
                    });
                    output.innerHTML += `</div>\n`;
                }
                
                output.scrollTop = output.scrollHeight;
                
            } catch (err) {
                document.getElementById(loadingId).remove();
                output.innerHTML += `<div style="color: red;">[SYSTEM ERROR]: ${err.message}</div>\n`;
            }
        }
    });
    
    // Auto-scroll on focus
    document.addEventListener('click', () => {
        input.focus();
    });
});

async function typeText(text, element) {
    const container = document.createElement('div');
    element.appendChild(container);
    
    // Simple fast typewriter
    const chunk = 5; // characters at a time for speed
    for (let i = 0; i < text.length; i += chunk) {
        container.textContent += text.substring(i, i + chunk);
        element.scrollTop = element.scrollHeight;
        await new Promise(r => setTimeout(r, 10));
    }
}
