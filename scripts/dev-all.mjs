import { spawn } from 'node:child_process';

const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const workspaces = [
  '@aiquote/portal',
  '@aiquote/national-project-map',
  '@aiquote/ai-cost-estimation',
  '@aiquote/bid-template-analysis',
  '@aiquote/bid-result-analysis',
];

const children = workspaces.map((workspace) => {
  const npmArgs = ['--workspace', workspace, 'run', 'dev'];
  const command = process.platform === 'win32' ? 'cmd.exe' : npmCommand;
  const args = process.platform === 'win32'
    ? ['/d', '/s', '/c', [npmCommand, ...npmArgs].join(' ')]
    : npmArgs;
  const child = spawn(command, args, {
    cwd: process.cwd(),
    env: process.env,
    stdio: 'inherit',
    windowsHide: true,
  });

  child.on('exit', (code, signal) => {
    if (code !== 0 && signal !== 'SIGINT') {
      console.error(`[dev:all] ${workspace} exited with code ${code ?? 'unknown'}`);
    }
  });

  return child;
});

function stopChildren() {
  for (const child of children) {
    if (!child.killed) child.kill('SIGINT');
  }
}

process.on('SIGINT', () => {
  stopChildren();
  process.exit(0);
});
process.on('SIGTERM', () => {
  stopChildren();
  process.exit(0);
});
