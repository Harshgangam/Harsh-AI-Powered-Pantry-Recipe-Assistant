const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';

let pythonCmd = isWin ? 'python' : 'python3';

const venvWin = path.join(rootDir, '.venv', 'Scripts', 'python.exe');
const venvPosix = path.join(rootDir, '.venv', 'bin', 'python');

if (isWin && fs.existsSync(venvWin)) {
  pythonCmd = venvWin;
} else if (!isWin && fs.existsSync(venvPosix)) {
  pythonCmd = venvPosix;
}

const args = ['-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload'];

console.log(`[BACKEND] Starting FastAPI backend with ${pythonCmd}...`);

const proc = spawn(pythonCmd, args, {
  cwd: rootDir,
  stdio: 'inherit',
  env: { ...process.env, PYTHONPATH: rootDir }
});

proc.on('exit', (code) => {
  process.exit(code || 0);
});
