const express = require('express');
const fs = require('fs');
const path = require('path');
const multer = require('multer');
const ffmpeg = require('fluent-ffmpeg'); // To convert WebM to WAV
const app = express();
const PORT = 3000;

// Setup Multer for file uploads
const upload = multer({ dest: 'uploads/' });

// Serve the audio folder
app.use('/audio', express.static(path.join(__dirname, 'audio')));

// Endpoint to handle audio upload
app.post('/upload-audio', upload.single('audio'), (req, res) => {
    const uploadedFilePath = req.file.path;
    const outputFilePath = path.join(__dirname, 'audio', `${Date.now()}.wav`);

    // Convert the uploaded WebM file to WAV using FFmpeg
    ffmpeg(uploadedFilePath)
        .output(outputFilePath)
        .on('end', () => {
            console.log('Conversion complete');
            fs.unlinkSync(uploadedFilePath); // Delete the temporary WebM file after conversion
            res.json({ message: 'File uploaded successfully', file: outputFilePath });
        })
        .on('error', (err) => {
            console.error('Error during conversion:', err);
            res.status(500).json({ message: 'Conversion failed' });
        })
        .run();
});

// Endpoint to get a random audio file
app.get('/random-audio', (req, res) => {
    const audioFolder = path.join(__dirname, 'audio');
    fs.readdir(audioFolder, (err, files) => {
        if (err) {
            console.error('Error reading audio folder:', err);
            res.status(500).send('Error reading audio folder');
            return;
        }

        const audioFiles = files.filter(file => /\.(mp3|wav|ogg|webm)$/i.test(file));

        if (audioFiles.length === 0) {
            res.status(404).send('No audio files found');
            return;
        }

        const randomFile = audioFiles[Math.floor(Math.random() * audioFiles.length)];
        res.send(`/audio/${randomFile}`);
    });
});

// Serve the HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server running at https://cd2d-109-58-151-252.ngrok-free.app`);
});
//WERKING-RECORDS AND THEN PLAYS BACK RECORDINGS RANDOMLY ALSO HAS NGROK LINK WHICH YOU CAN CHANGE ABOVE