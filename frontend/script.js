// Upload PDF
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a PDF file');
        return;
    }
    
    formData.append('file', file);
    
    try {
        document.getElementById('uploadStatus').innerHTML = '<div class="loading">Uploading and processing PDF...</div>';
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('uploadStatus').innerHTML = `<div class="success">${result.message}</div>`;
            document.getElementById('chatSection').style.display = 'block';
        } else {
            document.getElementById('uploadStatus').innerHTML = `<div class="error">Error: ${result.detail}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('uploadStatus').innerHTML = `<div class="error">Upload failed: ${error.message}</div>`;
    }
});

// Ask question
document.getElementById('askForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const question = document.getElementById('question').value.trim();
    if (!question) {
        alert('Please enter a question');
        return;
    }
    
    try {
        document.getElementById('answer').innerHTML = '<div class="loading">Getting answer...</div>';
        
        const formData = new FormData();
        formData.append('question', question);
        
        const response = await fetch('/api/ask', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('answer').innerHTML = `<div class="answer">${result.answer}</div>`;
        } else {
            document.getElementById('answer').innerHTML = `<div class="error">Error: ${result.detail}</div>`;
        }
    } catch (error) {
        console.error('Ask error:', error);
        document.getElementById('answer').innerHTML = `<div class="error">Failed to get answer: ${error.message}</div>`;
    }
});