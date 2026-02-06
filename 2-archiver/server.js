const express = require('express');
const fs = require('fs');
const app = express();
app.use(express.json({limit: '50mb'}));

const OUTPUT_FILE = 'all_approved_results.json';
const FAILED_OUTPUT_FILE = 'all_failed_results.json';

// Max entries per file: passed (approved) vs failed
const MAX_APPROVED = 100;
const MAX_FAILED = 10;

// Initialize files with empty array if they don't exist
[OUTPUT_FILE, FAILED_OUTPUT_FILE].forEach(file => {
    if (!fs.existsSync(file)) fs.writeFileSync(file, '[]');
});



// New function to handle the safety backup
function backupFiles() {
    const archiveDir = './archive';
    if (!fs.existsSync(archiveDir)) {
        fs.mkdirSync(archiveDir);
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    [OUTPUT_FILE, FAILED_OUTPUT_FILE].forEach(file => {
        if (fs.existsSync(file)) {
            const stats = fs.statSync(file);
            // Only backup if the file isn't empty (more than 2 bytes for '[]')
            if (stats.size > 2) {
                const backupName = `${archiveDir}/${timestamp}_${file}`;
                fs.copyFileSync(file, backupName);
                console.log(`💾 Safety backup created: ${backupName}`);
            }
        }
    });
}

function shutdown() {
    console.log('\nStopping server...');
    backupFiles(); // Save the data before we wipe it
    console.log('Clearing active result files for next session...');
    [OUTPUT_FILE, FAILED_OUTPUT_FILE].forEach(file => {
        fs.writeFileSync(file, '[]');
    });
    process.exit(0);
}


process.on('SIGINT', shutdown);   // Ctrl+C
process.on('SIGTERM', shutdown);  // e.g. kill

function readResultsFile(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8').trim();
        return content ? JSON.parse(content) : [];
    } catch {
        return [];
    }
}

function appendResult(filePath, iteration, data, logEmoji, maxLimit) {
    const json = readResultsFile(filePath);
    if (json.length >= maxLimit) {
        console.log(`${logEmoji} Limit reached (${json.length}/${maxLimit}), skipped Iteration ${iteration}`);
        return false;
    }
    json.push({ iteration, timestamp: new Date().toISOString(), response: data });
    fs.writeFileSync(filePath, JSON.stringify(json, null, 2));
    console.log(`${logEmoji} Appended Iteration ${iteration} to ${filePath} (${json.length}/${maxLimit})`);
    return true;
}

app.post('/save', (req, res) => {
    const { iteration, data } = req.body;
    const saved = appendResult(OUTPUT_FILE, iteration, data, '✅', MAX_APPROVED);
    res.send(saved ? 'Saved to master file' : `Limit reached (${MAX_APPROVED}), not saved`);
});

app.post('/save-failed', (req, res) => {
    const { iteration, data } = req.body;
    const saved = appendResult(FAILED_OUTPUT_FILE, iteration, data, '❌', MAX_FAILED);
    res.send(saved ? 'Saved to failed file' : `Limit reached (${MAX_FAILED}), not saved`);
});

app.listen(3000, () => console.log('🚀 Master Collector running on http://localhost:3000'));