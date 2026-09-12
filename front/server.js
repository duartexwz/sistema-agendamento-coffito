import { createReadStream } from 'node:fs';
import { access, stat } from 'node:fs/promises';
import { createServer, request as proxyRequest } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), 'dist');
const port = Number(process.env.PORT ?? 4173);
const apiProxyTarget = process.env.API_PROXY_TARGET ?? 'http://api:8000';

const mimeTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

function safePath(pathname) {
  const cleanPath = normalize(decodeURIComponent(pathname)).replace(/^(\.\.[/\\])+/, '');
  return join(root, cleanPath);
}

async function resolveFile(pathname) {
  const requestedPath = safePath(pathname === '/' ? '/index.html' : pathname);

  try {
    const fileStat = await stat(requestedPath);
    if (fileStat.isFile()) return requestedPath;
  } catch {
    return join(root, 'index.html');
  }

  return join(root, 'index.html');
}

function proxyApiRequest(request, response, url) {
  const target = new URL(apiProxyTarget);
  const targetPath = `${url.pathname.replace(/^\/api(?=\/|$)/, '') || '/'}${url.search}`;
  const headers = {
    ...request.headers,
    host: target.host,
  };

  const upstream = proxyRequest(
    {
      protocol: target.protocol,
      hostname: target.hostname,
      port: target.port,
      method: request.method,
      path: targetPath,
      headers,
    },
    (upstreamResponse) => {
      response.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.headers);
      upstreamResponse.pipe(response);
    },
  );

  upstream.on('error', () => {
    response.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
    response.end(JSON.stringify({ detail: 'API indisponivel no proxy do frontend' }));
  });

  request.pipe(upstream);
}

const server = createServer(async (request, response) => {
  const url = new URL(request.url ?? '/', `http://${request.headers.host}`);

  if (url.pathname === '/api' || url.pathname.startsWith('/api/')) {
    proxyApiRequest(request, response, url);
    return;
  }

  if (!['GET', 'HEAD'].includes(request.method ?? '')) {
    response.writeHead(405);
    response.end();
    return;
  }

  const filePath = await resolveFile(url.pathname);

  try {
    await access(filePath);
  } catch {
    response.writeHead(404);
    response.end('Not found');
    return;
  }

  response.writeHead(200, {
    'Content-Type': mimeTypes[extname(filePath)] ?? 'application/octet-stream',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
  });

  if (request.method === 'HEAD') {
    response.end();
    return;
  }

  createReadStream(filePath).pipe(response);
});

server.listen(port, '0.0.0.0', () => {
  console.log(`Frontend ready on port ${port}`);
});
