// 下载 face-api.js 模型文件的脚本
const https = require('https');
const fs = require('fs');
const path = require('path');

const modelsDir = './public/models';
const baseUrl = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights';

const modelFiles = [
    'ssd_mobilenetv1_model-weights_manifest.json',
    'ssd_mobilenetv1_model-shard1',
    'face_landmark_68_model-weights_manifest.json',
    'face_landmark_68_model-shard1',
    'face_recognition_model-weights_manifest.json',
    'face_recognition_model-shard1',
    'face_recognition_model-shard2'
];

function downloadFile(url, dest) {
    return new Promise((resolve, reject) => {
        console.log(`Downloading ${url} to ${dest}`);

        const file = fs.createWriteStream(dest);

        https.get(url, (response) => {
            if (response.statusCode !== 200) {
                reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
                return;
            }

            response.pipe(file);

            file.on('finish', () => {
                file.close();
                console.log(`Downloaded ${dest}`);
                resolve();
            });

            file.on('error', (err) => {
                fs.unlink(dest, () => { }); // 删除部分下载的文件
                reject(err);
            });
        }).on('error', (err) => {
            reject(err);
        });
    });
}

async function downloadModels() {
    if (!fs.existsSync(modelsDir)) {
        fs.mkdirSync(modelsDir, { recursive: true });
    }

    for (const file of modelFiles) {
        const url = `${baseUrl}/${file}`;
        const dest = path.join(modelsDir, file);

        try {
            await downloadFile(url, dest);
        } catch (error) {
            console.error(`Error downloading ${file}:`, error.message);
        }
    }

    console.log('All models downloaded!');
}

downloadModels().catch(console.error);
