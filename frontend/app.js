function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    
    // Update nav styling
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('text-primary', 'border-primary');
        btn.classList.add('text-textmain', 'border-transparent');
    });
    const activeBtn = document.getElementById(`nav-${tabId}`);
    if (activeBtn) {
        activeBtn.classList.remove('text-textmain', 'border-transparent');
        activeBtn.classList.add('text-primary', 'border-primary');
    }
}

// File dropzone logic
const dropzone = document.getElementById('resumeDropzone');
const fileInput = document.getElementById('resumeFile');
const fileNameDisplay = document.getElementById('fileNameDisplay');
let selectedFile = null;

if(fileInput) {
    fileInput.addEventListener('change', (e) => {
        if(e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileNameDisplay.textContent = selectedFile.name;
            fileNameDisplay.classList.add('text-primary');
        }
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-primary', 'bg-[#16161a]');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-primary', 'bg-[#16161a]');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-primary', 'bg-[#16161a]');
        if(e.dataTransfer.files.length > 0) {
            selectedFile = e.dataTransfer.files[0];
            fileInput.files = e.dataTransfer.files;
            fileNameDisplay.textContent = selectedFile.name;
            fileNameDisplay.classList.add('text-primary');
        }
    });
}

// ATS Analyzer API Call
const analyzeBtn = document.getElementById('analyzeBtn');
if(analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
        const jobDesc = document.getElementById('jobDesc').value;
        
        if (!selectedFile || !jobDesc.trim()) {
            alert('Please upload a resume and paste a job description.');
            return;
        }

        const formData = new FormData();
        formData.append('resume', selectedFile);
        formData.append('job_desc', jobDesc);

        // UI Loading State
        const btnText = document.getElementById('analyzeBtnText');
        const spinner = document.getElementById('analyzeSpinner');
        btnText.textContent = "Analyzing...";
        spinner.classList.remove('hidden');
        analyzeBtn.disabled = true;
        document.getElementById('atsResults').classList.add('hidden');

        try {
            const response = await fetch('/api/analyze-ats', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (response.ok) {
                renderATSResults(data);
            } else {
                alert('Error: ' + (data.error || 'Unknown error occurred'));
            }
        } catch (error) {
            alert('Connection failed: ' + error.message);
        } finally {
            btnText.textContent = "Analyze Resume";
            spinner.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    });
}

function renderATSResults(data) {
    document.getElementById('atsResults').classList.remove('hidden');
    
    // Overall Score
    document.getElementById('overallScoreText').textContent = `${data.overall_score}%`;
    document.getElementById('overallScoreSvg').setAttribute('stroke-dasharray', `${data.overall_score}, 100`);
    
    let scoreColor = '#4ade80'; // green
    if(data.overall_score < 40) scoreColor = '#f87171'; // red
    else if(data.overall_score < 75) scoreColor = '#fbbf24'; // yellow
    
    document.getElementById('overallScoreText').style.color = scoreColor;
    document.getElementById('overallScoreSvg').setAttribute('stroke', scoreColor);

    // Sub Scores
    const subContainer = document.getElementById('subScoresContainer');
    subContainer.innerHTML = '';
    for (const [key, val] of Object.entries(data.sub_scores)) {
        subContainer.innerHTML += `
            <div>
                <div class="flex justify-between mb-1 text-sm font-medium">
                    <span>${key}</span>
                    <span>${val}%</span>
                </div>
                <progress class="w-full h-2" value="${val}" max="100"></progress>
            </div>
        `;
    }

    // Keyword Badges
    const badgeContainer = document.getElementById('keywordBadges');
    badgeContainer.innerHTML = '';
    data.matched_exact.forEach(kw => {
        badgeContainer.innerHTML += `<span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-900/30 text-green-400 border border-green-500/50">✓ ${kw} (Exact)</span>`;
    });
    data.matched_semantic.forEach(kw => {
        badgeContainer.innerHTML += `<span class="px-3 py-1 rounded-full text-xs font-semibold bg-blue-900/30 text-blue-400 border border-blue-500/50">~ ${kw} (Semantic)</span>`;
    });
    data.missing_keywords.slice(0, 10).forEach(kw => {
        badgeContainer.innerHTML += `<span class="px-3 py-1 rounded-full text-xs font-semibold bg-red-900/30 text-red-400 border border-red-500/50">✗ ${kw} (Missing)</span>`;
    });

    // Missing Kws Alert & Optimizer Display
    if(data.missing_keywords.length > 0) {
        document.getElementById('missingKwsAlert').classList.remove('hidden');
        document.getElementById('missingKwsText').textContent = data.missing_keywords.slice(0,10).join(', ');
        document.getElementById('optimizerSection').classList.remove('hidden');
    } else {
        document.getElementById('missingKwsAlert').classList.add('hidden');
        document.getElementById('optimizerSection').classList.add('hidden');
    }

    // Recommendations
    const recList = document.getElementById('recommendationsList');
    recList.innerHTML = '';
    if(data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach(rec => {
            recList.innerHTML += `<li>💡 ${rec}</li>`;
        });
    } else {
        recList.innerHTML = `<li class="text-green-400">✓ Your resume looks structurally perfect and highly tailored!</li>`;
    }

    // Warnings
    const warnAlert = document.getElementById('warningsAlert');
    const warnList = document.getElementById('warningsList');
    if(data.warnings && data.warnings.length > 0) {
        warnAlert.classList.remove('hidden');
        warnList.innerHTML = '';
        data.warnings.forEach(w => {
            warnList.innerHTML += `<li>${w}</li>`;
        });
    } else {
        warnAlert.classList.add('hidden');
    }
}

// Theme Toggle Logic
function toggleTheme() {
    const htmlElement = document.documentElement;
    const isDark = htmlElement.classList.contains('dark');
    
    if (isDark) {
        htmlElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        document.getElementById('moonIcon').classList.remove('hidden');
        document.getElementById('sunIcon').classList.add('hidden');
    } else {
        htmlElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        document.getElementById('sunIcon').classList.remove('hidden');
        document.getElementById('moonIcon').classList.add('hidden');
    }
}

// Load saved theme on startup
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('theme') === 'light') {
        document.documentElement.classList.remove('dark');
        document.getElementById('moonIcon').classList.remove('hidden');
        document.getElementById('sunIcon').classList.add('hidden');
    } else {
        // Default is dark
        document.documentElement.classList.add('dark');
        document.getElementById('sunIcon').classList.remove('hidden');
        document.getElementById('moonIcon').classList.add('hidden');
    }
});

// Citation Generator API Call
const citeBtn = document.getElementById('citeBtn');
if(citeBtn) {
    citeBtn.addEventListener('click', async () => {
        const text = document.getElementById('citeInputText').value;
        const model = document.getElementById('citeModel').value;
        
        if (!text.trim()) {
            alert('Please paste some references to format.');
            return;
        }

        const btnText = document.getElementById('citeBtnText');
        const spinner = document.getElementById('citeSpinner');
        btnText.textContent = "Generating...";
        spinner.classList.remove('hidden');
        citeBtn.disabled = true;
        document.getElementById('citeResults').classList.add('hidden');

        try {
            const response = await fetch('/api/cite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text, model: model })
            });

            if (!response.ok) {
                const data = await response.json();
                alert('Error: ' + (data.error || 'Unknown error occurred'));
                throw new Error(data.error);
            }
            
            document.getElementById('citeResults').classList.remove('hidden');
            const textBox = document.getElementById('citeOutputText');
            textBox.value = "";
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                textBox.value += chunk;
                textBox.scrollTop = textBox.scrollHeight;
            }
        } catch (error) {
            alert('An error occurred: ' + error.message);
            console.error(error);
        } finally {
            btnText.textContent = "Generate Citations";
            spinner.classList.add('hidden');
            citeBtn.disabled = false;
        }
    });
}

// AI Detection API Call
const detectAiBtn = document.getElementById('detectAiBtn');
if(detectAiBtn) {
    detectAiBtn.addEventListener('click', async () => {
        const text = document.getElementById('aiInputText').value;
        if (!text || text.split(' ').length < 10) {
            alert('Please paste at least 10 words for analysis.');
            return;
        }

        const btnText = document.getElementById('detectAiBtnText');
        const spinner = document.getElementById('detectAiSpinner');
        btnText.textContent = "Analyzing...";
        spinner.classList.remove('hidden');
        detectAiBtn.disabled = true;
        document.getElementById('aiResults').classList.add('hidden');

        try {
            const response = await fetch('/api/detect-ai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();
            
            if (response.ok) {
                renderAiResults(data);
            } else {
                alert('Error: ' + (data.error || 'Unknown error occurred'));
            }
        } catch (error) {
            alert('Connection failed: ' + error.message);
        } finally {
            btnText.textContent = "Detect AI";
            spinner.classList.add('hidden');
            detectAiBtn.disabled = false;
        }
    });
}

function renderAiResults(data) {
    document.getElementById('aiResults').classList.remove('hidden');
    
    // AI Score
    const aiScore = data.score;
    document.getElementById('aiScoreText').textContent = `${aiScore}%`;
    document.getElementById('aiScoreSvg').setAttribute('stroke-dasharray', `${aiScore}, 100`);
    
    let scoreColor = '#4ade80'; // green (human)
    if(aiScore > 75) scoreColor = '#f87171'; // red (AI)
    else if(aiScore > 40) scoreColor = '#fbbf24'; // yellow
    
    document.getElementById('aiScoreText').style.color = scoreColor;
    document.getElementById('aiScoreSvg').setAttribute('stroke', scoreColor);

    // Report
    document.getElementById('aiReportText').textContent = data.report;
    
    // Suspicious Phrases
    const suspContainer = document.getElementById('aiSuspiciousContainer');
    const suspPhrases = document.getElementById('aiSuspiciousPhrases');
    
    if(data.suspicious_phrases && data.suspicious_phrases.length > 0) {
        suspContainer.classList.remove('hidden');
        suspPhrases.innerHTML = '';
        data.suspicious_phrases.forEach(phrase => {
            suspPhrases.innerHTML += `<span class="px-3 py-1 rounded-full text-xs font-semibold bg-orange-900/30 text-orange-400 border border-orange-500/50">"${phrase}"</span>`;
        });
    } else {
        suspContainer.classList.add('hidden');
    }
}

// Humanizer API Call
const humanizeBtn = document.getElementById('humanizeBtn');
if(humanizeBtn) {
    humanizeBtn.addEventListener('click', async () => {
        const text = document.getElementById('humanizeInputText').value;
        const tone = document.getElementById('humanizeTone').value;
        const model = document.getElementById('humanizeModel').value;
        
        if (!text.trim()) {
            alert('Please paste some text to humanize.');
            return;
        }

        const btnText = document.getElementById('humanizeBtnText');
        const spinner = document.getElementById('humanizeSpinner');
        btnText.textContent = "Humanizing...";
        spinner.classList.remove('hidden');
        humanizeBtn.disabled = true;
        document.getElementById('humanizeResults').classList.add('hidden');

        try {
            const response = await fetch('/api/humanize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text, tone: tone, model: model })
            });

            if (!response.ok) {
                const data = await response.json();
                alert('Error: ' + (data.error || 'Unknown error occurred'));
                throw new Error(data.error);
            }
            
            document.getElementById('humanizeResults').classList.remove('hidden');
            document.getElementById('humanizeBefore').textContent = text;
            document.getElementById('humanizeAfterTitle').textContent = `After (${tone})`;
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let isParsingReport = false;
            
            const afterBox = document.getElementById('humanizeAfter');
            const reportBox = document.getElementById('humanizeReport');
            afterBox.textContent = "";
            reportBox.textContent = "";
            
            let buffer = "";
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                
                if (!isParsingReport) {
                    if (buffer.includes("=== CHANGES REPORT ===")) {
                        isParsingReport = true;
                        const parts = buffer.split("=== CHANGES REPORT ===");
                        afterBox.textContent = parts[0].replace("=== REWRITTEN TEXT ===", "").trimStart();
                        reportBox.textContent = parts[1].trimStart();
                    } else {
                        afterBox.textContent = buffer.replace("=== REWRITTEN TEXT ===", "").trimStart();
                    }
                } else {
                    const parts = buffer.split("=== CHANGES REPORT ===");
                    if (parts.length > 1) {
                        reportBox.textContent = parts[1].trimStart();
                    }
                }
            }
        } catch (error) {
            alert('An error occurred: ' + error.message);
            console.error(error);
        } finally {
            btnText.textContent = "Humanize Now ✨";
            spinner.classList.add('hidden');
            humanizeBtn.disabled = false;
        }
    });
}

// Resume Optimizer API Call
const optimizeBtn = document.getElementById('optimizeBtn');
if(optimizeBtn) {
    optimizeBtn.addEventListener('click', async () => {
        const jobDesc = document.getElementById('jobDesc').value;
        const model = document.getElementById('optimizeModel').value;
        
        if (!selectedFile || !jobDesc.trim()) {
            alert('Resume file and Job Description are required.');
            return;
        }

        const formData = new FormData();
        formData.append('resume', selectedFile);
        formData.append('job_desc', jobDesc);
        formData.append('model', model);

        const btnText = document.getElementById('optimizeBtnText');
        const spinner = document.getElementById('optimizeSpinner');
        btnText.textContent = "Optimizing...";
        spinner.classList.remove('hidden');
        optimizeBtn.disabled = true;
        document.getElementById('optimizedResultSection').classList.add('hidden');

        try {
            const response = await fetch('/api/optimize', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                alert('Error: ' + (data.error || 'Unknown error occurred'));
                throw new Error(data.error);
            }
            
            document.getElementById('optimizedResultSection').classList.remove('hidden');
            const textBox = document.getElementById('optimizedResumeText');
            textBox.value = "";
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                textBox.value += chunk;
                // Auto-scroll
                textBox.scrollTop = textBox.scrollHeight;
            }
            
        } catch (error) {
            alert('An error occurred: ' + error.message);
            console.error(error);
        } finally {
            btnText.textContent = "Auto-Optimize Resume";
            spinner.classList.add('hidden');
            optimizeBtn.disabled = false;
        }
    });
}

// Utility: Download text as file
window.downloadText = function(elementId, filename) {
    const el = document.getElementById(elementId);
    const text = el.tagName === 'TEXTAREA' ? el.value : el.textContent;
    
    if (!text) {
        alert("No text to download!");
        return;
    }
    
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};
