import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const docsDir = path.join(__dirname, '../../docs');

// Create CNAME file
const cnameContent = 'colorado-pauper.org';
fs.writeFileSync(path.join(docsDir, 'CNAME'), cnameContent);
console.log('✓ Created CNAME');

// Create 404.html file
const notFoundContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecting...</title>
</head>
<body>
    <script>
        const path = window.location.pathname;
        const pathWithoutRepo = path.replace(/^\/Companion-Parser/, '');
        const hashPath = pathWithoutRepo === '/' ? '/#/' : '/#' + pathWithoutRepo;
        window.location.replace(hashPath);
    </script>
</body>
</html>`;
fs.writeFileSync(path.join(docsDir, '404.html'), notFoundContent);
console.log('✓ Created 404.html');
