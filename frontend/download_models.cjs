// 下载 face-api.js 模型文件的脚本
const https = require('https');
const fs = require('fs');
const path = require('path');

const modelsDir = './public/models';

// 使用国内镜像源，提供多个备选地址
const mirrorUrls = [
  'https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights',
  'https://fastly.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights',
  'https://gcore.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights',
  'https://raw.fastgit.org/justadudewhohacks/face-api.js/master/weights'
];

const modelFiles = [
  'ssd_mobilenetv1_model-weights_manifest.json',
  'ssd_mobilenetv1_model-shard1',
  'face_landmark_68_model-weights_manifest.json',
  'face_landmark_68_model-shard1',
  'face_recognition_model-weights_manifest.json',
  'face_recognition_model-shard1',
  'face_recognition_model-shard2'
];

function downloadFile(url, dest, timeout = 30000) {
  return new Promise((resolve, reject) => {
    console.log(`Downloading ${url} to ${dest}`);
    
    const file = fs.createWriteStream(dest);
    
    const request = https.get(url, { timeout }, (response) => {
      if (response.statusCode === 302 || response.statusCode === 301) {
        // 处理重定向
        file.close();
        fs.unlink(dest, () => {});
        return downloadFile(response.headers.location, dest, timeout).then(resolve).catch(reject);
      }
      
      if (response.statusCode !== 200) {
        file.close();
        fs.unlink(dest, () => {});
        reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
        return;
      }
      
      const totalSize = parseInt(response.headers['content-length'], 10);
      let downloadedSize = 0;
      
      response.on('data', (chunk) => {
        downloadedSize += chunk.length;
        if (totalSize) {
          const percent = ((downloadedSize / totalSize) * 100).toFixed(2);
          process.stdout.write(`\r${path.basename(dest)}: ${percent}%`);
        }
      });
      
      response.pipe(file);
      
      file.on('finish', () => {
        file.close();
        console.log(`\nDownloaded ${dest}`);
        resolve();
      });
      
      file.on('error', (err) => {
        fs.unlink(dest, () => {}); // 删除部分下载的文件
        reject(err);
      });
    });
    
    request.on('timeout', () => {
      request.abort();
      file.close();
      fs.unlink(dest, () => {});
      reject(new Error('Download timeout'));
    });
    
    request.on('error', (err) => {
      file.close();
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function downloadWithFallback(file) {
  const dest = path.join(modelsDir, file);
  
  // 检查文件是否已存在
  if (fs.existsSync(dest)) {
    console.log(`${file} already exists, skipping...`);
    return;
  }
  
  for (let i = 0; i < mirrorUrls.length; i++) {
    const url = `${mirrorUrls[i]}/${file}`;
    
    try {
      await downloadFile(url, dest);
      return; // 成功下载，退出循环
    } catch (error) {
      console.error(`\nError downloading ${file} from mirror ${i + 1}:`, error.message);
      
      if (i < mirrorUrls.length - 1) {
        console.log(`Trying next mirror...`);
      } else {
        console.error(`Failed to download ${file} from all mirrors`);
      }
    }
  }
}

async function downloadModels() {
  if (!fs.existsSync(modelsDir)) {
    fs.mkdirSync(modelsDir, { recursive: true });
  }
  
  console.log('Starting model downloads...');
  console.log(`Using mirrors: ${mirrorUrls.length} available`);
  
  for (const file of modelFiles) {
    await downloadWithFallback(file);
  }
  
  console.log('\nAll models download completed!');
  console.log(`Models saved to: ${path.resolve(modelsDir)}`);
}

downloadModels().catch(console.error);