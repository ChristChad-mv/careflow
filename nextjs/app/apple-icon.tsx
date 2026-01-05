import { ImageResponse } from 'next/og';
import { readFile } from 'fs/promises';
import { join } from 'path';

// Image metadata
export const size = {
  width: 180,
  height: 180,
};
export const contentType = 'image/png';

// Apple icon component using logo-2.png
export default async function AppleIcon() {
  const logoPath = join(process.cwd(), 'public', 'logo-2.png');
  const logoBuffer = await readFile(logoPath);
  const logoBase64 = logoBuffer.toString('base64');
  
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'white',
          borderRadius: '40px',
        }}
      >
        <img
          src={`data:image/jpeg;base64,${logoBase64}`}
          width="160"
          height="160"
          style={{
            objectFit: 'contain',
          }}
        />
      </div>
    ),
    {
      ...size,
    }
  );
}
