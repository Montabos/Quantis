'use client';

interface GeneratedChartProps {
  filename: string;
  mimeType: string;
  dataBase64: string;
  title?: string;
  description?: string;
}

export function GeneratedChart({ filename, mimeType, dataBase64, title, description }: GeneratedChartProps) {
  const imageSrc = `data:${mimeType};base64,${dataBase64}`;

  return (
    <div className="mb-12">
      <div className="bg-white rounded-lg border border-[#E5E5E5] p-6">
        {title && (
          <div className="mb-6">
            <h3 className="text-[11px] font-semibold text-[#737373] mb-2 uppercase tracking-wider">
              {title}
            </h3>
            {description && (
              <p className="text-sm text-[#6B7280] font-light leading-relaxed">
                {description}
              </p>
            )}
          </div>
        )}
        
        <div className="relative w-full">
          <img
            src={imageSrc}
            alt={filename}
            className="w-full h-auto rounded-lg"
            style={{ maxHeight: '600px', objectFit: 'contain' }}
          />
        </div>
      </div>
    </div>
  );
}

