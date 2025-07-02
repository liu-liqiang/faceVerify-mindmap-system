// 重新下载 face-api.js 模型文件的脚本（使用备用源）
const https = require('https');
const fs = require('fs');
const path = require('path');

const modelsDir = './public/models';

// 使用JSDelivr CDN作为备用源
const baseUrl = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@latest/model';

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
            if (response.statusCode === 302 || response.statusCode === 301) {
                // 处理重定向
                return downloadFile(response.headers.location, dest).then(resolve).catch(reject);
            }

            if (response.statusCode !== 200) {
                reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
                return;
            }

            response.pipe(file);

            file.on('finish', () => {
                file.close();
                // 验证文件大小
                const stats = fs.statSync(dest);
                console.log(`Downloaded ${dest} (${stats.size} bytes)`);

                if (stats.size === 0) {
                    fs.unlinkSync(dest);
                    reject(new Error(`Downloaded file ${dest} is empty`));
                    return;
                }

                resolve();
            });

            file.on('error', (err) => {
                fs.unlink(dest, () => { });
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

    console.log('开始下载人脸识别模型文件...');

    for (const file of modelFiles) {
        const url = `${baseUrl}/${file}`;
        const dest = path.join(modelsDir, file);

        try {
            await downloadFile(url, dest);
        } catch (error) {
            console.error(`下载 ${file} 失败:`, error.message);

            // 尝试原始GitHub源作为备用
            console.log(`尝试从GitHub备用源下载 ${file}...`);
            const githubUrl = `https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/${file}`;

            try {
                await downloadFile(githubUrl, dest);
            } catch (githubError) {
                console.error(`从GitHub下载 ${file} 也失败:`, githubError.message);
                throw new Error(`无法下载 ${file}`);
            }
        }
    }

    console.log('所有模型文件下载完成!');

    // 验证所有文件
    console.log('\n验证下载的文件:');
    modelFiles.forEach(file => {
        const filePath = path.join(modelsDir, file);
        if (fs.existsSync(filePath)) {
            const stats = fs.statSync(filePath);
            console.log(`✓ ${file}: ${stats.size} bytes`);
        } else {
            console.log(`✗ ${file}: 文件不存在`);
        }
    });
}

downloadModels().catch(console.error);
